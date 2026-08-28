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

$DatabaseUrlConfigured = Select-String -LiteralPath ".env" -Pattern "^DATABASE_URL=.+" -Quiet
if (-not $DatabaseUrlConfigured) {
    throw ".env 缺少 DATABASE_URL，无法初始化 PostgreSQL Checkpoint。"
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
    throw "LangGraph Checkpoint 数据库初始化失败。请根据上方错误检查 DATABASE_URL、数据库状态和连接权限。"
}

Write-Host "项目依赖和 PostgreSQL Checkpoint 初始化完成。"
