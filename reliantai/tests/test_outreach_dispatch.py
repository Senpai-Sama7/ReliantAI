from unittest.mock import patch

from reliantai.services.outreach_dispatch import send_email, send_sms


@patch("reliantai.services.outreach_dispatch.httpx.Client")
def test_send_sms_success(mock_client_cls):
    mock_resp = mock_client_cls.return_value.__enter__.return_value.post.return_value
    mock_resp.status_code = 201
    mock_resp.json.return_value = {"sid": "SM123", "status": "queued"}

    with patch.dict(
        "os.environ",
        {
            "TWILIO_ACCOUNT_SID": "sid",
            "TWILIO_AUTH_TOKEN": "token",
            "TWILIO_FROM_NUMBER": "+15551234567",
        },
    ):
        result = send_sms("+15559876543", "Hello")

    assert result == {"sid": "SM123", "status": "queued"}


def test_send_sms_rejects_invalid_number():
    result = send_sms("555-1234", "Hello")
    assert result == {"error": "invalid_number"}


@patch("reliantai.services.outreach_dispatch.httpx.Client")
def test_send_sms_accepts_formatted_number(mock_client_cls):
    mock_resp = mock_client_cls.return_value.__enter__.return_value.post.return_value
    mock_resp.status_code = 201
    mock_resp.json.return_value = {"sid": "SM123", "status": "queued"}

    with patch.dict(
        "os.environ",
        {
            "TWILIO_ACCOUNT_SID": "sid",
            "TWILIO_AUTH_TOKEN": "token",
            "TWILIO_FROM_NUMBER": "+15551234567",
        },
    ):
        result = send_sms("(555) 987-6543", "Hello")

    assert result == {"sid": "SM123", "status": "queued"}
    call_data = mock_client_cls.return_value.__enter__.return_value.post.call_args.kwargs["data"]
    assert call_data["To"] == "+15559876543"


@patch("reliantai.services.outreach_dispatch.httpx.Client")
def test_send_email_success(mock_client_cls):
    mock_resp = mock_client_cls.return_value.__enter__.return_value.post.return_value
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"id": "email-1"}

    with patch.dict("os.environ", {"RESEND_API_KEY": "re_test"}):
        result = send_email("owner@example.com", "Subject", "Body")

    assert result == {"id": "email-1", "status": "sent"}
