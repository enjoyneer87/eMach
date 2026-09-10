param(
    [string]$Repo = 'D:\KDH\NvidiaNemo\eMach',
    [string]$Work = 'C:\work\_thermal_kit_20260910',
    [ValidateSet('base','sph')][string]$Htc = 'base',
    [ValidatePattern('^[a-zA-Z0-9_]+$')][string]$Attempt = 'ports'
)
# Explicit per-h-set process and result isolation. Invoke once per h-set.
$ErrorActionPreference = 'Stop'
$py = 'C:\Users\moa\.ansys_python_venvs\PyMotorEnv_310\Scripts\python.exe'
$kit = Join-Path $Repo 'mlxperPJT\thermal\plans\PLAN_20260906_assets'
$cdb = 'D:\KDH\simVary\Ansys_Thermal\ff_e10_mesh_v2.cdb'
$run = Join-Path $Work ('d1_measured_' + $Htc + '_' + $Attempt)
$taskName = 'Codex_D1_Measured_' + $Htc + '_' + $Attempt + '_20260910'
$port = if ($Htc -eq 'base') { 50161 } else { 50162 }
if (Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue) {
    throw "MAPDL port $port is already occupied; inspect its owner before restarting."
}
if ((Test-Path -LiteralPath $run) -or (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue)) {
    throw 'Existing D1 task/run directory; inspect it before any restart.'
}
$maps = @((Join-Path $Work 'codex_d4_fullmap\points.json'))
foreach($speed in @(2000,4000,8000,16000)) {
    $maps += Join-Path $Work ('low_parallel_' + $speed + '\points.json')
}
foreach($path in $maps) {
    $doc = Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($doc._dry_run -or -not $doc._gates_ok) { throw "Map not complete: $path" }
}
New-Item -ItemType Directory -Path $run | Out-Null
$arguments = @((Join-Path $kit 'd1_cont_rating.py'), '--repo', $Repo,
    '--cdb', $cdb, '--htc-set', $Htc, '--nproc', '4', '--mode', 'super', '--mapdl-port', $port,
    '--out', $run, '--out-name', ('e10_cont_rating_mcad_' + $Htc + '.json'),
    '--run-dir', (Join-Path $run 'mapdl'), '--log', (Join-Path $run 'run.log'), '--no-git-check')
foreach($path in $maps) { $arguments += @('--loss-map', $path) }
$argumentLine = ($arguments | ForEach-Object { '"' + $_ + '"' }) -join ' '
$action = New-ScheduledTaskAction -Execute $py -Argument $argumentLine -WorkingDirectory $kit
$principal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Hours 2)
Register-ScheduledTask -TaskName $taskName -Action $action -Principal $principal -Settings $settings | Out-Null
Start-ScheduledTask -TaskName $taskName
Get-ScheduledTask -TaskName $taskName | Select-Object TaskName,State
Write-Output "Log: $run\run.log"
