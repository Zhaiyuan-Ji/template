$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $ProjectRoot

$EnvPath = Join-Path $ProjectRoot ".env"
if (-not (Test-Path -LiteralPath $EnvPath -PathType Leaf)) {
    throw "缺少 .env。请先运行 scripts/setup.ps1，再填写项目配置。"
}

foreach ($Line in Get-Content -LiteralPath $EnvPath) {
    $TrimmedLine = $Line.Trim()
    if (-not $TrimmedLine -or $TrimmedLine.StartsWith("#")) {
        continue
    }

    $Parts = $TrimmedLine -split "=", 2
    if ($Parts.Count -ne 2) {
        continue
    }

    [Environment]::SetEnvironmentVariable($Parts[0].Trim(), $Parts[1], "Process")
}

$PostgresUri = [Environment]::GetEnvironmentVariable("POSTGRES_URI", "Process")
if (-not $PostgresUri) {
    throw ".env 缺少 POSTGRES_URI。"
}
if ($PostgresUri.Contains("<project_database>")) {
    throw "POSTGRES_URI 仍包含 <project_database>，请替换为当前项目的独立数据库名。"
}

try {
    $ParsedPostgresUri = [Uri]$PostgresUri
} catch {
    throw "POSTGRES_URI 不是有效的 URI。"
}

if ($ParsedPostgresUri.Host -ne "host.docker.internal") {
    throw "POSTGRES_URI 必须使用 host.docker.internal 连接宿主机 PostgreSQL。"
}

$DatabaseName = $ParsedPostgresUri.AbsolutePath.Trim("/")
if ($DatabaseName -notmatch "^[a-z0-9_]+$") {
    throw "PostgreSQL 数据库名只能包含小写字母、数字和下划线。"
}
if ($DatabaseName -eq "langgraph") {
    throw "不能使用公共默认数据库 langgraph，请为当前 Agent 创建独立数据库。"
}

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "未找到 uv。请先安装 uv。"
}

uv run langgraph up `
    -c langgraph.dev.json `
    --postgres-uri $PostgresUri `
    --watch `
    --wait

if ($LASTEXITCODE -ne 0) {
    throw "Agent Server 启动失败。请检查 Graph 配置、PostgreSQL 和 Docker 状态。"
}
