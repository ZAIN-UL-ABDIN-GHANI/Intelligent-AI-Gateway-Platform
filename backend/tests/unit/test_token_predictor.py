from app.routing.agents.token_predictor import estimate_input_tokens, estimate_output_tokens


def test_input_tokens_roughly_chars_over_4():
    prompt = "a" * 400
    assert estimate_input_tokens(prompt) == 100


def test_input_tokens_never_zero():
    assert estimate_input_tokens("") >= 1


def test_code_intent_predicts_more_output_tokens_than_chat():
    chat_tokens = estimate_output_tokens("chat", 50)
    code_tokens = estimate_output_tokens("code", 50)
    assert code_tokens > chat_tokens


def test_output_tokens_scale_with_input():
    small = estimate_output_tokens("chat", 10)
    large = estimate_output_tokens("chat", 5000)
    assert large > small
