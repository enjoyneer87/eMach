<#
.SYNOPSIS
  Block silently until <RunDir>\done.json exists, then print it once.
  Run this ONCE as a background command (run_in_background) so the agent is notified on completion.
  Do not call it repeatedly with a short timeout - that is the polling this replaces.

  Exit code: the job's exit code, 124 on timeout.

.EXAMPLE
  .\wait_done.ps1 -RunDir C:\work\runs\e10_hybrid_20261021_130000 -TimeoutMin 240
#>
param(
  [Parameter(Mandatory=$true)][string]$RunDir,
  [int]$TimeoutMin = 240,
  [int]$PollSec = 30,
  # Optional: also print this summary JSON written by the job itself (e.g. thesis_out\x.json)
  [string]$SummaryJson = ""
)
$done = Join-Path $RunDir "done.json"
$deadline = (Get-Date).AddMinutes($TimeoutMin)
while (-not (Test-Path $done)) {
  if ((Get-Date) -gt $deadline) {
    $tail = @(Get-Content (Join-Path $RunDir "stdout.log") -Tail 5 -ErrorAction SilentlyContinue)
    Write-Output ("TIMEOUT after {0} min. Job may still be running. stdout tail:" -f $TimeoutMin)
    $tail | ForEach-Object { Write-Output ("  " + [string]$_) }
    exit 124
  }
  Start-Sleep -Seconds $PollSec
}
Start-Sleep -Seconds 2
# A running task cannot unregister itself; remove the one-off task now that it has finished.
$meta = Join-Path $RunDir "run.json"
if (Test-Path $meta) {
  $m = Get-Content $meta -Raw -Encoding UTF8 | ConvertFrom-Json
  if ($m.task_name) { Unregister-ScheduledTask -TaskName $m.task_name -Confirm:$false -ErrorAction SilentlyContinue }
}
$j = Get-Content $done -Raw -Encoding UTF8 | ConvertFrom-Json
Write-Output ($j | ConvertTo-Json -Depth 4 -Compress)
if ($SummaryJson -and (Test-Path $SummaryJson)) {
  Write-Output "--- summary:"
  Write-Output (Get-Content $SummaryJson -Raw -Encoding UTF8)
}
exit [int]$j.exit_code
