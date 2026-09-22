"""split_amount 单元测试 + /split 接口测试。"""

import random

import pytest
from fastapi.testclient import TestClient

from main import app, split_amount

client = TestClient(app)


# ---------- 分摊算法 ----------

def test_exact_division():
    assert split_amount(100, [1, 1, 1, 1]) == [25, 25, 25, 25]


def test_remainder_distributed_by_fractional_part():
    # 100/3 = 33.33...，余数相同，索引靠前者优先补一
    assert split_amount(100, [1, 1, 1]) == [34, 33, 33]


def test_fractional_part_descending():
    # total=5, weights=[3,1,1]: 精确份额 3.0 / 1.0 / 1.0 -> [3,1,1]
    assert split_amount(5, [3, 1, 1]) == [3, 1, 1]
    # total=7, weights=[3,1,1]: 4.2 / 1.4 / 1.4 -> 余数 0.2/0.4/0.4 -> [4,2,1]
    assert split_amount(7, [3, 1, 1]) == [4, 2, 1]


def test_tie_on_fraction_prefers_larger_weight():
    # total=5, weights=[2,1,1]: 2.5 / 1.25 / 1.25 -> 余数相同(0.25)，权重 1=1，索引靠前者优先
    assert split_amount(5, [2, 1, 1]) == [3, 1, 1]
    # total=2, weights=[1,3]: 0.5 / 1.5 -> 小数部分都是 0.5，权重大者(3)优先补一
    assert split_amount(2, [1, 3]) == [0, 2]
    # total=5, weights=[1,3]: 1.25 / 3.75 -> [1,4]
    assert split_amount(5, [1, 3]) == [1, 4]
    # total=7, weights=[3,6,1]: 2.1 / 4.2 / 0.7 -> 余数 0.1/0.2/0.7 -> [2,4,1]
    assert split_amount(7, [3, 6, 1]) == [2, 4, 1]


def test_tie_on_fraction_and_weight_prefers_earlier_index():
    # total=1, weights=[1,1]: 0.5 / 0.5，余数、权重都相同，索引 0 优先
    assert split_amount(1, [1, 1]) == [1, 0]


def test_zero_weight_gets_nothing():
    assert split_amount(10, [0, 1, 0, 1]) == [0, 5, 0, 5]
    # 余下 1 分也不会落到权重 0 的项上
    assert split_amount(11, [0, 1, 0, 1]) == [0, 6, 0, 5]


def test_zero_total():
    assert split_amount(0, [1, 2, 3]) == [0, 0, 0]


def test_single_weight():
    assert split_amount(999, [7]) == [999]


def test_sum_invariant_fuzz():
    rng = random.Random(42)
    for _ in range(2000):
        n = rng.randint(1, 20)
        weights = [rng.randint(0, 100) for _ in range(n)]
        if all(w == 0 for w in weights):
            continue
        total = rng.randint(0, 10**9)
        shares = split_amount(total, weights)
        assert len(shares) == n
        assert sum(shares) == total
        assert all(s >= 0 for s in shares)
        for w, s in zip(weights, shares):
            if w == 0:
                assert s == 0


# ---------- HTTP 接口 ----------

def test_api_ok():
    r = client.post("/split", json={"total": 100, "weights": [1, 1, 1]})
    assert r.status_code == 200
    body = r.json()
    assert body["shares"] == [34, 33, 33]
    assert sum(body["shares"]) == body["total"] == 100


def test_api_negative_total_422():
    r = client.post("/split", json={"total": -1, "weights": [1]})
    assert r.status_code == 422


def test_api_empty_weights_422():
    r = client.post("/split", json={"total": 100, "weights": []})
    assert r.status_code == 422


def test_api_all_zero_weights_422():
    r = client.post("/split", json={"total": 100, "weights": [0, 0, 0]})
    assert r.status_code == 422


def test_api_negative_weight_422():
    r = client.post("/split", json={"total": 100, "weights": [1, -2]})
    assert r.status_code == 422


def test_api_zero_total_ok():
    r = client.post("/split", json={"total": 0, "weights": [3, 1]})
    assert r.status_code == 200
    assert r.json()["shares"] == [0, 0]
