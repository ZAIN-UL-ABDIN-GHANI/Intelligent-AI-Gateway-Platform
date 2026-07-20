from app.routing.agents.risk import classify_risk


def test_no_pii_returns_none():
    assert classify_risk("What's the weather like today?") == "none"


def test_email_flagged_low_risk():
    assert classify_risk("Contact me at jane.doe@example.com please") == "low"


def test_ssn_flagged_high_risk():
    assert classify_risk("My SSN is 123-45-6789") == "high"


def test_secret_key_flagged_high_risk():
    assert classify_risk("Here is my api_key for the service") == "high"


def test_credit_card_flagged_high_risk():
    assert classify_risk("Card number: 4111 1111 1111 1111") == "high"
