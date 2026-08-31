$ErrorActionPreference = "Stop"

$TemplateRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $TemplateRoot

if (-not (Test-Path -LiteralPath ".env")) {
    Copy-Item -LiteralPath ".env.example" -Destination ".env"
    Write-Host "已从 .env.example 创建 .env，请在运行 Agent 前填写 DEEPSEEK_API_KEY。"
}

$DeepSeekKeyConfigured = Select-String -LiteralPath ".env" -Pattern "^DEEPSEEK_API_KEY=.+" -Quiet
if (-not $DeepSeekKeyConfigured) {
    Write-Warning ".env 尚未填写 DEEPSEEK_API_KEY；模型调用会失败。"
}

$PostgresUriConfigured = Select-String -LiteralPath ".env" -Pattern "^POSTGRES_URI=.+" -Quiet
if (-not $PostgresUriConfigured) {
    throw ".env 缺少 POSTGRES_URI。请填写当前 Agent 项目的独立 PostgreSQL 数据库地址。"
}

$PostgresUriPlaceholder = Select-String -LiteralPath ".env" -Pattern "<project_database>" -Quiet
if ($PostgresUriPlaceholder) {
    throw ".env 中的 POSTGRES_URI 仍包含 <project_database>，请替换为当前项目的独立数据库名。"
}

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "未找到 uv。请先安装 uv。"
}

uv sync
if ($LASTEXITCODE -ne 0) {
    throw "项目依赖安装失败。"
}

Write-Host "项目依赖安装完成。PostgreSQL 服务和项目数据库由外部统一管理。"
