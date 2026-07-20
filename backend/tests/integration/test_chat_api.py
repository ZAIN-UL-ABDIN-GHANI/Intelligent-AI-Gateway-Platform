def test_health_endpoint(client):
    resp = client.get("/v1/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_chat_completion_requires_auth(client):
    resp = client.post("/v1/chat/completions", json={"messages": [{"role": "user", "content": "hi"}]})
    assert resp.status_code == 401


def test_chat_completion_end_to_end(client, org_and_key):
    api_key = org_and_key["api_key"]
    resp = client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "Hello there, how are you?"}]},
        headers={"Authorization": f"Bearer {api_key}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["routed_model"] in {"gemma-local", "claude", "gpt", "gemini"}
    assert "trace_id" in body
    assert body["cache_hit"] is False


def test_second_identical_request_hits_cache(client, org_and_key):
    api_key = org_and_key["api_key"]
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {"messages": [{"role": "user", "content": "What is the capital of Japan?"}]}

    first = client.post("/v1/chat/completions", json=payload, headers=headers)
    second = client.post("/v1/chat/completions", json=payload, headers=headers)

    assert first.json()["cache_hit"] is False
    assert second.json()["cache_hit"] is True


def test_empty_messages_rejected(client, org_and_key):
    api_key = org_and_key["api_key"]
    resp = client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "   "}]},
        headers={"Authorization": f"Bearer {api_key}"},
    )
    assert resp.status_code == 422


def test_high_risk_prompt_routes_locally(client, org_and_key):
    api_key = org_and_key["api_key"]
    resp = client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "My SSN is 123-45-6789, please store it"}]},
        headers={"Authorization": f"Bearer {api_key}"},
    )
    assert resp.status_code == 200
    assert resp.json()["routed_model"] == "gemma-local"


def test_trace_retrieval(client, org_and_key):
    api_key = org_and_key["api_key"]
    headers = {"Authorization": f"Bearer {api_key}"}
    chat_resp = client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "Write me a poem about autumn"}]},
        headers=headers,
    )
    trace_id = chat_resp.json()["trace_id"]

    trace_resp = client.get(f"/v1/traces/{trace_id}", headers=headers)
    assert trace_resp.status_code == 200
    data = trace_resp.json()
    assert data["trace_id"] == trace_id
    assert "reason" in data
    assert "candidate_scores" in data


def test_feedback_submission(client, org_and_key):
    api_key = org_and_key["api_key"]
    headers = {"Authorization": f"Bearer {api_key}"}
    chat_resp = client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "Summarize this: the sky is blue"}]},
        headers=headers,
    )
    trace_id = chat_resp.json()["trace_id"]

    fb_resp = client.post(
        "/v1/feedback",
        json={"trace_id": trace_id, "rating": "up", "comment": "Great answer"},
        headers=headers,
    )
    assert fb_resp.status_code == 201


def test_analytics_cost_reflects_usage(client, org_and_key):
    api_key = org_and_key["api_key"]
    headers = {"Authorization": f"Bearer {api_key}"}
    client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "Write complex code ```def x(): pass``` step by step"}]},
        headers=headers,
    )
    resp = client.get("/v1/analytics/cost", headers=headers)
    assert resp.status_code == 200
    assert "total_cost" in resp.json()


def test_cross_org_trace_access_forbidden(client, org_and_key):
    # second org
    org2 = client.post("/v1/admin/organizations", json={"name": "Other Org"}).json()
    key2 = client.post(
        "/v1/admin/api-keys", json={"label": "k2"}, headers={"Authorization": f"Bearer {org2['admin_token']}"}
    ).json()["key"]

    headers1 = {"Authorization": f"Bearer {org_and_key['api_key']}"}
    chat_resp = client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "hello"}]},
        headers=headers1,
    )
    trace_id = chat_resp.json()["trace_id"]

    headers2 = {"Authorization": f"Bearer {key2}"}
    resp = client.get(f"/v1/traces/{trace_id}", headers=headers2)
    assert resp.status_code == 403
