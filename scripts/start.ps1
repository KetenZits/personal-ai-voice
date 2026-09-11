$ErrorActionPreference = "Stop"
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    throw "Virtual environment missing. Run .\scripts\setup.ps1 first."
}
& .\.venv\Scripts\python.exe main.py @args

