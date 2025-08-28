from playwright.sync_api import sync_playwright
import re

BASE_URL = "https://api-test.qiwi.com/partner"
AGENT_ID = "fake_agent_id"
POINT_ID = "fake_point_id"
BEARER_TOKEN = "fake_bearer_token"
PAYOUT_ID = "generated_payout_id"

date_regex = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{3})?Z?$")
numeric_regex = re.compile(r"^\d+(\.\d{1,2})?$")


def check_basic_response(response):
    assert response.status == 200, f"Status code is {response.status}"
    assert "application/json" in response.headers.get("content-type", "")
    try:
        return response.json()
    except Exception:
        raise AssertionError("Response is not valid JSON")


def test_get_all_payments():
    url = f"{BASE_URL}/v1/agents/{AGENT_ID}/points/{POINT_ID}/payments"
    with sync_playwright() as p:
        request = p.request.new_context(
            extra_http_headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {BEARER_TOKEN}",
            }
        )
        response = request.get(url)
        data = check_basic_response(response)
        assert isinstance(data, list)
        for idx, payment in enumerate(data):
            for field in [
                "paymentId",
                "creationDateTime",
                "expirationDatetime",
                "status",
                "recipientDetails",
                "amount",
            ]:
                assert field in payment
            assert (
                isinstance(payment["paymentId"], str) and len(payment["paymentId"]) > 0
            )
            assert date_regex.match(payment["creationDateTime"])
            assert date_regex.match(payment["expirationDatetime"])
            assert isinstance(payment["status"], dict)
            assert isinstance(payment["recipientDetails"], dict)
            assert isinstance(payment["amount"], dict)
        request.dispose()


def test_request_balance():
    url = f"{BASE_URL}/v1/agents/{AGENT_ID}/points/{POINT_ID}/balance"
    with sync_playwright() as p:
        request = p.request.new_context(
            extra_http_headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {BEARER_TOKEN}",
            }
        )
        response = request.get(url)
        data = check_basic_response(response)
        for key in ["balance", "overdraft", "available"]:
            assert key in data
            obj = data[key]
            assert isinstance(obj, dict)
            assert "value" in obj and "currency" in obj
            assert isinstance(obj["value"], str)
            assert isinstance(obj["currency"], str)
            assert numeric_regex.match(obj["value"])
            assert float(obj["value"]) > 0
        request.dispose()


def test_create_payment():
    url = f"{BASE_URL}/v1/agents/{AGENT_ID}/points/{POINT_ID}/payments/{PAYOUT_ID}"
    payload = {
        "recipientDetails": {
            "providerCode": "qiwi-wallet",
            "fields": {"phone": "79123456789"},
        },
        "amount": {"value": "1.00", "currency": "RUB"},
    }
    with sync_playwright() as p:
        request = p.request.new_context(
            extra_http_headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {BEARER_TOKEN}",
            }
        )
        response = request.put(url, data=payload)
        data = check_basic_response(response)

        for field in [
            "paymentId",
            "creationDateTime",
            "expirationDatetime",
            "status",
            "recipientDetails",
            "amount",
        ]:
            assert field in data

        assert data["paymentId"] == PAYOUT_ID
        assert date_regex.match(data["creationDateTime"])
        assert date_regex.match(data["expirationDatetime"])

        status = data["status"]
        assert isinstance(status, dict)
        assert "value" in status and "changedDateTime" in status
        assert status["value"] == "CREATED"
        assert date_regex.match(status["changedDateTime"])

        recipient = data["recipientDetails"]
        assert isinstance(recipient, dict)
        assert "providerCode" in recipient and "fields" in recipient
        assert isinstance(recipient["providerCode"], str)
        assert isinstance(recipient["fields"], dict)

        amount = data["amount"]
        assert isinstance(amount, dict)
        assert "value" in amount and "currency" in amount
        assert isinstance(amount["value"], str)
        assert isinstance(amount["currency"], str)
        assert len(amount["currency"]) == 3
        assert numeric_regex.match(amount["value"])
        assert float(amount["value"]) > 0

        request.dispose()


def test_execute_payment():
    url = f"{BASE_URL}/v1/agents/{AGENT_ID}/points/{POINT_ID}/payments/{PAYOUT_ID}/execute"
    with sync_playwright() as p:
        request = p.request.new_context(
            extra_http_headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {BEARER_TOKEN}",
            }
        )
        response = request.post(url)
        data = check_basic_response(response)

        for field in [
            "paymentId",
            "creationDateTime",
            "expirationDatetime",
            "status",
            "recipientDetails",
            "amount",
        ]:
            assert field in data

        assert data["paymentId"] == PAYOUT_ID
        assert date_regex.match(data["creationDateTime"])
        assert date_regex.match(data["expirationDatetime"])

        status = data["status"]
        assert isinstance(status, dict)
        assert "value" in status and "changedDateTime" in status
        assert status["value"] in ["IN_PROGRESS", "COMPLETED"]
        assert date_regex.match(status["changedDateTime"])

        recipient = data["recipientDetails"]
        assert isinstance(recipient, dict)
        assert "providerCode" in recipient and "fields" in recipient
        assert isinstance(recipient["providerCode"], str)
        assert isinstance(recipient["fields"], dict)

        amount = data["amount"]
        assert isinstance(amount, dict)
        assert "value" in amount and "currency" in amount
        assert isinstance(amount["value"], str)
        assert isinstance(amount["currency"], str)
        assert len(amount["currency"]) == 3
        assert numeric_regex.match(amount["value"])
        assert float(amount["value"]) > 0

        request.dispose()
