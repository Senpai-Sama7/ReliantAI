from reliantai.lib.slug import is_valid_slug


def test_valid_slugs():
    assert is_valid_slug("test-hvac-austin")
    assert is_valid_slug("comfort-pro-hvac-austin-ab12")


def test_rejects_traversal_and_invalid():
    assert not is_valid_slug("../admin")
    assert not is_valid_slug("")
    assert not is_valid_slug("a" * 101)
    assert not is_valid_slug("UPPER-case")
    assert not is_valid_slug("bad--double")
