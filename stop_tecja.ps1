$ErrorActionPreference = "SilentlyContinue"

$ports = @(8000, 5174)
$connections = Get-NetTCPConnection `
    -State Listen `
    -ErrorAction SilentlyContinue |
    Where-Object { $_.LocalPort -in $ports }

$processIds = $connections |
    Select-Object -ExpandProperty OwningProcess -Unique

foreach ($processId in $processIds) {
    if ($processId -and $processId -ne $PID) {
        Stop-Process -Id $processId -Force
        Write-Host "Port süreci kapatıldı: $processId" -ForegroundColor Yellow
    }
}

Write-Host "TecJA backend/frontend durduruldu." -ForegroundColor Green
