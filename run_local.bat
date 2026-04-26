@echo off
REM 上证PE项目本地开发启动脚本 (CMD/Batch)

echo 上证PE项目本地开发环境启动
echo ==========================================

REM 检查Python
where python >nul 2>nul
if %errorlevel% equ 0 (
    set python_cmd=python
) else (
    where python3 >nul 2>nul
    if %errorlevel% equ 0 (
        set python_cmd=python3
    ) else (
        echo 错误: 未找到Python，请先安装Python 3.7+
        pause
        exit /b 1
    )
)

echo 使用Python命令: %python_cmd%

REM 检查虚拟环境
if exist venv (
    echo 激活虚拟环境...
    call venv\Scripts\activate.bat
) else (
    echo 创建虚拟环境...
    %python_cmd% -m venv venv
    call venv\Scripts\activate.bat
    
    echo 安装依赖包...
    pip install -r requirements.txt
)

REM 加载环境变量（简单版本）
echo 加载环境配置...
if exist .env (
    for /f "tokens=1,2 delims== eol=#" %%a in (.env) do (
        set "%%a=%%b"
        echo   %%a = %%b
    )
)

REM 显示配置
echo.
echo 当前配置:
echo   数据源: %DATA_SOURCE%
echo   远程API: %REMOTE_API_URL%
echo   服务端口: %PORT%
echo.

REM 启动服务
echo 启动PE数据服务...
echo 服务地址: http://localhost:%PORT%
echo API接口: http://localhost:%PORT%/api/market/pe
echo 健康检查: http://localhost:%PORT%/api/health
echo.
echo 按 Ctrl+C 停止服务
echo.

%python_cmd% pe_data_service.py