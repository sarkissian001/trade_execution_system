from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from trading_execution_system.main import app

client = TestClient(app)

TODAY = datetime.now().date()
TODAY_ISO = TODAY.isoformat()
TOMORROW_ISO = (TODAY + timedelta(days=1)).isoformat()
DAY_AFTER_TOMORROW_ISO = (TODAY + timedelta(days=2)).isoformat()


def create_sample_trade_payload(requester_id="User1"):
    return {
        "requester_id": requester_id,
        "details": {
            "trading_entity": "EntityA",
            "counterparty": "EntityB",
            "direction": "Buy",
            "style": "Forward",
            "currency": "GBP",
            "notional_amount": 1000000,
            "underlying": ["GBP", "USD"],
            "trade_date": TODAY_ISO,
            "value_date": TOMORROW_ISO,
            "delivery_date": DAY_AFTER_TOMORROW_ISO,
            "strike": 0,
        },
    }


def test_submit_and_approve_trade():
    response = client.post(
        "/api/v1/trades/",
        json=create_sample_trade_payload(),
        headers={"x-user-id": "User1"},
    )
    assert response.status_code == 200, f"Error: {response.json()}"
    data = response.json()
    trade_id = data["id"]
    assert data["state"] == "PENDING_APPROVAL"

    response = client.post(
        f"/api/v1/trades/{trade_id}/approve", headers={"x-user-id": "admin"}
    )
    assert response.status_code == 200, f"Error: {response.json()}"
    data = response.json()
    assert data["state"] == "APPROVED"


def test_update_trade_and_reapprove():
    requester_headers = {"X-User-Id": "User1"}
    response = client.post(
        "/api/v1/trades/", json=create_sample_trade_payload(), headers=requester_headers
    )
    assert response.status_code == 200
    data = response.json()
    trade_id = data["id"]
    assert data["state"] == "PENDING_APPROVAL"

    details_payload = create_sample_trade_payload()["details"]
    details_payload["notional_amount"] = 123

    update_payload = {"user_id": "User1", "details": details_payload}

    response = client.post(
        f"/api/v1/trades/{trade_id}/update",
        json=update_payload,
        headers=requester_headers,
    )
    assert response.status_code == 200
    updated_trade = response.json()

    assert updated_trade["details"]["notional_amount"] == 123
    assert data["state"] == "PENDING_APPROVAL"


def test_trade_cancellation_permissions():
    headers = {"x-user-id": "User1"}
    response = client.post(
        "/api/v1/trades/", json=create_sample_trade_payload(), headers=headers
    )
    assert response.status_code == 200
    trade_id = response.json()["id"]

    response = client.post(f"/api/v1/trades/{trade_id}/cancel", headers=headers)
    assert response.status_code == 200
    assert response.json()["state"] == "CANCELLED"

    headers = {"x-user-id": "admin"}
    response = client.post(f"/api/v1/trades/{trade_id}/cancel", headers=headers)
    assert response.status_code in (400, 422), f"Error: {response.json()}"


def test_unauthorised_approval():
    headers = {"x-user-id": "User1"}
    response = client.post(
        "/api/v1/trades/", json=create_sample_trade_payload(), headers=headers
    )
    assert response.status_code == 200
    trade_id = response.json()["id"]

    response = client.post(f"/api/v1/trades/{trade_id}/approve", headers=headers)
    assert (
        response.status_code == 403
    ), f"Expected unauthorised error, got: {response.json()}"
    assert (
        "only approvers can perform this action."
        in response.json().get("detail", "").lower()
    )


def test_invalid_trade_date_ordering():
    payload = create_sample_trade_payload()
    payload["details"]["trade_date"] = DAY_AFTER_TOMORROW_ISO
    payload["details"]["value_date"] = TODAY_ISO

    headers = {"x-user-id": "User1"}
    response = client.post("/api/v1/trades/", json=payload, headers=headers)
    assert response.status_code in (
        400,
        422,
    ), f"Expected validation error, got: {response.json()}"


