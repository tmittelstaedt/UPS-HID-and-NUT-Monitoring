param (
    [string]$NutServer = "172.16.16.20",  # NUT server IP
    [string]$UpsName   = "nutdev-usb1",   # Known UPS name
    [int]$Port         = 3493,
    [int]$TimeoutSeconds = 5,
    [string]$Username  = "",              # Optional NUT username
    [string]$Password  = ""               # Optional NUT password
)

$client = $null
$reader = $null
$writer = $null

try {
    # Connect to NUT server
    $client = New-Object System.Net.Sockets.TcpClient
    $client.ReceiveTimeout = $TimeoutSeconds * 1000
    $client.SendTimeout = $TimeoutSeconds * 1000
    $client.Connect($NutServer, $Port)

    $stream = $client.GetStream()
    $reader = New-Object System.IO.StreamReader($stream)
    $writer = New-Object System.IO.StreamWriter($stream)
    $writer.AutoFlush = $true

    Write-Host "Connected to NUT server $NutServer on port $Port" -ForegroundColor Green

    # Optional authentication
    if ($Username -and $Password) {
        $writer.WriteLine("USERNAME $Username")
        $authResp = $reader.ReadLine()
        if ($authResp -notmatch "^OK") {
            throw "Authentication failed at USERNAME step: $authResp"
        }

        $writer.WriteLine("PASSWORD $Password")
        $passResp = $reader.ReadLine()
        if ($passResp -notmatch "^OK") {
            throw "Authentication failed at PASSWORD step: $passResp"
        }
    }

    # Request UPS variables
    $writer.WriteLine("LIST VAR $UpsName")

    $vars = @{}
    while ($true) {
        $line = $reader.ReadLine()
        if (-not $line) { break } # Connection closed
        if ($line -match '^VAR\s+\S+\s+(\S+)\s+"(.*)"$') {
            $vars[$matches[1]] = $matches[2]
        }
        elseif ($line -match '^END LIST VAR') {
            break
        }
    }

    # Convert to object for easy access
    $upsStatus = [PSCustomObject]$vars

    # Output structured data
    Write-Host "`nUPS Status Object:" -ForegroundColor Cyan
    $upsStatus | Format-List

    # Example: Access specific values
    if ($upsStatus.PSObject.Properties.Name -contains 'battery.charge') {
        Write-Host "`nBattery Charge: $($upsStatus.'battery.charge')%"
    }
    if ($upsStatus.PSObject.Properties.Name -contains 'ups.status') {
        Write-Host "UPS Status: $($upsStatus.'ups.status')"
    }
}
catch {
    Write-Error "Failed to connect or retrieve data: $_"
}
finally {
    # Cleanup
    if ($writer) { $writer.Close() }
    if ($reader) { $reader.Close() }
    if ($client) { $client.Close() }
}
