$ErrorActionPreference = "Stop"

$TemplateRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $TemplateRoot

if (-not (Test-Path -LiteralPath ".env")) {
    Copy-Item -LiteralPath ".env.example" -Destination ".env"
    Write-Host "已从 .env.example 创建 .env，请在运行 Agent 前填写 DEEPSEEK_API_KEY。"
}

$DeepSeekKeyConfigured = Select-String -LiteralPath ".env" -Pattern "^DEEPSEEK_API_KEY=.+" -Quiet
if (-not $DeepSeekKeyConfigured) {
    Write-Warning ".env 尚未填写 DEEPSEEK_API_KEY；数据库可以初始化，但模型调用会失败。"
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "未找到 Docker。请先安装并启动 Docker Desktop。"
}

docker info *> $null
if ($LASTEXITCODE -ne 0) {
    throw "Docker Engine 未运行。请先启动 Docker Desktop。"
}

docker compose up -d postgres
if ($LASTEXITCODE -ne 0) {
    throw "PostgreSQL 容器启动失败。"
}

$ContainerId = docker compose ps -q postgres
if (-not $ContainerId) {
    throw "没有找到 PostgreSQL 容器。"
}

$Healthy = $false
for ($Attempt = 1; $Attempt -le 30; $Attempt++) {
    $Status = docker inspect --format "{{.State.Health.Status}}" $ContainerId
    if ($Status -eq "healthy") {
        $Healthy = $true
        break
    }
    Start-Sleep -Seconds 2
}

if (-not $Healthy) {
    throw "PostgreSQL 在 60 秒内没有进入 healthy 状态。"
}

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "未找到 uv。请先安装 uv。"
}

uv sync
if ($LASTEXITCODE -ne 0) {
    throw "项目依赖安装失败。"
}

uv run agent-db-setup
if ($LASTEXITCODE -ne 0) {
    throw "LangGraph Checkpoint 数据库初始化失败。"
}

Write-Host "Template 基础环境初始化完成。"
