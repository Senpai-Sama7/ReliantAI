from reliantai.services.schema_validation import validate_local_business_schema


def test_validate_local_business_schema_valid():
    schema = {
        "@context": "https://schema.org",
        "@type": "HVACBusiness",
        "name": "Apex HVAC",
        "address": {"@type": "PostalAddress", "streetAddress": "123 Main"},
        "telephone": "+18325551234",
    }
    result = validate_local_business_schema(schema)
    assert result["valid"] is True


def test_validate_local_business_schema_missing_fields():
    result = validate_local_business_schema({"name": "Apex HVAC"})
    assert result["valid"] is False
    assert "missing_fields" in result
