$ErrorActionPreference = "Stop"

Write-Host "Creating Python virtual environment in .venv ..."
py -m venv .venv

Write-Host "Installing Python dependencies ..."
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt

Write-Host ""
Write-Host "Setup complete. To activate this environment in PowerShell, run:"
Write-Host "  .\.venv\Scripts\Activate.ps1"
Write-Host ""
Write-Host "Then start the API with:"
Write-Host "  uvicorn app.main:app --reload"
