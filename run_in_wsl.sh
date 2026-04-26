#!/bin/bash
# 在WSL中直接运行Python服务

echo "🚀 在WSL中启动上证PE数据服务..."
echo "================================================"

# 项目路径
PROJECT_PATH="/mnt/c/Users/mss/WorkBuddy/20260414224936/stock-project-local"

# 进入项目目录
cd "$PROJECT_PATH"
echo "项目目录: $(pwd)"

# 安装Python依赖（如果需要）
echo "检查Python依赖..."
if ! python3 -c "import flask" &> /dev/null; then
    echo "安装Flask和相关依赖..."
    pip3 install flask flask-cors requests
fi

# 检查neoData token
TOKEN_FILE="neodata_token.txt"
if [ ! -f "$TOKEN_FILE" ]; then
    echo "⚠️  警告: 未找到neoData token文件"
    echo "   请确保 '$TOKEN_FILE' 文件存在"
    echo "   或者设置环境变量 NEODATA_TOKEN"
fi

# 启动服务
echo "启动Flask服务..."
export DATA_SOURCE="remote_api"
export PORT="5000"
export NEODATA_QUERY_SCRIPT="./neodata_query.py"

echo ""
echo "服务配置:"
echo "  - 数据源: $DATA_SOURCE"
echo "  - 端口: $PORT"
echo "  - neoData脚本: $NEODATA_QUERY_SCRIPT"
echo ""
echo "API端点:"
echo "  - 健康检查: http://localhost:5000/api/health"
echo "  - 大盘PE: http://localhost:5000/api/market/pe"
echo "  - 股票搜索: http://localhost:5000/api/search?q=茅台"
echo ""
echo "前端页面:"
echo "  - 直接在浏览器中打开: file:///mnt/c/Users/mss/WorkBuddy/20260414224936/stock-project-local/html/stock.html"
echo ""
echo "按 Ctrl+C 停止服务"
echo "================================================"

# 运行服务
python3 pe_data_service_extended.py