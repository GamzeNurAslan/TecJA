$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonPath = Join-Path $projectRoot ".venv\Scripts\python.exe"
$frontendPath = Join-Path $projectRoot "frontend"
$logPath = Join-Path $projectRoot "logs"

if (-not (Test-Path $pythonPath)) {
    throw "Python sanal ortamı bulunamadı: $pythonPath"
}

if (-not (Test-Path (Join-Path $frontendPath "package.json"))) {
    throw "Frontend package.json bulunamadı: $frontendPath"
}

New-Item -ItemType Directory -Force -Path $logPath | Out-Null

function Test-Service {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Url
    )

    try {
        $response = Invoke-WebRequest `
            -UseBasicParsing `
            -Uri $Url `
            -TimeoutSec 2
        return $response.StatusCode -ge 200 -and $response.StatusCode -lt 500
    }
    catch {
        return $false
    }
}

$backendUrl = "http://127.0.0.1:8000/api/health"
$frontendUrl = "http://127.0.0.1:5174/"

if (Test-Service $backendUrl) {
    Write-Host "Backend zaten çalışıyor: http://127.0.0.1:8000" -ForegroundColor Green
}
else {
    $backendOut = Join-Path $logPath "backend.out.log"
    $backendErr = Join-Path $logPath "backend.err.log"

    Start-Process `
        -FilePath $pythonPath `
        -ArgumentList @(
            "-m",
            "uvicorn",
            "backend.app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000"
        ) `
        -WorkingDirectory $projectRoot `
        -WindowStyle Hidden `
        -RedirectStandardOutput $backendOut `
        -RedirectStandardError $backendErr | Out-Null

    $backendReady = $false
    1..15 | ForEach-Object {
        if (-not $backendReady) {
            Start-Sleep -Seconds 1
            $backendReady = Test-Service $backendUrl
        }
    }

    if ($backendReady) {
        Write-Host "Backend başlatıldı: http://127.0.0.1:8000" -ForegroundColor Green
    }
    else {
        Write-Warning "Backend başlatılamadı. Log: $backendErr"
    }
}

if (Test-Service $frontendUrl) {
    Write-Host "Frontend zaten çalışıyor: http://127.0.0.1:5174" -ForegroundColor Green
}
else {
    $frontendOut = Join-Path $logPath "frontend.out.log"
    $frontendErr = Join-Path $logPath "frontend.err.log"

    Start-Process `
        -FilePath "npm.cmd" `
        -ArgumentList @(
            "run",
            "dev",
            "--",
            "--host",
            "127.0.0.1",
            "--port",
            "5174"
        ) `
        -WorkingDirectory $frontendPath `
        -WindowStyle Hidden `
        -RedirectStandardOutput $frontendOut `
        -RedirectStandardError $frontendErr | Out-Null

    $frontendReady = $false
    1..20 | ForEach-Object {
        if (-not $frontendReady) {
            Start-Sleep -Seconds 1
            $frontendReady = Test-Service $frontendUrl
        }
    }

    if ($frontendReady) {
        Write-Host "Frontend başlatıldı: http://127.0.0.1:5174" -ForegroundColor Green
    }
    else {
        Write-Warning "Frontend başlatılamadı. Log: $frontendErr"
    }
}

Write-Host "TecJA hazır. Tarayıcı: http://127.0.0.1:5174" -ForegroundColor Cyan
