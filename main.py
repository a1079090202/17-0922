"""账单分摊 API：按权重把总额（整数分）拆成整数数组。"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, NonNegativeInt

app = FastAPI(title="Bill Split API", version="1.0.0")


class SplitRequest(BaseModel):
    """分摊请求。

    - total: 总金额，单位分，非负整数（负数由校验层返回 422）
    - weights: 权重数组，非空，元素均为非负整数
    """

    total: NonNegativeInt = Field(..., description="总金额（分）")
    weights: list[NonNegativeInt] = Field(..., min_length=1, description="权重数组")


class SplitResponse(BaseModel):
    shares: list[int]
    total: int


def split_amount(total: int, weights: list[int]) -> list[int]:
    """按权重分摊总额（最大余数法），返回与 weights 等长的整数数组。

    1. 每项先取 floor(total * w / sum_w)；
    2. 剩余的分按小数部分（余数）从大到小依次补一；
       余数相同则权重大者优先，权重再相同则索引靠前者优先。

    全程整数运算，无浮点误差；结果之和恒等于 total。
    """
    weight_sum = sum(weights)
    floors = [(total * w) // weight_sum for w in weights]
    remainders = [(total * w) % weight_sum for w in weights]
    remaining = total - sum(floors)

    # 排序键：余数降序 -> 权重降序 -> 索引升序
    order = sorted(range(len(weights)), key=lambda i: (-remainders[i], -weights[i], i))

    shares = list(floors)
    for i in order[:remaining]:
        shares[i] += 1
    return shares


@app.post("/split", response_model=SplitResponse)
def split(req: SplitRequest) -> SplitResponse:
    if sum(req.weights) == 0:
        raise HTTPException(status_code=422, detail="权重之和必须大于 0")
    shares = split_amount(req.total, req.weights)
    return SplitResponse(shares=shares, total=req.total)
