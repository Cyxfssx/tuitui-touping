$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (!(Test-Path -LiteralPath $python)) { throw 'Missing .venv. See README-webview.md.' }
if (!(Test-Path -LiteralPath 'tuitui-engine\scrcpy.exe')) { throw 'Missing tuitui-engine.' }
& $python -m PyInstaller --noconfirm --clean --windowed --name TuiTuiScreenV2 --icon assets\tuitui.ico --collect-all webview --add-data 'tuitui_web\assets;tuitui_web\assets' tuitui_web_main.py
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller build failed.' }
$dest = Join-Path $PSScriptRoot 'dist\TuiTuiScreenV2'
Copy-Item -Recurse -Force -LiteralPath (Join-Path $PSScriptRoot 'tuitui-engine') -Destination (Join-Path $dest 'tuitui-engine')
New-Item -ItemType Directory -Path (Join-Path $dest 'assets') -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'assets\tuitui2-scanner.jar'),(Join-Path $PSScriptRoot 'assets\tuitui2.apk') -Destination (Join-Path $dest 'assets') -Force
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'README-webview.md') -Destination (Join-Path $dest '使用说明.md') -Force
Write-Host "Done: $dest"


