$ErrorActionPreference = 'Stop'

# ---- Config (edit once, then share) ----
$REPO_OWNER = 'i-z-z-y'
$REPO_NAME = 'wpdrive-client'
$REPO_ZIP_MAIN = "https://github.com/$REPO_OWNER/$REPO_NAME/archive/refs/heads/main.zip"
$REPO_API_LATEST = "https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/releases/latest"
$INSTALL_SCOPE = 'auto' # auto | user | system
# Optional overrides via env vars:
#   WPDRIVE_REPO_URL   (direct URL to zip or git repo)
#   WPDRIVE_PY_EXE     (full path to python.exe)
#   WPDRIVE_PY_CMD     (e.g., "py -3.14")
#   WPDRIVE_SCOPE      (auto|user|system)

function Write-Info($msg) { Write-Host "[wpdrive-installer] $msg" -ForegroundColor Cyan }
function Write-Ok($msg) { Write-Host "[wpdrive-installer] $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "[wpdrive-installer] $msg" -ForegroundColor Yellow }

function Get-LatestReleaseZip {
  try {
    $headers = @{ Accept = 'application/vnd.github+json'; 'User-Agent' = 'wpdrive-installer' }
    $resp = Invoke-RestMethod -Uri $REPO_API_LATEST -Headers $headers
    if ($resp.zipball_url) { return $resp.zipball_url }
  } catch {
    Write-Warn "Could not resolve latest release; falling back to main branch zip."
  }
  return $REPO_ZIP_MAIN
}

$RepoUrl = if ($env:WPDRIVE_REPO_URL) { $env:WPDRIVE_REPO_URL } else { Get-LatestReleaseZip }

$Scope = if ($env:WPDRIVE_SCOPE) { $env:WPDRIVE_SCOPE } else { $INSTALL_SCOPE }
if ($Scope -notin @('auto','user','system')) {
  Write-Warn "Unknown WPDRIVE_SCOPE value '$Scope'. Using auto."
  $Scope = 'auto'
}

# Resolve python command
$PyCmd = $null
if ($env:WPDRIVE_PY_EXE) {
  $PyCmd = @($env:WPDRIVE_PY_EXE)
} elseif ($env:WPDRIVE_PY_CMD) {
  $PyCmd = $env:WPDRIVE_PY_CMD.Split(' ', [System.StringSplitOptions]::RemoveEmptyEntries)
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
  $PyCmd = @('py','-3.14')
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
  $PyCmd = @('python')
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
  $PyCmd = @('python3')
} else {
  throw "Python not found. Install Python 3.9+ and retry."
}

function Invoke-Checked([string[]]$Cmd, [string[]]$Args = @()) {
  $prev = $ErrorActionPreference
  $ErrorActionPreference = 'Continue'
  $all = @()
  if ($Cmd.Length -gt 1) { $all += $Cmd[1..($Cmd.Length-1)] }
  if ($Args) { $all += $Args }
  $output = & $Cmd[0] @all 2>&1
  $ErrorActionPreference = $prev
  $output | ForEach-Object { Write-Host $_ }
  if ($LASTEXITCODE -ne 0) { throw "Command failed: $($Cmd -join ' ')" }
  return $output
}

function Invoke-Capture([string[]]$Cmd, [string[]]$Args = @()) {
  $prev = $ErrorActionPreference
  $ErrorActionPreference = 'Continue'
  $all = @()
  if ($Cmd.Length -gt 1) { $all += $Cmd[1..($Cmd.Length-1)] }
  if ($Args) { $all += $Args }
  $output = & $Cmd[0] @all 2>&1
  $ErrorActionPreference = $prev
  if ($LASTEXITCODE -ne 0) {
    $output | ForEach-Object { Write-Host $_ }
    throw "Command failed: $($Cmd -join ' ')"
  }
  return ($output -join "`n").Trim()
}

function Add-PathEntry([string]$Entry, [ValidateSet('User','Machine')]$Target) {
  $current = [Environment]::GetEnvironmentVariable('Path', $Target)
  if (-not $current) { $current = '' }
  $paths = $current.Split(';') | Where-Object { $_ -ne '' }
  if ($paths -contains $Entry) { return $false }
  $new = if ($current -and $current.Trim()) { "$current;$Entry" } else { $Entry }
  [Environment]::SetEnvironmentVariable('Path', $new, $Target)
  return $true
}

$IsAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

Write-Info "Installing wpdrive from $RepoUrl"
$pipArgs = @('-m','pip','install','--upgrade',$RepoUrl)
if ($Scope -eq 'user') {
  $pipArgs = @('-m','pip','install','--upgrade','--user',$RepoUrl)
} elseif ($Scope -eq 'system' -and -not $IsAdmin) {
  Write-Warn "System scope requested but not running as admin. Proceeding with default install."
}
Invoke-Checked $PyCmd $pipArgs

$sysScripts = Invoke-Capture $PyCmd @('-c','import sysconfig; print(sysconfig.get_path("scripts"))')
$userBase = Invoke-Capture $PyCmd @('-c','import site; print(site.USER_BASE)')
$userScripts = Join-Path $userBase 'Scripts'

$scriptDir = $null
$installScope = 'unknown'
if (Test-Path -LiteralPath (Join-Path $sysScripts 'wpdrive.exe')) {
  $scriptDir = $sysScripts
  $installScope = 'system'
} elseif (Test-Path -LiteralPath (Join-Path $userScripts 'wpdrive.exe')) {
  $scriptDir = $userScripts
  $installScope = 'user'
}

if (-not $scriptDir) {
  Write-Warn "wpdrive.exe not found in expected Scripts locations."
} else {
  if ($installScope -eq 'system' -and $IsAdmin) {
    if (Add-PathEntry $scriptDir 'Machine') { Write-Ok "Added to machine PATH." } else { Write-Info "Machine PATH already contains Scripts path." }
  } else {
    if (Add-PathEntry $scriptDir 'User') { Write-Ok "Added to user PATH." } else { Write-Info "User PATH already contains Scripts path." }
  }
}

# Refresh current session PATH
$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')

if (Get-Command wpdrive -ErrorAction SilentlyContinue) {
  Write-Ok "wpdrive is now available on PATH."
} else {
  Write-Warn "wpdrive not found on PATH in this session. Open a new terminal."
}

Write-Host "" 
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1) wpdrive init --root C:\\path\\to\\sync --url http://localhost --user your-user --app-password 'your app password'" 
Write-Host "  2) wpdrive sync --root C:\\path\\to\\sync" 
Write-Host "  3) Daemon: wpdrive daemon --interval 10 --root C:\\path\\to\\sync" 
