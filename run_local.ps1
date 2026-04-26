# 上证PE项目本地开发启动脚本 (PowerShell)

Write-Host "上证PE项目本地开发环境启动" -ForegroundColor Green
Write-Host "=========================================="

# 检查Python
$pythonCmd = "python"
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = "python"
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    $pythonCmd = "python3"
} else {
    Write-Host "错误: 未找到Python，请先安装Python 3.7+" -ForegroundColor Red
    exit 1
}

Write-Host "使用Python命令: $pythonCmd"

# 检查虚拟环境
$venvPath = "venv"
if (Test-Path $venvPath) {
    Write-Host "激活虚拟环境..."
    & "$venvPath\Scripts\Activate.ps1"
} else {
    Write-Host "创建虚拟环境..."
    & $pythonCmd -m venv venv
    & "$venvPath\Scripts\Activate.ps1"
    
    Write-Host "安装依赖包..."
    pip install -r requirements.txt
}

# 加载环境变量
Write-Host "加载环境配置..."
if (Test-Path .env) {
    Get-Content .env | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($key, $value, "Process")
            Write-Host "  $key = $value"
        }
    }
}

# 显示配置
Write-Host ""
Write-Host "当前配置:"
Write-Host "  数据源: $env:DATA_SOURCE"
Write-Host "  远程API: $env:REMOTE_API_URL"
Write-Host "  服务端口: $env:PORT"
Write-Host ""

# 启动服务
Write-Host "启动PE数据服务..." -ForegroundColor Yellow
Write-Host "服务地址: http://localhost:$env:PORT" -ForegroundColor Cyan
Write-Host "API接口: http://localhost:$env:PORT/api/market/pe" -ForegroundColor Cyan
Write-Host "健康检查: http://localhost:$env:PORT/api/health" -ForegroundColor Cyan
Write-Host ""
Write-Host "按 Ctrl+C 停止服务" -ForegroundColor Gray
Write-Host ""

& $pythonCmd pe_data_service.py