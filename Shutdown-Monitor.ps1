param (
    [string]$ServerIP = "192.168.1.50",  # IP of first machine running Monitor-UPS.ps1 --Server
    [int]$Port = 50000,                  # TCP port
    [int]$CheckInterval = 30,            # Seconds between checks
    [int]$ShutdownDelay = 300,           # Seconds to wait before shutdown after going on battery
    [switch]$Log                         # Enable logging to C:\UPS\shutdown-monitor.log
)

# Prepare logging if enabled
$logFile = "C:\UPS\shutdown-monitor.log"
if ($Log) {
    if (-not (Test-Path "C:\UPS")) {
        New-Item -Path "C:\UPS" -ItemType Directory -Force | Out-Null
    }
    if (-not (Test-Path $logFile)) {
        New-Item -Path $logFile -ItemType File -Force | Out-Null
    }
}

function Write-Log {
    param ([string]$Message)
    if ($Log) {
        $timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        Add-Content -Path $logFile -Value "$timestamp $Message"
    }
}

Write-Host "Shutdown Monitor started. Monitoring UPS at $ServerIP:$Port" -ForegroundColor Cyan
if ($Log) { Write-Log "Shutdown Monitor started. Monitoring UPS at $ServerIP:$Port" }

$lastStatus = $null
$shutdownPending = $false
$shutdownStartTime = $null

function Get-UPSStatusFromServer {
    param ($ip, $port)

    try {
        $tcpClient = New-Object System.Net.Sockets.TcpClient
        $tcpClient.Connect($ip, $port)
        $stream = $tcpClient.GetStream()
        $reader = New-Object System.IO.StreamReader($stream)
        $json = $reader.ReadToEnd()
        $tcpClient.Close()

        if (-not [string]::IsNullOrWhiteSpace($json)) {
            return $json | ConvertFrom-Json
        }
    }
    catch {
        Write-Warning "Failed to connect to UPS server: $_"
    }
    return $null
}

while ($true) {
    $statusObj = Get-UPSStatusFromServer -ip $ServerIP -port $Port

    if ($statusObj) {
        $currentStatus = $statusObj.Status
        $battery = $statusObj.BatteryPercent
        $timeStamp = $statusObj.TimestampUTC

        Write-Host "[$timeStamp] UPS Status: $currentStatus, Battery: $battery%" -ForegroundColor Yellow

        if ($currentStatus -eq "On Battery") {
            if (-not $shutdownPending) {
                $shutdownPending = $true
                $shutdownStartTime = Get-Date
                Write-Host "AC power lost. Shutdown scheduled in $ShutdownDelay seconds unless power returns." -ForegroundColor Red
                Write-Log "Power failure detected. Shutdown scheduled in $ShutdownDelay seconds unless power returns."
            }
            else {
                $elapsed = (Get-Date) - $shutdownStartTime
                if ($elapsed.TotalSeconds -ge $ShutdownDelay) {
                    Write-Host "AC power still offline after $ShutdownDelay seconds. Shutting down..." -ForegroundColor Red
                    Write-Log "Shutdown initiated after $ShutdownDelay seconds on battery."
                    Stop-Computer -Force
                }
            }
        }
        elseif ($currentStatus -eq "Online") {
            if ($shutdownPending) {
                Write-Host "AC power restored. Shutdown canceled." -ForegroundColor Green
                Write-Log "AC power restored. Shutdown canceled."
            }
            $shutdownPending = $false
            $shutdownStartTime = $null
        }
        else {
            Write-Host "UPS status unknown. No shutdown action taken." -ForegroundColor Gray
        }

        $lastStatus = $currentStatus
    }
    else {
        Write-Warning "No UPS data received from server."
    }

    Start-Sleep -Seconds $CheckInterval
}
