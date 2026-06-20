import re


def normalize_us_e164(phone: str) -> str | None:
    """Normalize common US phone formats to E.164 (+1XXXXXXXXXX)."""
    if not phone:
        return None

    trimmed = phone.strip()
    if re.match(r"^\+1\d{10}$", trimmed):
        return trimmed

    digits = re.sub(r"\D", "", trimmed)
    if len(digits) == 10:
        return f"+1{digits}"
    if len(digits) == 11 and digits.startswith("1"):
        return f"+{digits}"
    return None
