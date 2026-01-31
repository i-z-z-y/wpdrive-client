param(
  [Parameter(Mandatory = $true)][string]$Version
)

if ($Version -notmatch '^\d+\.\d+\.\d+$') {
  throw "Version must be in X.Y.Z format"
}

$root = Split-Path -Parent $PSScriptRoot
$pyproject = Join-Path $root 'pyproject.toml'
if (-not (Test-Path -LiteralPath $pyproject)) { throw "pyproject.toml not found" }

$content = Get-Content -Path $pyproject -Raw
$replacement = 'version = "' + $Version + '"'
$updated = $content -replace '(?m)^version\s*=\s*"[^"]+"', $replacement
if ($updated -eq $content) { throw "version line not found in pyproject.toml" }

$updated | Set-Content -Path $pyproject -Encoding ASCII
Write-Host "Updated version in pyproject.toml to $Version" -ForegroundColor Green
