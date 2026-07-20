from app.routing.policy import eligible_backends, score_candidates, budget_pressure


def test_high_risk_strict_policy_restricts_to_local():
    candidates = eligible_backends(
        intent="chat",
        risk_level="high",
        input_tokens=100,
        healthy_backends={"gemma-local", "claude", "gpt", "gemini"},
        privacy_policy="strict",
    )
    assert candidates == ["gemma-local"]


def test_no_risk_allows_all_intent_candidates():
    candidates = eligible_backends(
        intent="chat",
        risk_level="none",
        input_tokens=100,
        healthy_backends={"gemma-local", "claude", "gpt", "gemini"},
        privacy_policy="strict",
    )
    assert set(candidates) == {"gemma-local", "claude", "gpt", "gemini"}


def test_unhealthy_backend_excluded():
    candidates = eligible_backends(
        intent="chat",
        risk_level="none",
        input_tokens=100,
        healthy_backends={"claude", "gpt"},
        privacy_policy="strict",
    )
    assert "gemma-local" not in candidates
    assert "gemini" not in candidates


def test_context_window_exceeded_excludes_backend():
    # 300k tokens exceeds gemma-local (8192), gpt (128k), and claude (200k);
    # only gemini's 1M window remains eligible.
    candidates = eligible_backends(
        intent="chat",
        risk_level="none",
        input_tokens=300_000,
        healthy_backends={"gemma-local", "claude", "gpt", "gemini"},
        privacy_policy="strict",
    )
    assert candidates == ["gemini"]


def test_score_candidates_returns_sorted_by_score_desc():
    scored = score_candidates(
        candidates=["gemma-local", "claude", "gpt", "gemini"],
        intent="chat",
        input_tokens=100,
        output_tokens=100,
        budget_pressure=0.0,
    )
    scores = [c.score for c in scored]
    assert scores == sorted(scores, reverse=True)


def test_budget_pressure_bounds():
    assert budget_pressure(0, 100) == 0.0
    assert budget_pressure(100, 100) == 1.0
    assert budget_pressure(200, 100) == 1.0  # clamped
    assert budget_pressure(50, 0) == 0.0  # avoid div by zero
