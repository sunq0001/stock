# 踩坑记录

> 遇到异常行为时先翻这里，大概率是踩过的坑。

## 后端

### K线tooltip涨跌幅显示 -80% 多

**症状**：平安银行(000001) K线 tooltip 显示 -88% 等异常百分比，其他股票正常。

**原因**：ECharts tooltip 返回的 `k.value` 是 **5元素数组** `[index, open, close, low, high]`，代码直接用 `[open, close, low, high]` 解构导致 `open` 被赋值为 index（如 100），涨跌幅公式 `(close - 100) / 100` 产生 -80%。

**修复**：判断数组长度 ≥ 5 时跳过首位：
```javascript
const [open, close, low, high] = Array.isArray(val) 
  ? (val.length >= 5 ? [val[1], val[2], val[3], val[4]] : val) 
  : [0, 0, 0, 0];
```

### NaN 导致 JSON 解析失败

**症状**：Flask 返回的 JSON 中包含 `NaN`，前端 `JSON.parse` 报错。

**原因**：InfluxDB 返回的数据中有 `NaN` 值，`jsonify` 默认不处理 NaN。

**修复**：添加全局 NaN → null 替换：
```python
def _clean_nan(obj):
    if isinstance(obj, float) and math.isnan(obj): return None
    if isinstance(obj, dict): return {k: _clean_nan(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)): return [_clean_nan(v) for v in obj]
    return obj
```
并替换 `flask.jsonify`。

### akshare 分红配股报错

**症状**：`/api/dividend/<code>` 或 `/api/allotment/<code>` 返回 500 错误。

**原因**：
1. akshare 返回值字段名变化（`实施方案分红说明` 等为 None 时 `str()` 报错）
2. Python 3.12+ 与 akshare 兼容性问题

**修复**：
1. 加 `_safe_str()` 处理 None/NaN 值
2. 使用 Python 3.11 运行（Docker 镜像用 `python:3.11-slim`）

### 分红日期差一天

**症状**：tooltip 中分红日期显示不对，比如 6/12 分红但在 K 线图上对应的是 6/13 的数据。

**原因**：分红 API 返回的 `date` 是**股权登记日**（T日），K线中对应的应该是**除权日**（T+1日）。代码中优先匹配了 `date` 而不是 `ex_date`。

**修复**：前端所有分红日期匹配改为优先用 `ex_date`：
```javascript
const d = div.ex_date || div.date || '';
```

### API 只返回 5 条数据

**症状**：大盘 PE 历史数据只有几条，不是全部。

**原因**：Flux 查询用 `r["type"]` 过滤但爬虫写入的是 `product_code` 标签（tag），不是 `type` 字段（field）。

**修复**：去掉类型过滤，直接查询所有数据。

### Docker 容器的端口与服务端口混淆

**症状**：容器内 Flask 监听 18082 但 nginx 连不上。

**原因**：把宿主机端口（18082）当容器内端口用了。容器间通信要用容器内端口（5000）。

**修复**：Flask 固定监听 `PORT` 环境变量（默认 5000），nginx 的 `proxy_pass` 用 `http://web:5000`。

### docker-compose 缺少环境变量导致端口不对

**症状**：Flask 容器启动后监听的端口不是预期的。

**原因**：`docker-compose.local.yml` 中 web 服务缺少 `PORT` 环境变量。

**修复**：加上 `PORT: 5000`。

## 前端

### 分红标记叠加层不显示

**症状**：K线图下方没有分红/配股标签。

**原因**：`divOverlay` 的 CSS `pointer-events: none` 影响了子元素交互，或者 ECharts 缩放后标记位置没刷新。

**修复**：标记容器单独设置 `pointer-events: auto`，缩放事件后 `setTimeout(renderDividendMarkers, 50)`。

### 除权日涨跌幅显示异常

**症状**：除权日当天涨跌幅显示 -10% 等大幅变动。

**原因**：前复权 K 线的除权日本身就是跳变的，计算当日涨跌幅没有意义。

**修复**：tooltip 中检测到除权日时显示"除权日"而不是百分比。

## 部署

### git push 到 GitHub 超时

**症状**：`git push origin main` 报 `Failed to connect to github.com port 443: Could not connect to server`。

**原因**：网络环境限制（防火墙/代理）。

**方案**：切换网络或配置代理后再推送。

### GitHub 远程与本地历史冲突

**症状**：`git push` 被拒绝，`git pull` 产生大量冲突。

**原因**：本地 repo 和远程 GitHub 的 commit 历史分叉。

**方案**：
1. 先用 `git fetch origin` 查看远程差异
2. 如确定本地版本为最新，用 `git push --force-with-lease`
3. 如要合并，用 `git pull -X ours` 保留本地版本

### InfluxDB 数据被覆盖

**症状**：大盘 PE 数据变少（只有 1999-2010）。

**原因**：Docker 容器重建时挂载了旧的数据卷，或者 volume 路径不对。

**修复**：备份完整数据到安全位置（`/var/www/stock/data/sse_pe_data.db`），容器改用新的 volume 路径。

## 数据

### 大盘 PE 正常但个股查不到

**症状**：大盘 PE 图表有数据，但个股搜索/K线无数据。

**原因**：大盘数据来自 SSE 官网（已存储在 InfluxDB），个股数据来自腾讯 API/akshare（实时查询，非持久化）。两者数据源不同。

**当前状态**：个股数据尚未持久化到 InfluxDB，属于过渡状态。
