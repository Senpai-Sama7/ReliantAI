from reliantai.services.sms_compliance import is_stop_request


def test_is_stop_request_exact_phrase():
    assert is_stop_request("STOP") is True
    assert is_stop_request("opt out") is True


def test_is_stop_request_word_boundary():
    assert is_stop_request("please cancel my subscription") is True


def test_is_stop_request_no_false_positive_on_substrings():
    assert is_stop_request("You seem friendly and professional") is False
    assert is_stop_request("cancellation policy") is False
