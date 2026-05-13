$ErrorActionPreference = "Stop"

$Python = if ($env:PDF_STAMP_PYTHON) { $env:PDF_STAMP_PYTHON } else { "python" }

& $Python -m pip install --upgrade pip
& $Python -m pip install -r requirements.txt
& $Python -m pip install pyinstaller

& $Python -m PyInstaller `
  --noconfirm `
  --clean `
  --windowed `
  --name "文件盖章易" `
  main.py

$portable = "dist\文件盖章易"
New-Item -ItemType Directory -Force -Path "$portable\user_data\stamps" | Out-Null
if (-not (Test-Path "$portable\user_data\settings.json")) {
  "{}" | Out-File -Encoding utf8 "$portable\user_data\settings.json"
}

Write-Host "Portable build completed: $portable"