def test_view_trade_history():
    headers = {"x-user-id": "User1"}
    response = client.post(
        "/api/v1/trades/", json=create_sample_trade_payload(), headers=headers
    )
    assert response.status_code == 200
    trade_id = response.json()["id"]

    headers = {"x-user-id": "admin"}
    response = client.get(f"/api/v1/trades/{trade_id}/history", headers=headers)
    assert response.status_code == 200
    assert len(response.json()["history"]) >= 1


def test_cancel_trade_after_approval_should_be_possible():
    headers = {"x-user-id": "User1"}
    response = client.post(
        "/api/v1/trades/", json=create_sample_trade_payload(), headers=headers
    )
    assert response.status_code == 200
    trade_id = response.json()["id"]

    headers = {"x-user-id": "admin"}
    response = client.post(f"/api/v1/trades/{trade_id}/approve", headers=headers)
    assert response.status_code == 200
    assert response.json()["state"] == "APPROVED"

    # cancel trade after approval as requester (User1) – allowed.
    headers = {"x-user-id": "User1"}
    response = client.post(f"/api/v1/trades/{trade_id}/cancel", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["state"] == "CANCELLED"


def test_only_admin_can_send_to_execute():
    requester_headers = {"x-user-id": "User1"}
    create_response = client.post(
        "/api/v1/trades/", json=create_sample_trade_payload(), headers=requester_headers
    )
    assert (
        create_response.status_code == 200
    ), f"Error creating trade: {create_response.json()}"
    trade_id = create_response.json()["id"]

    response = client.post(
        f"/api/v1/trades/{trade_id}/approve", headers={"x-user-id": "admin"}
    )
    assert response.status_code == 200
    assert response.json()["state"] == "APPROVED"

    non_admin_response = client.post(
        f"/api/v1/trades/{trade_id}/send_to_execute", headers=requester_headers
    )
    assert (
        non_admin_response.status_code == 403
    ), f"Expected 403 for non-admin, got {non_admin_response.status_code}: {non_admin_response.json()}"
    expected_error = "Only approvers can perform this action."
    assert (
        non_admin_response.json().get("detail", "") == expected_error
    ), f"Expected error message to be '{expected_error}', got: {non_admin_response.json().get('detail', '')}"

    admin_response = client.post(
        f"/api/v1/trades/{trade_id}/send_to_execute", headers={"x-user-id": "admin"}
    )
    assert (
        admin_response.status_code == 200
    ), f"Error sending trade to execute: {admin_response.json()}"

    assert admin_response.json()["state"] == "SENT_TO_COUNTERPARTY"


def test_booking_trade_requires_send_to_execute_and_requester_or_approver():
    # Submit request

    requester_headers = {"x-user-id": "User1"}
    create_response = client.post(
        "/api/v1/trades/", json=create_sample_trade_payload(), headers=requester_headers
    )
    assert (
        create_response.status_code == 200
    ), f"Error creating trade: {create_response.json()}"
    trade_id = create_response.json()["id"]

    # approve by admin
    approve_response = client.post(
        f"/api/v1/trades/{trade_id}/approve", headers={"x-user-id": "admin"}
    )
    assert (
        approve_response.status_code == 200
    ), f"Error approving trade: {approve_response.json()}"
    assert approve_response.json()["state"] == "APPROVED"

    # send the trade to execute as admin.
    send_to_execute_response = client.post(
        f"/api/v1/trades/{trade_id}/send_to_execute", headers={"x-user-id": "admin"}
    )
    assert send_to_execute_response.status_code == 200
    assert send_to_execute_response.json()["state"] == "SENT_TO_COUNTERPARTY"

    # try to book the trade using an unauthorised user.
    # User2 is not authorised to do anything
    unauthorised_headers = {"x-user-id": "User2"}
    book_payload = {"strike": 100}  # Example payload; adjust as needed.
    unauthorised_book_response = client.post(
        f"/api/v1/trades/{trade_id}/book",
        json=book_payload,
        headers=unauthorised_headers,
    )

    assert unauthorised_book_response.status_code == 403, (
        f"Expected 403 for unauthorised booking, got {unauthorised_book_response.status_code}: "
        f"{unauthorised_book_response.json()}"
    )
    expected_error = "Only requesters or approvers can perform this action."
    assert (
        unauthorised_book_response.json().get("detail", "") == expected_error
    ), f"Expected error message '{expected_error}', got: {unauthorised_book_response.json().get('detail', '')}"

    # book the trade using an authorised user.
    authorized_book_response = client.post(
        f"/api/v1/trades/{trade_id}/book", json=book_payload, headers=requester_headers
    )
    assert authorized_book_response.status_code == 200

    assert authorized_book_response.json()["state"] == "EXECUTED"


def test_get_trade_history_authorised():
    requester_headers = {"x-user-id": "User1"}
    create_response = client.post(
        "/api/v1/trades/", json=create_sample_trade_payload(), headers=requester_headers
    )
    assert create_response.status_code == 200
    trade_id = create_response.json()["id"]

    admin_headers = {"x-user-id": "admin"}
    approve_response = client.post(
        f"/api/v1/trades/{trade_id}/approve", headers=admin_headers
    )
    assert (
        approve_response.status_code == 200
    ), f"Error approving trade: {approve_response.json()}"

    history_response = client.get(
        f"/api/v1/trades/{trade_id}/history", headers=requester_headers
    )
    assert history_response.status_code == 200
    history_data = history_response.json()

    assert (
        "history" in history_data
    ), f"Response does not contain 'history': {history_data}"
    assert isinstance(
        history_data["history"], list
    ), f"Expected 'history' to be a list, got {type(history_data['history'])}"


def test_get_trade_history_unauthorised():
    requester_headers = {"x-user-id": "User1"}
    create_response = client.post(
        "/api/v1/trades/", json=create_sample_trade_payload(), headers=requester_headers
    )
    assert create_response.status_code == 200
    trade_id = create_response.json()["id"]

    unauthorised_headers = {"x-user-id": "User2"}
    history_response = client.get(
        f"/api/v1/trades/{trade_id}/history", headers=unauthorised_headers
    )
    assert (
        history_response.status_code == 403
    ), f"Expected 403 for unauthorised access, got {history_response.status_code}: {history_response.json()}"
    expected_error = "Only requesters or approvers can perform this action."
    assert (
        history_response.json().get("detail", "") == expected_error
    ), f"Expected error message '{expected_error}', got: {history_response.json().get('detail', '')}"


def test_get_trade_diff_authorized_valid():
    requester_headers = {"x-user-id": "User1"}
    create_response = client.post(
        "/api/v1/trades/", json=create_sample_trade_payload(), headers=requester_headers
    )
    assert (
        create_response.status_code == 200
    ), f"Error creating trade: {create_response.json()}"
    trade_id = create_response.json()["id"]

    update_payload = create_sample_trade_payload()
    update_payload["user_id"] = "User1"
    update_payload["details"]["notional_amount"] = 2000000
    update_response = client.post(
        f"/api/v1/trades/{trade_id}/update",
        json=update_payload,
        headers=requester_headers,
    )
    assert update_response.status_code == 200

    diff_response = client.get(
        f"/api/v1/trades/{trade_id}/diff?from_index=0&to_index=1",
        headers=requester_headers,
    )
    assert diff_response.status_code == 200
    diff_data = diff_response.json()

    assert (
        "differences" in diff_data
    ), f"'differences' key not found in response: {diff_data}"
    assert isinstance(
        diff_data["differences"], dict
    ), f"Expected 'differences' to be a dict, got {type(diff_data['differences'])}"


def test_get_trade_diff_invalid_indices():
    requester_headers = {"x-user-id": "User1"}
    create_response = client.post(
        "/api/v1/trades/", json=create_sample_trade_payload(), headers=requester_headers
    )
    assert create_response.status_code == 200
    trade_id = create_response.json()["id"]

    diff_response = client.get(
        f"/api/v1/trades/{trade_id}/diff?from_index=0&to_index=10",
        headers=requester_headers,
    )
    assert (
        diff_response.status_code == 400
    ), f"Expected 400 for invalid indices, got {diff_response.status_code}: {diff_response.json()}"

    error_detail = diff_response.json().get("detail", "").lower()
    expected_fragment = "invalid history indices"
    assert (
        expected_fragment in error_detail
    ), f"Expected error message to contain '{expected_fragment}', got: {error_detail}"


def test_get_trade_diff_unauthorised():
    requester_headers = {"x-user-id": "User1"}
    create_response = client.post(
        "/api/v1/trades/", json=create_sample_trade_payload(), headers=requester_headers
    )
    assert create_response.status_code == 200
    trade_id = create_response.json()["id"]

    unauthorised_headers = {"x-user-id": "User2"}
    diff_response = client.get(
        f"/api/v1/trades/{trade_id}/diff?from_index=0&to_index=0",
        headers=unauthorised_headers,
    )
    assert (
        diff_response.status_code == 403
    ), f"Expected 403 for unauthorised access, got {diff_response.status_code}: {diff_response.json()}"
    expected_error = "Only requesters or approvers can perform this action."
    assert (
        diff_response.json().get("detail", "") == expected_error
    ), f"Expected error message '{expected_error}', got: {diff_response.json().get('detail', '')}"


def test_get_trade_status_authorized():
    # Step 1: Create a trade as the requester (User1)
    requester_headers = {"x-user-id": "User1"}
    create_response = client.post(
        "/api/v1/trades/", json=create_sample_trade_payload(), headers=requester_headers
    )
    assert create_response.status_code == 200
    trade_id = create_response.json()["id"]

    # Step 2: Retrieve the trade status as the authorized user (the requester)
    status_response = client.get(
        f"/api/v1/trades/{trade_id}/status", headers=requester_headers
    )
    assert status_response.status_code == 200
    status_data = status_response.json()
    assert (
        "state" in status_data
    ), f"Expected 'state' key in response, got: {status_data}"


def test_get_trade_status_unauthorised():
    requester_headers = {"x-user-id": "User1"}
    create_response = client.post(
        "/api/v1/trades/", json=create_sample_trade_payload(), headers=requester_headers
    )
    assert create_response.status_code == 200
    trade_id = create_response.json()["id"]

    unauthorised_headers = {"x-user-id": "User2"}
    status_response = client.get(
        f"/api/v1/trades/{trade_id}/status", headers=unauthorised_headers
    )

    assert (
        status_response.status_code == 403
    ), f"Expected 403 for unauthorised access, got {status_response.status_code}: {status_response.json()}"
    expected_error = "Only requesters or approvers can perform this action."
    assert (
        status_response.json().get("detail", "") == expected_error
    ), f"Expected error message '{expected_error}', got: {status_response.json().get('detail', '')}"


def test_get_all_trades_as_requester():
    # Create a trade as User1.
    headers_user1 = {"x-user-id": "User1"}
    response1 = client.post(
        "/api/v1/trades/", json=create_sample_trade_payload(), headers=headers_user1
    )
    assert response1.status_code == 200, f"Error creating trade: {response1.json()}"
    trade1_id = response1.json()["id"]

    headers_user2 = {"x-user-id": "User2"}
    response2 = client.post(
        "/api/v1/trades/",
        json=create_sample_trade_payload(requester_id="User2"),
        headers=headers_user2,
    )
    assert response2.status_code == 200
    trade2_id = response2.json()["id"]

    response = client.get("/api/v1/trades/", headers=headers_user1)
    assert response.status_code == 200
    trades = response.json()

    trade_ids = [trade["id"] for trade in trades]
    assert trade1_id in trade_ids, "User1's trade not found in the results."
    assert trade2_id not in trade_ids, "User2's trade should not be visible to User1."
