"""账单分摊 API：按权重把总额（整数分）拆成整数份数。"""

from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

app = FastAPI(title="Bill Split API", version="1.0.0")


class SplitRequest(BaseModel):
    total: int = Field(..., ge=0, description="账单总额，单位：分，非负整数")
    weights: List[int] = Field(..., description="各方权重，非负整数数组")

    @field_validator("weights")
    @classmethod
    def validate_weights(cls, v: List[int]) -> List[int]:
        if not v:
            raise ValueError("weights 不能为空数组")
        if any(w < 0 for w in v):
            raise ValueError("weights 必须全部为非负整数")
        return v


class SplitResponse(BaseModel):
    shares: List[int]


def split_total(total: int, weights: List[int]) -> List[int]:
    """按权重分摊总额。

    1. 每份先取 total * w / W 的整数部分；
    2. 未分完的“分”按小数部分从大到小依次补 1；
    3. 小数部分相同时，权重更大者优先；权重也相同时，索引靠前者优先。
    """
    weight_sum = sum(weights)
    if weight_sum == 0:
        raise ValueError("权重之和不能为 0")

    shares = [total * w // weight_sum for w in weights]
    # 小数部分以 (total * w) % weight_sum 表示（分母统一为 weight_sum）
    remainders = [total * w - shares[i] * weight_sum for i, w in enumerate(weights)]
    leftover = total - sum(shares)

    order = sorted(
        range(len(weights)),
        key=lambda i: (-remainders[i], -weights[i], i),
    )
    for i in order[:leftover]:
        shares[i] += 1
    return shares


@app.post("/split", response_model=SplitResponse)
def split(req: SplitRequest) -> SplitResponse:
    if sum(req.weights) == 0:
        raise HTTPException(status_code=422, detail="权重不能全部为 0")
    return SplitResponse(shares=split_total(req.total, req.weights))


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
