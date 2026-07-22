from reliantai.services.url_safety import is_public_http_url, sanitize_http_url


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


def test_sanitize_http_url_prepends_https_for_bare_domains():
    assert sanitize_http_url("www.example.com") == "https://www.example.com"
    assert sanitize_http_url("example.com/path") == "https://example.com/path"


def test_is_public_http_url_rejects_localhost():
    assert is_public_http_url("http://127.0.0.1/secret") is False
    assert is_public_http_url("http://localhost/admin") is False


def test_is_public_http_url_rejects_metadata():
    assert is_public_http_url("http://169.254.169.254/latest/meta-data") is False


def test_is_public_http_url_rejects_credentials():
    assert is_public_http_url("https://user:pass@example.com/") is False


def test_is_public_http_url_accepts_public_https():
    assert is_public_http_url("https://example.com/page") is True
