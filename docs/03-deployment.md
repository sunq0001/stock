# 部署指南

## 一、部署方式选择

| 方式 | 适用场景 | 复杂度 |
|------|---------|--------|
| Docker Compose（推荐） | 本地测试、服务器部署 | 低 |
| Ansible 自动化 | 服务器批量/重复部署 | 中 |
| deploy.py 脚本 | 简易手动部署 | 低 |

## 二、Docker Compose 部署

### 2.1 本地部署

```bash
# 构建并启动
docker compose -f docker-compose.local.yml up -d --build

# 查看日志
docker compose -f docker-compose.local.yml logs -f

# 停止并清理
docker compose -f docker-compose.local.yml down
```

### 2.2 服务器部署

```bash
# 1. SSH 到服务器
ssh root@101.43.3.247

# 2. 拉取代码
cd /var/www/stock
git pull

# 3. 构建并启动
docker compose -f docker-compose.production.yml up -d --build

# 4. 检查状态
docker compose -f docker-compose.production.yml ps
curl http://localhost:8080/api/health
```

## 三、Ansible 自动化部署

### 3.1 安装 Ansible

```bash
pip install ansible PyYAML paramiko docker -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
```

### 3.2 部署

```bash
cd ansible
ansible all -m ping                      # 测试连通性
ansible-playbook deploy.yml              # 一键部署
```

### 3.3 常用操作

```bash
# 只同步代码（不重启）
ansible-playbook deploy.yml --tags sync

# 只重启服务
ansible-playbook deploy.yml --tags restart

# 查看服务日志
ansible all -m shell -a "cd /var/www/stock && docker compose logs -f"

# 查看服务器信息
ansible all -m setup
```

### 3.4 服务器信息

| 项目 | 值 |
|------|-----|
| IP | 101.43.3.247 |
| 用户 | root |
| 密码 | Sandisk88! |
| 项目路径 | /var/www/stock |

## 四、数据同步（本地 → 服务器）

### 4.1 为什么需要数据同步

Docker 镜像只包含代码，不包含数据库数据。服务器首次部署时 InfluxDB 为空，需要初始化。

### 4.2 全量数据同步（推荐）

```bash
# 本地：导出 InfluxDB 数据
docker exec stock-influxdb influx backup /tmp/backup --token my-super-secret-token
docker cp stock-influxdb:/tmp/backup ./influxdb-backup

# 打包
tar czf influxdb-backup.tar.gz influxdb-backup/

# 传到服务器
scp influxdb-backup.tar.gz root@101.43.3.247:/var/www/stock/

# 服务器：恢复
ssh root@101.43.3.247
cd /var/www/stock
tar xzf influxdb-backup.tar.gz
docker exec stock-influxdb influx restore /path/to/backup --token my-super-secret-token
```

### 4.3 数据量估算

| 数据类型 | 估算大小 | 说明 |
|---------|---------|------|
| 大盘指标 | ~10MB | 6500天 × 5品类 × 10字段 |
| 个股K线（4000只×5000天） | ~500MB~1GB | 单次全量，后续增量很小 |
| 分红配股 | ~50MB | 文本数据，体积小 |
| 合计压缩后 | ~100~300MB | tar.gz |

### 4.4 增量更新

日常使用只需采集当天数据，无需重复全量同步：

```bash
# 本地采集当天数据
python sse_market_data_crawler.py --date $(date +%Y-%m-%d)
python data_collector.py --daily

# 或者每天在服务器上跑 cron 更新
```

## 五、Nginx 配置说明

### 5.1 反向代理

```nginx
location /api/ {
    proxy_pass http://172.18.0.2:5000/;   # Flask 容器地址
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

### 5.2 静态文件

```nginx
location / {
    root /usr/share/nginx/html;
    index market.html;
}
```

## 六、故障排除

### 6.1 容器无法启动

```bash
# 检查 Docker 运行状态
docker version

# 检查端口占用
netstat -ano | findstr :8080

# 重新构建（清理缓存）
docker compose build --no-cache
```

### 6.2 API 返回 502

- Nginx 无法代理到 Flask 容器
- 检查 Flask 容器是否运行：`docker ps | grep sse-pe-service`
- 检查 Flask 监听端口：`docker logs sse-pe-service`
- 检查 Nginx 中 `proxy_pass` 的容器 IP/端口是否正确

### 6.3 前端无数据

- 直接访问 API：`curl http://localhost:18082/api/market/pe/history`
- 检查 InfluxDB 是否有数据：`curl http://localhost:18086/health`
- 查看 Flask 日志中是否有错误

### 6.4 Docker 网络问题

- 确认容器在同一个网络：`docker network ls`
- 查看容器IP：`docker inspect <容器名> | grep IPAddress`
- 固定网络为 `bridge` 模式
