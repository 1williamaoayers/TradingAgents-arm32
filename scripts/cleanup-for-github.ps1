# GitHub上传前清理脚本 (PowerShell版本)
# 删除不必要的测试文件、缓存、临时文件等

Write-Host "🧹 清理项目,准备上传GitHub..." -ForegroundColor Yellow
Write-Host ""

$deletedFiles = 0
$deletedDirs = 0

# 1. 删除Python缓存
Write-Host "📦 清理Python缓存..." -ForegroundColor Cyan
Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
Get-ChildItem -Path . -Recurse -File -Include "*.pyc","*.pyo","*.pyd" -ErrorAction SilentlyContinue | Remove-Item -Force
Write-Host "✅ Python缓存已清理" -ForegroundColor Green

# 2. 删除根目录的测试文件
Write-Host "🧪 清理根目录测试文件..." -ForegroundColor Cyan
Get-ChildItem -Path . -File -Filter "test_*.py" -ErrorAction SilentlyContinue | Remove-Item -Force
Remove-Item -Path "configure_newsapi.py" -Force -ErrorAction SilentlyContinue
Remove-Item -Path "investigate_akshare_news.py" -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path . -File -Filter "news_report_*.md" -ErrorAction SilentlyContinue | Remove-Item -Force
Write-Host "✅ 根目录测试文件已清理" -ForegroundColor Green

# 3. 删除临时文件和备份
Write-Host "📄 清理临时文件..." -ForegroundColor Cyan
Get-ChildItem -Path . -Recurse -File -Include "*.tmp","*.temp","*.bak","*.old" -ErrorAction SilentlyContinue | Remove-Item -Force
Write-Host "✅ 临时文件已清理" -ForegroundColor Green

# 4. 删除日志文件
Write-Host "📝 清理日志文件..." -ForegroundColor Cyan
Get-ChildItem -Path . -Recurse -File -Filter "*.log" -ErrorAction SilentlyContinue | Remove-Item -Force
if (Test-Path "logs") {
    Get-ChildItem -Path "logs" -Recurse | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue
}
Write-Host "✅ 日志文件已清理" -ForegroundColor Green

# 5. 删除数据缓存
Write-Host "💾 清理数据缓存..." -ForegroundColor Cyan
if (Test-Path "data") {
    Get-ChildItem -Path "data" -Recurse | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue
}
if (Test-Path "cache") {
    Get-ChildItem -Path "cache" -Recurse | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue
}
if (Test-Path "backups") {
    Get-ChildItem -Path "backups" -Recurse | Remove-Item -Force -Recurse -ErrorAction SilentlyContinue
}
Write-Host "✅ 数据缓存已清理" -ForegroundColor Green

# 6. 删除.env文件(保留.env.docker和.env.example)
Write-Host "🔐 清理环境变量文件..." -ForegroundColor Cyan
if (Test-Path ".env") {
    Remove-Item -Path ".env" -Force
    Write-Host "✅ .env文件已删除(保留.env.docker和.env.example)" -ForegroundColor Green
}

# 7. 删除IDE配置
Write-Host "💻 清理IDE配置..." -ForegroundColor Cyan
if (Test-Path ".vscode\settings.json") {
    Remove-Item -Path ".vscode\settings.json" -Force -ErrorAction SilentlyContinue
}
if (Test-Path ".idea") {
    Remove-Item -Path ".idea" -Recurse -Force -ErrorAction SilentlyContinue
}
Write-Host "✅ IDE配置已清理" -ForegroundColor Green

# 8. 删除构建产物
Write-Host "🏗️ 清理构建产物..." -ForegroundColor Cyan
if (Test-Path "build") {
    Remove-Item -Path "build" -Recurse -Force -ErrorAction SilentlyContinue
}
if (Test-Path "dist") {
    Remove-Item -Path "dist" -Recurse -Force -ErrorAction SilentlyContinue
}
Get-ChildItem -Path . -Recurse -Directory -Filter "*.egg-info" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
Write-Host "✅ 构建产物已清理" -ForegroundColor Green

# 9. 删除不必要的大文件
Write-Host "📦 清理大文件..." -ForegroundColor Cyan
if (Test-Path "uv.lock") {
    Remove-Item -Path "uv.lock" -Force -ErrorAction SilentlyContinue
}
Write-Host "✅ 大文件已清理" -ForegroundColor Green

# 10. 保留必要的空目录结构
Write-Host "📁 创建必要的空目录..." -ForegroundColor Cyan
New-Item -ItemType Directory -Path "data" -Force | Out-Null
New-Item -ItemType Directory -Path "logs" -Force | Out-Null
New-Item -ItemType Directory -Path "cache" -Force | Out-Null
New-Item -ItemType Directory -Path "backups" -Force | Out-Null
New-Item -ItemType File -Path "data\.gitkeep" -Force | Out-Null
New-Item -ItemType File -Path "logs\.gitkeep" -Force | Out-Null
New-Item -ItemType File -Path "cache\.gitkeep" -Force | Out-Null
New-Item -ItemType File -Path "backups\.gitkeep" -Force | Out-Null
Write-Host "✅ 目录结构已保留" -ForegroundColor Green

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host "✅ 清理完成!" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host ""
Write-Host "已清理:"
Write-Host "  ✅ Python缓存(__pycache__, *.pyc)"
Write-Host "  ✅ 测试文件(test_*.py)"
Write-Host "  ✅ 临时文件(*.tmp, *.bak)"
Write-Host "  ✅ 日志文件(*.log)"
Write-Host "  ✅ 数据缓存(data/, cache/)"
Write-Host "  ✅ 环境变量(.env)"
Write-Host "  ✅ IDE配置(.vscode, .idea)"
Write-Host "  ✅ 构建产物(build/, dist/)"
Write-Host ""
Write-Host "保留:"
Write-Host "  ✅ .env.docker (Docker配置模板)"
Write-Host "  ✅ .env.example (配置示例)"
Write-Host "  ✅ 源代码文件"
Write-Host "  ✅ 文档文件"
Write-Host "  ✅ 配置文件"
Write-Host ""
Write-Host "下一步:"
Write-Host "  1. 检查 git status"
Write-Host "  2. git add ."
Write-Host "  3. git commit -m 'Initial commit'"
Write-Host "  4. git push"
Write-Host ""
