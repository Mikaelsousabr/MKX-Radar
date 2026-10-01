$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
try {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw "Instale o Docker Desktop antes de continuar." }
    docker info *> $null
    if ($LASTEXITCODE -ne 0) { throw "Abra o Docker Desktop e aguarde Engine running. Depois execute novamente." }
    $engineType = docker info --format '{{.OSType}}'
    if ($engineType -ne 'linux') { throw "Configure o Docker Desktop para usar conteineres Linux." }
    New-Item -ItemType Directory -Force gmapsdata | Out-Null
    Write-Host "Preparando o MKX Radar. A primeira execucao pode levar alguns minutos." -ForegroundColor Cyan
    docker compose -f compose.mkx.yaml up -d --build
    if ($LASTEXITCODE -ne 0) { throw "A inicializacao falhou. Confira a mensagem acima (ou se a porta 8081 esta ocupada)." }
    $ready = $false
    for ($attempt = 0; $attempt -lt 45; $attempt++) {
        try {
            $probe = Invoke-WebRequest 'http://127.0.0.1:8081/api/v1/jobs' -UseBasicParsing -TimeoutSec 2
            if ($probe.StatusCode -eq 200) { $ready = $true; break }
        } catch { }
        Start-Sleep -Seconds 2
    }
    if (-not $ready) { docker compose -f compose.mkx.yaml logs --tail 30; throw "O motor ainda nao respondeu. Confira os logs acima." }
    Start-Process 'http://localhost:8081'
    Write-Host "MKX Radar iniciado: http://localhost:8081" -ForegroundColor Green
    Write-Host "Pode fechar esta janela. Mantenha o Docker Desktop aberto."
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
