param(
    [switch]$Background
)

Set-Location $PSScriptRoot

$python = Join-Path $PSScriptRoot "venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    $python = "python"
}

$arguments = @("src/main.py")

if ($Background) {
    $stdout = Join-Path $PSScriptRoot "flask-server.out.log"
    $stderr = Join-Path $PSScriptRoot "flask-server.err.log"
    $process = Start-Process -FilePath $python -ArgumentList $arguments -WorkingDirectory $PSScriptRoot -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
    Write-Output ("Started Voice Library on http://127.0.0.1:5000 with PID {0}" -f $process.Id)
} else {
    & $python @arguments
}
