param(
    [string]$Repo = 'D:\KDH\NvidiaNemo\eMach',
    [string]$Python = 'C:\Users\moa\.ansys_python_venvs\PyMotorEnv_310\Scripts\python.exe',
    [string]$RunDirectory = 'C:\work\_thermal_kit_20260910\d4_map',
    [string]$Speeds = '2000,4000,8000,16000',
    [string]$Currents = '115.075,230.05,345.025,460.0',
    [string]$TaskName = 'eMach_D4_Interactive',
    [double]$Phase = 36.0,
    [ValidateRange(1, 4)][int]$MaxInstances = 1
)
# Run the Python driver in the logged-in user's desktop session. No password,
# privilege elevation, automatic trigger, or attachment to another model.
$ErrorActionPreference = 'Stop'
$driver = Join-Path $Repo 'mlxperPJT\thermal\plans\PLAN_20260906_assets\d4_loss_map.py'
foreach ($path in @($Python, $driver)) {
    if (-not (Test-Path -LiteralPath $path)) { throw "Missing: $path" }
}
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    throw "Task already exists: $TaskName. Inspect it before reusing its name."
}
if (@(Get-Process MotorCAD -ErrorAction SilentlyContinue).Count -ge $MaxInstances) {
    throw "MotorCAD instance limit reached ($MaxInstances). Inspect active workloads first."
}
if (Test-Path -LiteralPath $RunDirectory) {
    throw "Run directory already exists: $RunDirectory. Use a fresh directory."
}
New-Item -ItemType Directory -Path $RunDirectory | Out-Null
$arguments = @(
    $driver, '--repo', $Repo, '--speeds', $Speeds, '--currents', $Currents,
    '--phase', $Phase.ToString([System.Globalization.CultureInfo]::InvariantCulture),
    '--work-dir', (Join-Path $RunDirectory 'model'),
    '--out', (Join-Path $RunDirectory 'points.json'),
    '--log', (Join-Path $RunDirectory 'run.log')
)
foreach ($argument in $arguments) {
    if ($argument.Contains('"') -or $argument.EndsWith('\')) {
        throw 'Arguments must not contain quotes or end with a backslash.'
    }
}
$argumentLine = ($arguments | ForEach-Object { '"' + $_ + '"' }) -join ' '
$action = New-ScheduledTaskAction -Execute $Python -Argument $argumentLine -WorkingDirectory (Split-Path $driver)
$principal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Hours 12)
Register-ScheduledTask -TaskName $TaskName -Action $action -Principal $principal -Settings $settings | Out-Null
Start-ScheduledTask -TaskName $TaskName
Get-ScheduledTask -TaskName $TaskName | Select-Object TaskName, State
Write-Output "Log: $(Join-Path $RunDirectory 'run.log')"
# After completion, inspect Get-ScheduledTaskInfo and points.json, then remove
# this one-off task using Unregister-ScheduledTask -TaskName ... -Confirm:$false.
