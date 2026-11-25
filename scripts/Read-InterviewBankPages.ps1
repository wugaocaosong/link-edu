param(
    [Parameter(Mandatory)][string]$Path,
    [Parameter(Mandatory)][string]$Page
)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new()
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Storage.StorageFile,Windows.Storage,ContentType=WindowsRuntime]
$null = [Windows.Data.Pdf.PdfDocument,Windows.Data.Pdf,ContentType=WindowsRuntime]
$null = [Windows.Data.Pdf.PdfPageRenderOptions,Windows.Data.Pdf,ContentType=WindowsRuntime]
$null = [Windows.Storage.Streams.InMemoryRandomAccessStream,Windows.Storage.Streams,ContentType=WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder,Windows.Graphics.Imaging,ContentType=WindowsRuntime]
$null = [Windows.Media.Ocr.OcrEngine,Windows.Foundation,ContentType=WindowsRuntime]
$null = [Windows.Media.Ocr.OcrResult,Windows.Foundation,ContentType=WindowsRuntime]
$null = [Windows.Graphics.Imaging.SoftwareBitmap,Windows.Foundation,ContentType=WindowsRuntime]
$null = [Windows.Globalization.Language,Windows.Foundation,ContentType=WindowsRuntime]
$asAction = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and !$_.IsGenericMethod -and $_.GetParameters().Count -eq 1
} | Select-Object -First 1
$asTask = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.IsGenericMethod -and $_.GetParameters().Count -eq 1
} | Select-Object -First 1
function Await-Result($Operation, [type]$Type) {
    $task = $asTask.MakeGenericMethod($Type).Invoke($null, @($Operation))
    $task.GetAwaiter().GetResult()
}
$file = Await-Result ([Windows.Storage.StorageFile]::GetFileFromPathAsync((Resolve-Path -LiteralPath $Path).Path)) ([Windows.Storage.StorageFile])
$pdf = Await-Result ([Windows.Data.Pdf.PdfDocument]::LoadFromFileAsync($file)) ([Windows.Data.Pdf.PdfDocument])
$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage([Windows.Globalization.Language]::new('zh-Hans-CN'))
if (!$engine) { throw 'Install the Windows zh-Hans-CN OCR language pack.' }
foreach ($number in ($Page -split ',')) {
    $pdfPage = $pdf.GetPage($number - 1)
    $stream = [Windows.Storage.Streams.InMemoryRandomAccessStream]::new()
    try {
        $options = [Windows.Data.Pdf.PdfPageRenderOptions]::new()
        $options.DestinationWidth = 1800
        $null = $asAction.Invoke($null, @($pdfPage.RenderToStreamAsync($stream, $options))).GetAwaiter().GetResult()
        $stream.Seek(0)
        $decoder = Await-Result ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
        $bitmap = Await-Result ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
        try {
            $result = Await-Result ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
            "=== $number ==="
            $result.Lines | ForEach-Object { $_.Text }
        } finally { $bitmap.Dispose() }
    } finally {
        $stream.Dispose()
        $pdfPage.Dispose()
    }
}
