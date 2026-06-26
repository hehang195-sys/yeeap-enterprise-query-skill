"""
企业信息查询 Skill - Phase 1：创建订单。

调用企业查询业务后端 /api/mock-payee/create_order，获取 orderNo / amount / encrypted_data / skill_id，
并将订单元数据写入 ~/.yeeap/orders/<app_id>/<order_no>.json，供后续 yeeap-wallet 与 service.py 使用。
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

from file_utils import save_order

# 默认指向公网生产 yeeap 服务，本地联调可通过环境变量覆盖
DEFAULT_BASE_URL = "https://ap.yeepay.com/yeeap"
CREATE_ORDER_URL = os.environ.get("YEEAP_DEMO_BASE_URL", DEFAULT_BASE_URL).rstrip("/") + \
    "/api/mock-payee/create_order"


def create_order(question: str) -> tuple:
    pay_data = {"reqData": {"question": question}}
    payload = json.dumps(pay_data).encode("utf-8")
    req = urllib.request.Request(
        CREATE_ORDER_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            envelope = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        raise RuntimeError(f"网络请求异常，请确认 yeeap 服务已在 {CREATE_ORDER_URL} 上运行: {e}") from e

    body = envelope.get("resultData") if isinstance(envelope, dict) else None
    if body is None:
        raise RuntimeError(f"响应格式异常，无法解析 resultData：{envelope}")

    if body.get("responseCode") != "200":
        raise RuntimeError(
            f"Order creation failed: {body.get('responseMessage', 'unknown error')}"
        )

    order_no = body.get("orderNo")
    amount = body.get("amount")
    encrypted_data = body.get("encryptedData")
    app_id = body.get("appId")
    skill_id = body.get("skillId")
    response_pay_env = body.get("payEnv") or "PRODUCTION"

    missing = [k for k, v in (
        ("orderNo", order_no),
        ("amount", amount),
        ("encryptedData", encrypted_data),
        ("appId", app_id),
        ("skillId", skill_id),
    ) if not v]
    if missing:
        raise RuntimeError(f"订单创建响应缺少字段: {', '.join(missing)}")

    return order_no, amount, encrypted_data, app_id, skill_id, response_pay_env


def save_order_info(order_no, amount, question, encrypted_data, app_id, skill_id, pay_env):
    order_data = {
        "order_no": order_no,
        "amount": amount,
        "question": question,
        "encrypted_data": encrypted_data,
        "app_id": app_id,
        "skill_id": skill_id,
        "pay_env": pay_env,
    }
    return save_order(app_id, order_no, order_data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create enterprise-query order")
    parser.add_argument("question", help="企业关键词，如：阿里巴巴 / 腾讯 / 易宝")
    args = parser.parse_args()

    try:
        order_no, amount, encrypted_data, app_id, skill_id, pay_env = create_order(args.question)
    except RuntimeError as e:
        print(f"订单创建失败: {e}")
        sys.exit(1)

    save_order_info(order_no, amount, args.question, encrypted_data, app_id, skill_id, pay_env)

    print(f"ORDER_NO={order_no}")
    print(f"AMOUNT={amount}")
    print(f"QUESTION={args.question}")
    print(f"APP_ID={app_id}")
    print(f"SKILL_ID={skill_id}")
    print(f"PAY_ENV={pay_env}")
