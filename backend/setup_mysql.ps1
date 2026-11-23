param(
    [string]$HostName = '127.0.0.1',
    [int]$Port = 3306,
    [string]$User = 'root',
    [string]$Password = 'root',
    [string]$Database = 'link',
    [string]$PythonPath
)

$ErrorActionPreference = 'Stop'
if (-not $PythonPath) {
    $venv = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
    $PythonPath = if (Test-Path -LiteralPath $venv) { $venv } else { (Get-Command python.exe).Source }
}
$originalUrl = $env:DATABASE_URL
try {
    # With no connection overrides, use exactly the same configuration as Flask.
    if (@('HostName', 'Port', 'User', 'Password', 'Database') | Where-Object { $PSBoundParameters.ContainsKey($_) }) {
        $serverHost = if ($HostName.Contains(':') -and -not $HostName.StartsWith('[')) { "[$HostName]" } else { $HostName }
        $env:DATABASE_URL = 'mysql+pymysql://{0}:{1}@{2}:{3}/{4}?charset=utf8mb4' -f (
            [Uri]::EscapeDataString($User), [Uri]::EscapeDataString($Password), $serverHost, $Port, $Database
        )
    }
    & $PythonPath (Join-Path $PSScriptRoot 'init_db.py') --require-mysql
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
    $env:DATABASE_URL = $originalUrl
}
