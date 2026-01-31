$ErrorActionPreference = 'Stop'

$owner = 'i-z-z-y'
$repo = 'wpdrive-client'
$api = "https://api.github.com/repos/$owner/$repo/releases/latest"
$mainZip = "https://github.com/$owner/$repo/archive/refs/heads/main.zip"

try {
  $resp = Invoke-RestMethod -Uri $api -Headers @{ Accept = 'application/vnd.github+json' }
  $zip = $resp.zipball_url
  if (-not $zip) { throw "No zipball_url" }
} catch {
  Write-Host "Could not resolve latest release; falling back to main branch." -ForegroundColor Yellow
  $zip = $mainZip
}

$env:WPDRIVE_REPO_URL = $zip
Write-Host "Using: $zip" -ForegroundColor Cyan
& $PSScriptRoot\install.ps1
