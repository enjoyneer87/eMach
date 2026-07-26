param(
    [Parameter(Mandatory = $true)]
    [string]$RepoPath,

    [Parameter(Mandatory = $true)]
    [string]$Branch,

    [Parameter(Mandatory = $false)]
    [string]$Remote = "origin"
)

$ErrorActionPreference = "Stop"

$logDir = Join-Path $RepoPath "logs/policy-sync"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}
$logPath = Join-Path $logDir "policy_sync.log"

function Write-Log([string]$msg) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$ts $msg" | Out-File -FilePath $logPath -Append -Encoding utf8
}

try {
    Write-Log "[START] repo=$RepoPath branch=$Branch remote=$Remote"

    Set-Location $RepoPath
    git fetch $Remote | Out-Null
    git checkout $Branch | Out-Null
    git pull --ff-only $Remote $Branch | Out-Null

    Write-Log "[OK] sync complete"
}
catch {
    Write-Log ("[ERROR] " + $_.Exception.Message)
    throw
}
