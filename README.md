# 账单分摊 API (Bill Split API)

基于 FastAPI 的服务：给定账单总额（整数分）与各方权重，返回一组整数分摊结果，
其和**恒等于总额**。

## 分摊规则

1. 每份先取 `总额 × 权重 / 权重和` 的整数部分；
2. 未分完的“分”按小数部分从大到小依次补 1；
3. 小数部分相同时，权重更大者优先；权重也相同时，索引靠前者优先。

## 安装

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## 启动（单条命令）

服务监听 **8000 端口**：

```bash
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 接口

### POST /split

请求体：

| 字段      | 类型        | 说明                       |
|-----------|-------------|----------------------------|
| `total`   | int         | 总额（单位：分），非负整数 |
| `weights` | array[int]  | 非负整数权重，不可为空     |

示例：

```bash
curl -s -X POST http://localhost:8000/split \
  -H 'Content-Type: application/json' \
  -d '{"total": 100, "weights": [1, 1, 1]}'
# {"shares":[34,33,33]}

curl -s -X POST http://localhost:8000/split \
  -H 'Content-Type: application/json' \
  -d '{"total": 10, "weights": [3, 3, 3, 1]}'
# {"shares":[3,3,3,1]}
```

### 错误（均返回 HTTP 422）

- 总额为负数；
- 权重数组为空；
- 权重中含负数；
- 权重全部为 0。

### GET /health

健康检查，返回 `{"status":"ok"}`。
