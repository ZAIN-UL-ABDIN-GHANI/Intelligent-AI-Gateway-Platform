from app.routing.agents.intent import detect_intent


def test_detects_code_intent():
    assert detect_intent("Here is some code: ```def foo(): pass```") == "code"


def test_detects_summarization_intent():
    assert detect_intent("Please summarize this article for me") == "summarization"


def test_detects_extraction_intent():
    assert detect_intent("Extract all email addresses from this text") == "extraction"


def test_detects_creative_intent():
    assert detect_intent("Write a short story about a dragon") == "creative"


def test_detects_reasoning_intent():
    assert detect_intent("Explain step by step why the sky is blue") == "reasoning"


def test_detects_qa_intent():
    assert detect_intent("What is the capital of France?") == "qa"


def test_defaults_to_chat():
    assert detect_intent("hey there") == "chat"
