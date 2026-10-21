<#
.SYNOPSIS
  Before a fresh MAPDL solve: list (default) or stop leftover MAPDL solver processes,
  report stale PYMAPDL_* env vars and lock files, and create a fresh run_location.

  SAFETY: only MAPDL solver executables are ever targeted (ANSYS2xx.exe, ansysdis*, mapdl*).
  Never touched: license client (ansyscl, ansysli*, lmgrd), Motor-CAD, AEDT (ansysedt),
  Fluent, FreeFlow/Rocky, Workbench. A user may have those open.

.EXAMPLE
  .\ansys_clean.ps1                       # dry run: show what would be stopped
  .\ansys_clean.ps1 -Kill -NewRunLocation C:\work\mapdl_runs
#>
param(
  [switch]$Kill,
  [string]$NewRunLocation = ""
)
$target    = '^(ANSYS\d{3}|ansysdis\d*|mapdl)$'
$protected = '^(ansyscl|ansysli.*|lmgrd|MotorCAD.*|ansysedt|fluent.*|cx\d*|FreeFlow.*|Rocky.*|AnsysWBU|RunWB2)$'

$procs = Get-Process | Where-Object { $_.Name -match $target -and $_.Name -notmatch $protected }
$kept  = Get-Process | Where-Object { $_.Name -match $protected } | Select-Object -ExpandProperty Name -Unique

$out = [ordered]@{
  mapdl_processes = @($procs | ForEach-Object { "{0}:{1}" -f $_.Name, $_.Id })
  protected_running = @($kept)
  env_PYMAPDL_START_INSTANCE = $env:PYMAPDL_START_INSTANCE
  env_PYMAPDL_PORT = $env:PYMAPDL_PORT
  action = "dry_run"
  new_run_location = $null
}
if ($Kill -and $procs) {
  # PIDs are a snapshot: re-check name before stopping.
  foreach ($p in $procs) {
    $cur = Get-Process -Id $p.Id -ErrorAction SilentlyContinue
    if ($cur -and $cur.Name -eq $p.Name) { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue }
  }
  Start-Sleep -Seconds 3
  $out.action = "stopped"
  $out.still_running = @(Get-Process | Where-Object { $_.Name -match $target } | ForEach-Object { "{0}:{1}" -f $_.Name, $_.Id })
} elseif ($Kill) {
  $out.action = "nothing_to_stop"
}
if ($NewRunLocation) {
  $loc = Join-Path $NewRunLocation ("run_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
  New-Item -ItemType Directory -Force $loc | Out-Null
  $out.new_run_location = $loc
}
$out | ConvertTo-Json -Depth 3 -Compress
