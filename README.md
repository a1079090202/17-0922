# Bill Split API（账单分摊）

基于 FastAPI 的账单分摊服务：把总额（整数，单位分）按权重拆成整数数组，保证各项之和恒等于总额。

## 分摊规则（最大余数法）

1. 每项先按权重占比取整数部分：`floor(total * w_i / sum(weights))`；
2. 剩余的分按**小数部分从大到小**依次补一；
3. 小数部分相同时，**权重更大者**优先；权重再相同时，**索引靠前者**优先。

全程整数运算，无浮点误差。权重为 0 的项始终分得 0。

## 启动

```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

服务监听 **8000** 端口，交互式文档：<http://localhost:8000/docs>

## 接口

### POST /split

请求体：

```json
{
  "total": 100,
  "weights": [1, 1, 1]
}
```

- `total`：总金额（分），非负整数
- `weights`：权重数组，非空，元素为非负整数，且至少一项大于 0

响应 `200`：

```json
{
  "shares": [34, 33, 33],
  "total": 100
}
```

`shares` 与 `weights` 等长，且 `sum(shares) == total`。

### 错误（422）

以下情况返回 `422 Unprocessable Entity`：

- `total` 为负数
- `weights` 为空数组
- `weights` 全为 0（权重之和为 0）
- `weights` 含负数或字段类型非法

## 示例

```bash
curl -X POST http://localhost:8000/split \
  -H 'Content-Type: application/json' \
  -d '{"total": 100, "weights": [1, 1, 1]}'
# {"shares":[34,33,33],"total":100}
```

## 测试

```bash
pip install pytest httpx
pytest -v
```
