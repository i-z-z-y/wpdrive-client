$ErrorActionPreference = 'Stop'

# Build a one-file EXE using PyInstaller
# Output: installer\dist\WPDrive-Install.exe

$root = Split-Path -Parent $PSScriptRoot
$py = @('py','-3.14')

Write-Host "Installing PyInstaller..." -ForegroundColor Cyan
& $py[0] $py[1] -m pip install --upgrade pyinstaller

Write-Host "Building EXE..." -ForegroundColor Cyan
Push-Location $root
& $py[0] $py[1] -m PyInstaller --onefile --name WPDrive-Install --distpath installer\\dist --workpath installer\\build --specpath installer installer\\win_install.py
Pop-Location

Write-Host "EXE ready at installer\\dist\\WPDrive-Install.exe" -ForegroundColor Green
