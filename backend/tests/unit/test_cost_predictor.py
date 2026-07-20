from app.routing.agents.cost_predictor import predict_cost


def test_local_backend_is_free():
    assert predict_cost("gemma-local", 1000, 1000) == 0.0


def test_cloud_backend_costs_more_than_zero():
    assert predict_cost("claude", 1000, 1000) > 0.0


def test_more_tokens_costs_more():
    small = predict_cost("gpt", 100, 100)
    large = predict_cost("gpt", 10000, 10000)
    assert large > small
