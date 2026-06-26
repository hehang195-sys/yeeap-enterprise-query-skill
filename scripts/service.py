"""
企业信息查询 Skill - Phase 3：执行查询。

凭借 yeeap-wallet 写回订单文件的 payCredential，调用企业查询业务后端 /api/mock-payee/service，
返回结构化的企业工商信息。
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

from file_utils import load_order

# 默认指向公网生产 yeeap 服务，本地联调可通过环境变量覆盖
DEFAULT_BASE_URL = "https://ap.yeepay.com/yeeap"
GET_RESULT_URL = os.environ.get("YEEAP_DEMO_BASE_URL", DEFAULT_BASE_URL).rstrip("/") + \
    "/api/mock-payee/service"


def find_order_app_id(order_no: str) -> str:
    home_dir = os.path.expanduser("~")
    orders_root = os.path.join(home_dir, ".yeeap", "orders")
    if not os.path.isdir(orders_root):
        raise RuntimeError(f"订单根目录不存在: {orders_root}")
    for candidate in os.listdir(orders_root):
        order_path = os.path.join(orders_root, candidate, f"{order_no}.json")
        if os.path.isfile(order_path):
            return candidate
    raise RuntimeError(f"未找到订单 {order_no}，请先执行 Phase 1 创建订单")


def query_enterprise(question: str, order_no: str, credential: str) -> str:
    payload = json.dumps({
        "question": question,
        "orderNo": order_no,
        "credential": credential,
    }).encode("utf-8")
    req = urllib.request.Request(
        GET_RESULT_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            envelope = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        raise RuntimeError(f"查询请求失败：{e}") from e

    body = envelope.get("resultData") if isinstance(envelope, dict) else None
    if body is None:
        raise RuntimeError(f"响应格式异常: {envelope}")

    if body.get("responseCode") != "200":
        raise RuntimeError(
            f"Enterprise lookup failed: {body.get('responseMessage', 'unknown error')}"
        )

    pay_status = body.get("payStatus", "UNKNOWN")
    print(f"PAY_STATUS: {pay_status}")

    if pay_status == "ERROR":
        raise RuntimeError(body.get("errorInfo", "未知错误"))

    answer = body.get("answer")
    if not answer:
        raise RuntimeError("查询响应缺少 answer 字段")
    return answer


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query enterprise info")
    parser.add_argument("order_no", help="Phase 1 生成的订单号")
    args = parser.parse_args()

    try:
        app_id = find_order_app_id(args.order_no)
        order_data = load_order(app_id, args.order_no)

        question = order_data.get("question")
        if not question:
            raise RuntimeError("订单文件中缺少 question 字段")
        credential = order_data.get("payCredential")
        if not credential:
            raise RuntimeError("订单文件中缺少 payCredential 字段，请先完成 Phase 2 支付")

        answer = query_enterprise(question, args.order_no, credential)
        print(answer)
    except Exception as e:
        print("PAY_STATUS: ERROR")
        print(f"ERROR_INFO: {e}")
        sys.exit(1)
