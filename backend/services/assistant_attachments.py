"""Bounded, in-memory attachment transfer and document extraction."""
import base64
import binascii
from io import BytesIO
from pathlib import PurePosixPath
from zipfile import ZipFile

IMAGE_TYPES = {'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'webp': 'image/webp'}
FILE_TYPES = {'pdf', 'docx', 'txt', 'md'}
CHUNK_BYTES = 24 * 1024
EXCERPT_LIMIT = 16000


class AttachmentError(ValueError):
    pass


class AttachmentUpload:
    def __init__(self, kind, message):
        self.kind = kind
        self.request_id = message.get('request_id')
        name = message.get('name')
        size = message.get('size')
        if not isinstance(self.request_id, str) or not 1 <= len(self.request_id) <= 64:
            raise AttachmentError('附件请求编号无效。')
        if not isinstance(name, str) or not 1 <= len(name) <= 180 or any(ord(c)<32 for c in name):
            raise AttachmentError('附件文件名无效。')
        self.name = PurePosixPath(name.replace(chr(92), '/')).name
        self.ext = self.name.rsplit('.', 1)[-1].lower()
        allowed = IMAGE_TYPES if kind == 'image' else FILE_TYPES
        if '.' not in self.name or self.ext not in allowed:
            raise AttachmentError('不支持此附件类型。请选择 PNG、JPEG、WebP、PDF、DOCX、TXT 或 Markdown。')
        limit = 10 if kind == 'image' else 20
        if type(size) is not int or size <= 0 or size > limit * 1024 * 1024:
            raise AttachmentError(f'附件不能为空，大小不能超过 {limit} MB。')
        self.size = size
        self.data = bytearray()

    def append(self, message):
        encoded = message.get('data')
        if type(message.get('offset')) is not int or message['offset'] != len(self.data):
            raise AttachmentError('附件分片顺序无效，请重新发送。')
        if not isinstance(encoded, str) or not 0 < len(encoded) <= CHUNK_BYTES * 4 // 3:
            raise AttachmentError('附件数据无效。')
        try:
            chunk = base64.b64decode(encoded, validate=True)
        except (ValueError, binascii.Error):
            raise AttachmentError('附件编码无效。') from None
        if not chunk or len(self.data) + len(chunk) > self.size:
            raise AttachmentError('附件大小与声明不符。')
        self.data.extend(chunk)

    def finish(self):
        if len(self.data) != self.size:
            raise AttachmentError('附件未传完整，请重新发送。')
        return self


def image_mime(attachment):
    data = attachment.data
    signatures = {
        'png': data.startswith(b'\x89PNG\r\n\x1a\n'),
        'jpg': data.startswith(b'\xff\xd8\xff'),
        'jpeg': data.startswith(b'\xff\xd8\xff'),
        'webp': data.startswith(b'RIFF') and data[8:12] == b'WEBP',
    }
    if not signatures.get(attachment.ext):
        raise AttachmentError('图片格式与扩展名不符，或图片已损坏。')
    return IMAGE_TYPES[attachment.ext]


def extract_document(attachment, control):
    ext = attachment.ext
    data = attachment.data
    try:
        if ext == 'pdf':
            from pypdf import PdfReader
            if not data.startswith(b'%PDF-'):
                raise AttachmentError('文件内容不是有效的 PDF。')
            reader = PdfReader(BytesIO(data))
            if reader.is_encrypted:
                raise AttachmentError('无法读取加密 PDF，请先提供已解密的文件。')
            chunks, length = [], 0
            for page in reader.pages[:40]:
                control.check()
                text = (page.extract_text() or '').strip()
                if text:
                    chunks.append(text[:EXCERPT_LIMIT-length])
                    length += len(chunks[-1])
                if length >= EXCERPT_LIMIT:
                    break
            text = '\n\n'.join(chunks)
            truncated = len(reader.pages) > 40 or length >= EXCERPT_LIMIT
        elif ext == 'docx':
            from docx import Document
            with ZipFile(BytesIO(data)) as archive:
                entries = archive.infolist()
                if (len(entries) > 1500 or sum(entry.file_size for entry in entries) > 80*1024*1024
                        or 'word/document.xml' not in archive.namelist()
                        or archive.getinfo('word/document.xml').file_size > 8*1024*1024):
                    raise AttachmentError('DOCX 结构无效或解压后过大。')
            doc = Document(BytesIO(data))
            chunks, length = [], 0
            for block in doc.iter_inner_content():
                control.check()
                if hasattr(block, 'text'):
                    part = block.text
                else:
                    part = '\n'.join('\t'.join(cell.text for cell in row.cells) for row in block.rows)
                chunks.append(part[:EXCERPT_LIMIT-length])
                length += len(chunks[-1])
                if length >= EXCERPT_LIMIT:
                    break
            text, truncated = '\n'.join(chunks), length >= EXCERPT_LIMIT
        else:
            text = data.decode('utf-8-sig')
            if '\x00' in text or any(ord(c)<32 and c not in '\t\n\r\f' for c in text[:EXCERPT_LIMIT]):
                raise AttachmentError('文件不是有效文本，请另存为 UTF-8 后重试。')
            truncated = len(text) > EXCERPT_LIMIT
    except UnicodeError:
        raise AttachmentError('文本编码无法识别，请另存为 UTF-8。') from None
    except AttachmentError:
        raise
    except Exception as exc:
        control.check()
        raise AttachmentError('无法解析附件，文件可能损坏或服务器缺少解析组件。') from exc
    if not text.strip():
        raise AttachmentError('未能从附件提取文字。扫描版 PDF 可以截取清晰页面后按图片发送。')
    return text.strip()[:EXCERPT_LIMIT], truncated
