$ErrorActionPreference = "Stop"
if (-not (Test-Path ".venv")) {
    py -3.11 -m venv .venv
}
$version = & .\.venv\Scripts\python.exe -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ($version -notin @("3.11", "3.12")) {
    throw "Nova requires Python 3.11 or 3.12, but .venv uses Python $version. Remove .venv and recreate it with py -3.11 -m venv .venv."
}
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
Write-Host "Setup complete. Edit config/*.yaml, then run scripts/start.ps1."
