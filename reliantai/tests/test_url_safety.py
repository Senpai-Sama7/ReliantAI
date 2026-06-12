from reliantai.services.url_safety import sanitize_http_url


def test_sanitize_http_url_accepts_https():
    assert sanitize_http_url("https://example.com/path") == "https://example.com/path"


def test_sanitize_http_url_accepts_http():
    assert sanitize_http_url("http://example.com") == "http://example.com"


def test_sanitize_http_url_rejects_javascript():
    assert sanitize_http_url("javascript:alert(1)") is None


def test_sanitize_http_url_rejects_data_uri():
    assert sanitize_http_url("data:text/html,<script>alert(1)</script>") is None


def test_sanitize_http_url_rejects_empty_and_none():
    assert sanitize_http_url("") is None
    assert sanitize_http_url("   ") is None
    assert sanitize_http_url(None) is None
