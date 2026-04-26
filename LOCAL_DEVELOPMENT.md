# 本地开发环境指南

本目录包含上证市盈率数据项目的本地开发环境，可用于测试和开发。

## 项目结构

```
stock-project-local/
├── html/                    # 前端静态文件
│   ├── index.html          # 主页面
│   ├── stock.html          # 股票详情页面
│   └── data/               # 数据文件目录
├── nginx/                  # Nginx配置
│   └── conf.d/
│       └── default.conf    # Nginx站点配置
├── pe_data_service.py      # 核心数据服务（支持本地/远程数据源）
├── requirements.txt        # Python依赖
├── run_local.ps1          # PowerShell启动脚本
├── run_local.bat          # 批处理启动脚本
├── start_simple.py        # 简单启动脚本
├── docker-compose.yml     # Docker编排配置
├── Dockerfile.web         # Web服务Dockerfile
├── Dockerfile             # 爬虫Dockerfile（原始）
├── Dockerfile.crawler     # 爬虫Dockerfile（备用）
├── sse_pe_crawler.py      # 爬虫脚本（原始）
├── sse_playwright_crawler.py # 爬虫脚本（Playwright版本）
└── update_chart.py        # 图表更新脚本
```

## 快速开始

### 方法一：直接运行Python服务（推荐）

1. 安装Python依赖：
   ```bash
   pip install -r requirements.txt
   ```

2. 启动服务：
   ```bash
   python start_simple.py
   ```
   或者使用脚本：
   ```bash
   # Windows
   run_local.bat
   # PowerShell
   .\run_local.ps1
   ```

3. 访问应用：
   - 前端页面：http://localhost:18082/
   - API接口：http://localhost:18082/api/market/pe
   - 健康检查：http://localhost:18082/api/health

### 方法二：使用Docker Compose

1. 构建并启动服务：
   ```bash
   docker-compose up -d
   ```

2. 访问应用：
   - 前端页面：http://localhost:18082/ (通过web服务)
   - 通过nginx：http://localhost:8080/ (如果启用了nginx服务)

3. 停止服务：
   ```bash
   docker-compose down
   ```

## 配置说明

### 数据源模式

服务支持两种数据源模式，通过环境变量 `DATA_SOURCE` 控制：

1. **remote_api**（默认）：代理到远程服务器API
   ```
   DATA_SOURCE=remote_api
   REMOTE_API_URL=http://101.43.3.247:8082/api/market/pe
   ```

2. **local_db**：使用本地SQLite数据库
   ```
   DATA_SOURCE=local_db
   LOCAL_DB_PATH=sse_pe_data.db
   ```

### 端口配置

- 默认服务端口：18082（可通过环境变量 `PORT` 修改）
- nginx端口：8080（如果启用）

## 开发测试

### 测试远程API连通性

```bash
python -c "import requests; r = requests.get('http://101.43.3.247:8082/api/market/pe'); print('状态码:', r.status_code)"
```

### 测试本地服务

```bash
python test_local_service.py
```

### 完整功能测试

```bash
python test_full_service.py
```

## 爬虫脚本

本地环境中包含爬虫脚本，可用于测试数据采集：

```bash
# 运行原始爬虫
python sse_pe_crawler.py

# 运行Playwright爬虫（需要安装playwright）
python sse_playwright_crawler.py
```

## 注意事项

1. **远程API依赖**：默认配置依赖远程服务器API（101.43.3.247:8082），请确保网络连通性
2. **数据更新**：本地服务仅代理数据，不存储数据。如需更新数据，需在服务器上运行爬虫
3. **文件权限**：确保对 `html/data/` 目录有写入权限（如果需要本地数据存储）
4. **跨域问题**：服务已启用CORS，前端可直接调用API

## 故障排除

### 服务无法启动
- 检查Python依赖是否安装：`pip list | grep flask`
- 检查端口是否被占用：`netstat -ano | findstr :18082`
- 检查环境变量配置是否正确

### API返回无数据
- 检查远程API是否可达
- 检查网络连接和防火墙设置
- 查看服务日志：`python pe_data_service.py` 直接运行查看输出

### 前端页面无法加载
- 检查静态文件路径：确保 `html/` 目录存在且包含文件
- 检查浏览器控制台错误信息
- 尝试直接访问API端点测试连通性

## 扩展开发

### 添加新API端点
在 `pe_data_service.py` 中添加新的 `@app.route` 装饰函数

### 修改前端
编辑 `html/` 目录下的HTML、CSS、JS文件

### 自定义配置
通过 `.env` 文件或环境变量覆盖默认配置

---

如有问题，请参考服务器部署文档或联系项目维护者。