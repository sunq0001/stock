# 开发注意事项

## 1. 优先使用国内镜像

安装Python包时，**优先使用国内镜像源**，避免下载超时：

```bash
# 清华镜像（推荐）
pip install xxx -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn

# 阿里云镜像
pip install xxx -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com

# 豆瓣镜像
pip install xxx -i https://pypi.doubanio.com/simple/ --trusted-host pypi.doubanio.com
```

常用包安装示例：
```bash
pip install ansible PyYAML paramiko docker -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
```

## 2. 本地开发环境

### ⚠️ 架构原则（重要）
**数据源统一使用 InfluxDB，禁止混用云端 API！**

| 环境 | 数据源 | 说明 |
|------|--------|------|
| 本地开发 | `pe_data_service_influxdb.py` + 本地 InfluxDB (18086) | 直接从本地数据库读取 |
| 服务器部署 | `pe_data_service_influxdb.py` + 服务器 InfluxDB | 同样使用 InfluxDB |
| ~~旧版本~~ | ~~`pe_data_service.py` + 远程云端API~~ | **已废弃，不再使用** |

### 端口分配（固定不变）
- **InfluxDB**: `18086`
- **Flask 后端**: `18082`
- **Nginx 前端**: `18080`

### 开发流程
```
1. 本地开发测试 → 使用本地 InfluxDB
2. 同步数据到服务器 → 导出/导入 InfluxDB 数据
3. 服务器部署 → 使用服务器的 InfluxDB
```
**永远不要**：本地开发时又用本地 InfluxDB、又调用云端 API，保持数据来源单一！

### 启动本地服务
```bash
cd c:\Users\mss\WorkBuddy\20260414224936\stock-project-local

# 设置环境变量（使用本地 InfluxDB）
$env:INFLUXDB_URL="http://localhost:18086"
$env:INFLUXDB_TOKEN="my-super-secret-token"
$env:INFLUXDB_ORG="stock"
$env:INFLUXDB_BUCKET="market_data"

# 启动服务
python pe_data_service_influxdb.py
```

访问地址：
- 前端：http://localhost:18082/
- API：http://localhost:18082/api/market/pe/history

## 3. 服务器部署（Ansible）

### 安装Ansible
```bash
pip install ansible PyYAML paramiko docker -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
```

### 一键部署到服务器
```bash
cd ansible
ansible-playbook deploy.yml
```

服务器信息：
- 地址：101.43.3.247
- 用户：root
- 密码：Sandisk88!

## 4. Docker Compose（备用方式）

如果不用Ansible，手动部署：
```bash
ssh root@101.43.3.247
cd /root/stock-project
git pull
docker-compose up -d --build
```
