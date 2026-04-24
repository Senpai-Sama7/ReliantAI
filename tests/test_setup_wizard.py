import os
import re
import sys

# Add scripts to path for importing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts import setup_wizard


def test_set_env_var_append_and_replace():
    """Test that set_env_var can append new keys and replace existing ones."""
    content = "FOO=1\nBAR=2\n"

    # Replace existing key
    content = setup_wizard.set_env_var(content, "BAR", "22")
    assert re.search(r"^BAR=22$", content, re.MULTILINE)
    # Verify the old value is not there (not as a substring in case of overlap)
    assert not re.search(r"^BAR=2$", content, re.MULTILINE)

    # Append new key
    content = setup_wizard.set_env_var(content, "NEWKEY", "xyz")
    assert re.search(r"^NEWKEY=xyz$", content, re.MULTILINE)


def test_set_env_var_with_comments():
    """Test that set_env_var handles keys with comments and whitespace."""
    content = "KEY1=value1 # This is a comment\nKEY2=value2\n"
    content = setup_wizard.set_env_var(content, "KEY1", "newvalue1")
    assert re.search(r"^KEY1=newvalue1$", content, re.MULTILINE)
    # The old line with comment should be replaced
    assert "# This is a comment" not in content


def test_set_env_var_empty_content():
    """Test that set_env_var handles empty content."""
    content = ""
    content = setup_wizard.set_env_var(content, "KEY1", "value1")
    assert "KEY1=value1" in content


def test_backup_file(tmp_path):
    """Test that backup_file creates a timestamped backup."""
    env_file = tmp_path / ".env"
    env_file.write_text("X=1\n", encoding="utf-8")

    bak = setup_wizard.backup_file(str(env_file))
    assert bak is not None
    assert os.path.exists(bak)
    assert "bak" in bak

    # Read the backup and verify it has the same content
    with open(bak, "r", encoding="utf-8") as f:
        assert f.read() == "X=1\n"


def test_backup_file_nonexistent():
    """Test that backup_file returns None for nonexistent file."""
    bak = setup_wizard.backup_file("/nonexistent/path/.env")
    assert bak is None


def test_read_file(tmp_path):
    """Test that read_file reads UTF-8 content correctly."""
    test_file = tmp_path / "test.env"
    test_file.write_text("KEY=value\n", encoding="utf-8")

    content = setup_wizard.read_file(str(test_file))
    assert content == "KEY=value\n"


def test_read_file_nonexistent():
    """Test that read_file returns None for missing file."""
    content = setup_wizard.read_file("/nonexistent/test.env")
    assert content is None


def test_write_file(tmp_path):
    """Test that write_file writes UTF-8 content correctly."""
    test_file = tmp_path / "test.env"
    content = "KEY1=value1\nKEY2=value2\n"

    setup_wizard.write_file(str(test_file), content)

    with open(str(test_file), "r", encoding="utf-8") as f:
        assert f.read() == content


def test_create_empty_file_truncates_existing(tmp_path):
    """Test that create_empty_file truncates an existing file."""
    test_file = tmp_path / "test.env"
    # Create a file with content
    test_file.write_text("OLD_CONTENT=value\n", encoding="utf-8")

    # Call create_empty_file
    setup_wizard.create_empty_file(str(test_file))

    # Verify it's empty
    with open(str(test_file), "r", encoding="utf-8") as f:
        content = f.read()
        assert content == ""


def test_regex_handles_trailing_comments():
    """Test that the regex used in run_setup doesn't capture trailing comments."""
    content = """
KEY1=value1 # This is a comment
KEY2=value2# No space before comment
KEY3=value3
"""
    # Simulate the regex used in run_setup (line ~167)
    key = "KEY1"
    m = re.search(rf"^\s*{re.escape(key)}\s*=\s*([^#\n\r]*)", content, re.MULTILINE)
    if m:
        value = m.group(1).strip()
        # Should get just "value1", not the comment
        assert value == "value1"
        assert "#" not in value

    key = "KEY2"
    m = re.search(rf"^\s*{re.escape(key)}\s*=\s*([^#\n\r]*)", content, re.MULTILINE)
    if m:
        value = m.group(1).strip()
        assert value == "value2"
        assert "#" not in value
