<#
.SYNOPSIS
  One-shot sync of results: (1) rclone viz/data to gdrive, (2) git push with a single
  verification, or a git bundle when GitHub is unreachable (moa cannot resolve github.com).
  Prints one JSON summary. Replaces repeated push / ls-remote / rclone checks.

.EXAMPLE
  .\sync_out.ps1 -Repo D:\KDH\NvidiaNemo\eMach -VizDir ...\freeflow\viz -GdriveDest gdrive:Prius_thermal_viz/e10/viz
  .\sync_out.ps1 -Repo D:\KDH\NvidiaNemo\eMach -BundleOut C:\work\outbox      # git only
#>
param(
  [string]$Repo = "D:\KDH\NvidiaNemo\eMach",
  [string]$Branch = "",
  [string]$VizDir = "",
  [string]$GdriveDest = "",
  [string]$Rclone = "D:\KDH\NvidiaNemo\tools\bin\rclone.exe",
  [string]$BundleOut = "C:\work\outbox",
  [switch]$SkipGit
)
$ErrorActionPreference = "Continue"
$res = [ordered]@{}

function Run-Native([string]$exe, [string[]]$argv) {
  $o = & cmd /c ("`"" + $exe + "`" " + ($argv -join " ") + " 2>&1")
  return @{ code = $LASTEXITCODE; text = (($o | Out-String).Trim()) }
}

if ($VizDir -and $GdriveDest) {
  if (-not (Test-Path $Rclone)) { $res.rclone = "rclone not found: $Rclone" }
  else {
    $r = Run-Native $Rclone @("copy", "`"$VizDir`"", $GdriveDest, "--stats-one-line", "--stats", "0")
    $chk = Run-Native $Rclone @("check", "`"$VizDir`"", $GdriveDest, "--one-way", "--size-only")
    $res.rclone = [ordered]@{ copy_exit = $r.code; check_exit = $chk.code; check_tail = ([string]($chk.text -split "`n" | Select-Object -Last 1)) }
  }
}

if (-not $SkipGit) {
  Push-Location $Repo
  if (-not $Branch) { $Branch = (git rev-parse --abbrev-ref HEAD).Trim() }
  $head = (git rev-parse HEAD).Trim()
  $res.git = [ordered]@{ branch = $Branch; head = $head.Substring(0,7) }
  $probe = Run-Native "git" @("ls-remote", "origin", "refs/heads/$Branch")
  if ($probe.code -eq 0) {
    $ok = $false
    for ($i = 1; $i -le 3 -and -not $ok; $i++) {
      $p = Run-Native "git" @("push", "origin", $Branch)
      $v = Run-Native "git" @("ls-remote", "origin", "refs/heads/$Branch")
      if ($v.text -match $head) { $ok = $true }
      else { Start-Sleep -Seconds (10 * $i) }
    }
    $res.git.mode = "push"; $res.git.verified = $ok
  } else {
    New-Item -ItemType Directory -Force $BundleOut | Out-Null
    $base = "origin/$Branch"
    $hasBase = (Run-Native "git" @("rev-parse", "--verify", "--quiet", $base)).code -eq 0
    $range = $(if ($hasBase) { "$base..$Branch" } else { $Branch })
    $file = Join-Path $BundleOut ("eMach_{0}_{1}.bundle" -f ($Branch -replace '[\\/]','_'), $head.Substring(0,7))
    $b = Run-Native "git" @("bundle", "create", "`"$file`"", $range)
    $res.git.mode = "bundle"; $res.git.reason = "origin unreachable"
    $res.git.bundle = $file; $res.git.range = $range; $res.git.exit = $b.code
    if ($b.code -ne 0) { $res.git.error = ($b.text -split "`n" | Select-Object -Last 3) }
  }
  Pop-Location
}
$res | ConvertTo-Json -Depth 4 -Compress
