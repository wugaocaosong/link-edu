import os
import smtplib
import ssl
from email.message import EmailMessage


class MailUnavailable(Exception):
    pass


def send_board_mail(topic, author, body):
    host = os.getenv('SMTP_HOST')
    sender = os.getenv('SMTP_FROM')
    recipient = os.getenv('FEEDBACK_MAIL_TO')
    if not all((host, sender, recipient)):
        raise MailUnavailable('留言邮箱尚未配置，请稍后再发送。')
    message = EmailMessage()
    message['From'] = sender
    message['To'] = recipient
    message['Subject'] = f'临客 LINK 留言 · {topic}'
    message.set_content(f'{body}\n\n落款：{author}')
    context = ssl.create_default_context()
    try:
        port = int(os.getenv('SMTP_PORT', '465'))
        if port == 465:
            client = smtplib.SMTP_SSL(host, port, timeout=8, context=context)
        else:
            client = smtplib.SMTP(host, port, timeout=8)
        with client:
            if port != 465:
                client.starttls(context=context)
            if os.getenv('SMTP_USER'):
                client.login(os.environ['SMTP_USER'], os.getenv('SMTP_PASSWORD', ''))
            client.send_message(message)
    except (OSError, ValueError, smtplib.SMTPException) as exc:
        raise MailUnavailable('邮件服务暂时无法确认发送，留言草稿已保留。') from exc
