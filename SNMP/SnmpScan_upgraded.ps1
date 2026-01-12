param (
    [Parameter(Mandatory=$true)]
    [string]$Network
)

# ---- Parse network ----
if ($Network -match '^\d+\.\d+\.\d+\.\d+(\/\d+)?$') {
    $BaseNetwork = ($Network -split '/')[0] -replace '\.\d+$', ''
} else {
    throw "Wrong format, please use 10.30.6.0 or 10.30.6.0/24"
}

$Community  = "admin"
$OID        = ".1.3.6.1.4.1.4515.1.3.6.1.1.1.2.0"
$SnmpExe    = "snmpget"
$Timeout    = 1
$MaxThreads = 100

function Invoke-SnmpCheck {
    param(
        [string]$IP,
        [string]$SnmpExe,
        [string]$Community,
        [string]$OID,
        [int]$Timeout
    )

    # Call snmpget directly (no Invoke-Expression)
    $args = @("-v2c","-c",$Community,"-t",$Timeout,"-r","1",$IP,$OID)

    try {
        $output = & $SnmpExe @args 2>$null
    } catch {
        return $null
    }

    if (-not $output) { return $null }
    if ($output -match 'Timeout|No Such Object') { return $null }

    $product = $null
    if ($output -match 'STRING:\s*"(.*)"') {
        $product = $matches[1].Trim()
    } elseif ($output -match 'STRING:\s*(.+?)(\s|$)') {
        $product = $matches[1].Trim('"').Trim()
    } else {
        $product = $output.Trim()
    }

    [PSCustomObject]@{
        IP          = $IP
        ProductName = $product
    }
}

# ---- Ensure snmpget exists ----
$snmpCmd = Get-Command $SnmpExe -ErrorAction SilentlyContinue
if (-not $snmpCmd) {
    throw "Can't find '$SnmpExe' in PATH. Install Net-SNMP or set `$SnmpExe to full path (e.g. C:\...\snmpget.exe)."
}

$Results = @()

# ---- PS7 path: use -Parallel if available ----
if ($PSVersionTable.PSVersion.Major -ge 7) {
    $Results = 1..254 | ForEach-Object -Parallel {
        $ip = "$using:BaseNetwork.$_"
        Invoke-SnmpCheck -IP $ip -SnmpExe $using:SnmpExe -Community $using:Community -OID $using:OID -Timeout $using:Timeout
    } -ThrottleLimit $MaxThreads
}
else {
    # ---- PS5.1 path: use ThreadJob parallelism ----
    if (-not (Get-Module -ListAvailable -Name ThreadJob)) {
        Write-Host "ThreadJob module not found. Installing for CurrentUser..." -ForegroundColor Yellow
        try {
            Install-Module ThreadJob -Scope CurrentUser -Force -ErrorAction Stop
        } catch {
            throw "Failed installing ThreadJob. Run PowerShell as Admin or install it manually: Install-Module ThreadJob -Scope CurrentUser"
        }
    }
    Import-Module ThreadJob | Out-Null

    $jobs = @()
    foreach ($i in 1..254) {
        $ip = "$BaseNetwork.$i"

        # throttle
        while (@($jobs | Where-Object { $_.State -eq 'Running' }).Count -ge $MaxThreads) {
            Start-Sleep -Milliseconds 50
        }

        $jobs += Start-ThreadJob -ArgumentList $ip,$SnmpExe,$Community,$OID,$Timeout -ScriptBlock {
            param($IP,$SnmpExe,$Community,$OID,$Timeout)

            # re-define small helper inside job
            $args = @("-v2c","-c",$Community,"-t",$Timeout,"-r","1",$IP,$OID)
            try { $output = & $SnmpExe @args 2>$null } catch { return }

            if (-not $output) { return }
            if ($output -match 'Timeout|No Such Object') { return }

            $product = $null
            if ($output -match 'STRING:\s*"(.*)"') {
                $product = $matches[1].Trim()
            } elseif ($output -match 'STRING:\s*(.+?)(\s|$)') {
                $product = $matches[1].Trim('"').Trim()
            } else {
                $product = $output.Trim()
            }

            [PSCustomObject]@{
                IP          = $IP
                ProductName = $product
            }
        }
    }

    $Results = Receive-Job -Job $jobs -Wait -AutoRemoveJob
}

if ($Results) {
    $Results | Where-Object { $_ } | Sort-Object IP | Format-Table -AutoSize
} else {
    Write-Host "No snmp devices" -ForegroundColor Yellow
}
