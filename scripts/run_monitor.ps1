param(
    [int]$Limit = 20,
    [int]$SendLimit = 1,
    [string]$State = "data\monitor_state.db",
    [string]$EnvFile = ".env",
    [switch]$Watch,
    [int]$IntervalSeconds = 600,
    [int]$MaxCycles = 0
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$LogDir = Join-Path $ProjectRoot "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$LogFile = Join-Path $LogDir "monitor.log"

Push-Location $ProjectRoot
try {
    "[$Timestamp] start" | Out-File -FilePath $LogFile -Append -Encoding utf8
    if ($Watch) {
        if ($MaxCycles -gt 0) {
            python -m zanao_monitor.cli watch-mini-monitor --env $EnvFile --limit $Limit --interval-seconds $IntervalSeconds --send-limit $SendLimit --state $State --max-cycles $MaxCycles 2>&1 |
                Out-File -FilePath $LogFile -Append -Encoding utf8
        }
        else {
            python -m zanao_monitor.cli watch-mini-monitor --env $EnvFile --limit $Limit --interval-seconds $IntervalSeconds --send-limit $SendLimit --state $State 2>&1 |
                Out-File -FilePath $LogFile -Append -Encoding utf8
        }
    }
    else {
        python -m zanao_monitor.cli run-mini-monitor --env $EnvFile --limit $Limit --send --send-limit $SendLimit --state $State 2>&1 |
            Out-File -FilePath $LogFile -Append -Encoding utf8
    }
    "[$Timestamp] end" | Out-File -FilePath $LogFile -Append -Encoding utf8
}
finally {
    Pop-Location
}
