from reliantai.services.phone import normalize_us_e164


def test_normalize_us_e164_accepts_e164():
    assert normalize_us_e164("+15551234567") == "+15551234567"


def test_normalize_us_e164_strips_formatting():
    assert normalize_us_e164("(555) 123-4567") == "+15551234567"
    assert normalize_us_e164("555-123-4567") == "+15551234567"
    assert normalize_us_e164("1-555-123-4567") == "+15551234567"


def test_normalize_us_e164_rejects_invalid():
    assert normalize_us_e164("123") is None
    assert normalize_us_e164("") is None
