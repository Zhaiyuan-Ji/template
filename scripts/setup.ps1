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
    Write-Warning ".env 尚未填写 POSTGRES_URI；安装可以继续，但 Agent Server 无法启动。"
}

$PostgresUriPlaceholder = Select-String -LiteralPath ".env" -Pattern "<project_database>" -Quiet
if ($PostgresUriPlaceholder) {
    Write-Warning ".env 中的 POSTGRES_URI 仍包含 <project_database>；启动前必须替换为独立数据库名。"
}

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "未找到 uv。请先安装 uv。"
}

uv sync
if ($LASTEXITCODE -ne 0) {
    throw "项目依赖安装失败。"
}

Write-Host "项目依赖安装完成。填写 .env 后可运行 scripts/dev.ps1 启动 Agent Server。"
