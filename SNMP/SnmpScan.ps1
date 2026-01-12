param (
    [Parameter(Mandatory=$true)]
    [string]$Network 
)


if ($Network -match '^\d+\.\d+\.\d+\.\d+(\/\d+)?$') {
    $BaseNetwork = ($Network -split '/')[0] -replace '\.\d+$', ''
} else {
    throw "Wrong format, please use 10.30.6.0"
}

$Community = "admin"
$OID       = ".1.3.6.1.4.1.4515.1.3.6.1.1.1.2.0"
$SnmpExe   = "snmpget"
$Timeout   = 1
$MaxThreads = 100

$Results = 1..254 | ForEach-Object -Parallel {
    $IP = "$using:BaseNetwork.$_"
    $cmd = "& '$using:SnmpExe' -v2c -c $using:Community -t $using:Timeout -r 1 $IP $using:OID 2>`$null"

    $output = Invoke-Expression $cmd

    if ($output -and $output -notmatch 'Timeout|No Such Object') {
        if ($output -match 'STRING:\s*"(.*)"') {
            $Product = $matches[1].Trim()
        } elseif ($output -match 'STRING:\s*(.+?)(\s|$)') {
            $Product = $matches[1].Trim('"').Trim()
        } else {
            $Product = $output.Trim()
        }

        [PSCustomObject]@{
            IP          = $IP
            ProductName = $Product
        }
    }
} -ThrottleLimit $MaxThreads

if ($Results) {
    $Results | Sort-Object IP | Format-Table -AutoSize
} else {
    Write-Host "No snmp devices" -ForegroundColor Yellow
}