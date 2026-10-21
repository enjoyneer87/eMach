<#
.SYNOPSIS
  Launch a long Python job (MAPDL solve, viz, FreeFlow script) detached and return immediately.
  The job writes <RunDir>\done.json when it ends: exit code, elapsed, stdout/stderr tails, new files.
  Pair with wait_done.ps1 (run once in background) instead of polling logs.

.EXAMPLE
  .\run_detached.ps1 -Script D:\KDH\NvidiaNemo\eMach\mlxperPJT\thermal\freeflow\scripts\04_mapdl_thermal.py -Name e10_hybrid
  .\run_detached.ps1 -Script ...\d1_cont_rating.py -ScriptArgs '--repo','D:\KDH\NvidiaNemo\eMach','--mode','super' -Name d1 -ScheduledTask
#>
param(
  [Parameter(Mandatory=$true)][string]$Script,
  [string[]]$ScriptArgs = @(),
  [string]$Name = "job",
  [string]$RunRoot = "C:\work\runs",
  [string]$Python = "C:\Users\moa\.ansys_python_venvs\PyMotorEnv_310\Scripts\python.exe",
  [string]$WorkDir = "",
  # Use a one-off scheduled task so the job survives an SSH session closing.
  [switch]$ScheduledTask
)
$ErrorActionPreference = "Stop"
if (-not (Test-Path $Script)) { throw "Script not found: $Script" }
if (-not (Test-Path $Python)) { throw "Python not found: $Python" }
if (-not $WorkDir) { $WorkDir = Split-Path -Parent $Script }

$stamp  = Get-Date -Format "yyyyMMdd_HHmmss"
$runDir = Join-Path $RunRoot ("{0}_{1}" -f $Name, $stamp)
New-Item -ItemType Directory -Force $runDir | Out-Null

# Quote args for the runner command line
$argText = ($ScriptArgs | ForEach-Object { "'" + ($_ -replace "'", "''") + "'" }) -join ","
$taskName = "mth_{0}_{1}" -f $Name, $stamp

$runner = @"
`$ErrorActionPreference = 'Continue'
`$env:PYTHONUTF8 = '1'
`$env:RUN_DIR = '$runDir'
Remove-Item Env:PYMAPDL_START_INSTANCE -ErrorAction SilentlyContinue
Remove-Item Env:PYMAPDL_PORT -ErrorAction SilentlyContinue
Set-Location '$WorkDir'
`$t0 = Get-Date
`$before = @{}; Get-ChildItem -Path '$WorkDir' -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object { `$before[`$_.FullName] = `$_.LastWriteTime }
`$a = @($argText)
& '$Python' -X utf8 '$Script' @a 1> '$runDir\stdout.log' 2> '$runDir\stderr.log'
`$code = `$LASTEXITCODE
`$new = Get-ChildItem -Path '$WorkDir' -Recurse -File -ErrorAction SilentlyContinue | Where-Object { -not `$before.ContainsKey(`$_.FullName) -or `$before[`$_.FullName] -ne `$_.LastWriteTime } | Select-Object -First 40 -ExpandProperty FullName
`$done = [ordered]@{
  name = '$Name'; script = '$Script'; exit_code = `$code
  start = `$t0.ToString('s'); end = (Get-Date).ToString('s')
  elapsed_s = [math]::Round(((Get-Date) - `$t0).TotalSeconds, 1)
  stdout_tail = @(Get-Content '$runDir\stdout.log' -Tail 15 -ErrorAction SilentlyContinue | ForEach-Object { [string]`$_ })
  stderr_tail = @(Get-Content '$runDir\stderr.log' -Tail 15 -ErrorAction SilentlyContinue | ForEach-Object { [string]`$_ })
  new_or_changed_files = @(`$new | ForEach-Object { [string]`$_ })
}
`$done | ConvertTo-Json -Depth 3 | Set-Content -Encoding UTF8 '$runDir\done.json'
"@
$runnerPath = Join-Path $runDir "runner.ps1"
Set-Content -Path $runnerPath -Value $runner -Encoding UTF8

$meta = [ordered]@{ name=$Name; run_dir=$runDir; script=$Script; args=$ScriptArgs; started=(Get-Date).ToString('s'); mode= $(if ($ScheduledTask) {"scheduled_task"} else {"start_process"}); task_name = $(if ($ScheduledTask) {$taskName} else {$null}) }
$meta | ConvertTo-Json -Depth 3 | Set-Content -Encoding UTF8 (Join-Path $runDir "run.json")

if ($ScheduledTask) {
  $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument ("-NoProfile -ExecutionPolicy Bypass -File `"{0}`"" -f $runnerPath)
  Register-ScheduledTask -TaskName $taskName -Action $action -Force | Out-Null
  Start-ScheduledTask -TaskName $taskName
} else {
  Start-Process -FilePath "powershell.exe" -ArgumentList @("-NoProfile","-ExecutionPolicy","Bypass","-File","`"$runnerPath`"") -WindowStyle Hidden | Out-Null
}
# Single line for the caller: where to wait.
Write-Output ("RUN_DIR={0}" -f $runDir)
