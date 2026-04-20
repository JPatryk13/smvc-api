"""HTTP acceptance tests. Docstrings quote criteria from tests/acceptance/REQUIREMENTS.md."""

from starlette.testclient import TestClient

from smvc_api.auth import bearer_token_for_admin, bearer_token_for_user


def test_u3_user_transfer_returns_202_with_transfer_id(client: TestClient) -> None:
    """**U3** — The transfer endpoint returns **202** and the work continues **without** the user babysitting the request."""

    # Given a normal user token with a linked Instagram account.
    token = bearer_token_for_user(sub="alice", instagram_user_id="ig-alice")

    # When they start a transfer.
    r = client.post("/v1/transfers", headers={"Authorization": token})

    # Then the API accepts the job immediately with 202 and a transfer_id.
    assert r.status_code == 202
    body = r.json()
    assert "transfer_id" in body
    assert body["transfer_id"].startswith("t-")


def test_u1_user_cannot_request_other_instagram_account(client: TestClient) -> None:
    """**U1** — Only the **owner** of the linked Instagram identity may start that user's transfer; otherwise **403** (don't leak whether another account exists — pick **403** consistently)."""

    # Given user alice is authenticated for Instagram ig-alice.
    token = bearer_token_for_user(sub="alice", instagram_user_id="ig-alice")

    # When the request body asks to transfer for ig-bob instead.
    r = client.post(
        "/v1/transfers",
        headers={"Authorization": token},
        json={"instagram_user_id": "ig-bob"},
    )

    # Then the server refuses with 403.
    assert r.status_code == 403


def test_u2_instagram_not_linked_remediation(client: TestClient) -> None:
    """**U2** — If Instagram isn't connected or tokens are unusable, return a **clear error** plus a **next step** (e.g. "complete Instagram connection", link or doc id) — not a generic 500."""

    import base64
    import json

    # Given a user token with no instagram_user_id (Instagram not linked).
    payload = {"role": "user", "sub": "nomail"}
    raw = json.dumps(payload, separators=(",", ":")).encode()
    token = "Bearer " + base64.urlsafe_b64encode(raw).decode().rstrip("=")

    # When they attempt to start a transfer.
    r = client.post("/v1/transfers", headers={"Authorization": token})

    # Then the response is 400 with a structured detail including remediation.
    assert r.status_code == 400
    err = r.json()
    assert "detail" in err
    detail = err["detail"]
    assert isinstance(detail, dict)
    assert detail.get("code") == "instagram_not_linked"
    assert "remediation" in detail


def test_a1_admin_endpoint_rejects_non_admin(client: TestClient) -> None:
    """**A1** — Admin-only routes require provable **admin** credentials; everyone else gets **403**."""

    # Given a normal user token (not an admin).
    token = bearer_token_for_user(sub="alice", instagram_user_id="ig-alice")

    # When they call the admin transfer endpoint.
    r = client.post(
        "/v1/admin/transfers",
        headers={"Authorization": token},
        json={
            "source_instagram_user_id": "src",
            "target_miletribe_user_id": "mt-1",
        },
    )

    # Then access is denied with 403.
    assert r.status_code == 403


def test_admin_happy_path_202(client: TestClient) -> None:
    """**A2** — Request identifies **source Instagram** and **`target_miletribe_user_id`** explicitly.

    **O1** — Every run exposes a **`transfer_id`** and a status view with **counts** (discovered → scenery-selected → uploaded → failed) and **errors** per item when useful.
    """

    # Given an admin token.
    token = bearer_token_for_admin(sub="root")

    # When they POST an admin transfer with explicit source and target.
    r = client.post(
        "/v1/admin/transfers",
        headers={"Authorization": token},
        json={
            "source_instagram_user_id": "ig-any",
            "target_miletribe_user_id": "mt-target",
        },
    )

    # Then the job is accepted with 202 and a transfer_id.
    assert r.status_code == 202
    tid = r.json()["transfer_id"]

    # When the same caller fetches status for that transfer_id.
    st = client.get(f"/v1/transfers/{tid}", headers={"Authorization": token})

    # Then the status payload includes the same transfer_id (traceability).
    assert st.status_code == 200
    assert st.json()["transfer_id"] == tid


def test_a3_admin_audit_record(client: TestClient) -> None:
    """**A3** — Persist an **audit record**: admin identity, source, target, timestamp, and high-level outcome (counts / errors)."""

    from smvc_api.app import app

    # Given an admin token used for an audited subject.
    token = bearer_token_for_admin(sub="audit-admin")

    # When they create an admin transfer with known source and destination.
    client.post(
        "/v1/admin/transfers",
        headers={"Authorization": token},
        json={
            "source_instagram_user_id": "ig-src",
            "target_miletribe_user_id": "mt-dst",
        },
    )

    # Then the audit log contains a matching entry with who, source, and target.
    audit = app.state.audit_log
    entries = audit.entries()
    assert entries
    last = entries[-1]
    assert last["admin_subject"] == "audit-admin"
    assert last["source_instagram_user_id"] == "ig-src"
    assert last["target_miletribe_user_id"] == "mt-dst"
