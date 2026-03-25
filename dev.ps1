param(
    [string]$BackendHost = "127.0.0.1",
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 5173
)

$ErrorActionPreference = "Stop"

$backendRepo = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $backendRepo "backend"
$frontendDir = Join-Path (Split-Path -Parent $backendRepo) "UltimateGymAsistant-Front-end\frontend"

if (-not (Test-Path $backendDir)) {
    throw "No encontre la carpeta del backend en $backendDir"
}

if (-not (Test-Path $frontendDir)) {
    throw "No encontre la carpeta del frontend en $frontendDir"
}

$backendVenv = Join-Path $backendDir ".venv"
$backendPython = Join-Path $backendVenv "Scripts\python.exe"

if (-not (Test-Path $backendPython)) {
    Write-Host "Creando entorno virtual del backend..."
    Push-Location $backendDir
    try {
        python -m venv .venv
    } finally {
        Pop-Location
    }
}

if (-not (Test-Path $backendPython)) {
    throw "No pude crear el entorno virtual del backend en $backendVenv"
}

$backendStamp = Join-Path $backendVenv ".deps_installed"
if (-not (Test-Path $backendStamp)) {
    Write-Host "Instalando dependencias del backend..."
    Push-Location $backendDir
    try {
        & $backendPython -m pip install --upgrade pip
        & $backendPython -m pip install -r requirements.txt
        New-Item -ItemType File -Path $backendStamp -Force | Out-Null
    } finally {
        Pop-Location
    }
}

if (-not (Test-Path (Join-Path $frontendDir "node_modules"))) {
    Write-Host "Instalando dependencias del frontend..."
    Push-Location $frontendDir
    try {
        npm install --legacy-peer-deps
    } finally {
        Pop-Location
    }
}

$backendCommand = @"
Set-Location '$backendDir'
& '$backendPython' -m uvicorn main:app --reload --host $BackendHost --port $BackendPort
"@

$frontendApiUrl = "http://${BackendHost}:${BackendPort}"
$frontendCommand = @"
Set-Location '$frontendDir'
`$env:VITE_API_URL='$frontendApiUrl'
npm run dev -- --host 127.0.0.1 --port $FrontendPort
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCommand | Out-Null
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCommand | Out-Null

Write-Host ""
Write-Host "Backend:  http://${BackendHost}:${BackendPort}/docs"
Write-Host "Frontend: http://127.0.0.1:${FrontendPort}"
Write-Host ""
Write-Host "Se abrieron dos terminales nuevas para correr el proyecto."
