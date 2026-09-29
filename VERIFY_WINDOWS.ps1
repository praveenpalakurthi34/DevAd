$ErrorActionPreference = 'Stop'

Write-Host "[1/4] Backend dependencies" -ForegroundColor Cyan
Set-Location backend
if (-not (Test-Path .venv)) { python -m venv .venv }
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

Write-Host "[2/4] Backend tests" -ForegroundColor Cyan
.\.venv\Scripts\python.exe -m compileall -q app
.\.venv\Scripts\python.exe -m pytest -q tests

Write-Host "[3/4] Frontend dependencies/build" -ForegroundColor Cyan
Set-Location ..\frontend
npm ci
npm run build

Write-Host "[4/4] Ready" -ForegroundColor Green
Write-Host "Set .env in the project root with Hindsight + Groq credentials, then run the backend and frontend as described in README.md."
