"""Tests for NYML parser."""

import pytest
from nyml_parser import parse_nyml, ParseError, to_mapping, get_all


def test_basic_key_value():
    """Test basic key-value parsing."""
    text = "key: value"
    result = parse_nyml(text)
    assert result == {"key": "value"}


def test_nested_object():
    """Test nested object parsing."""
    text = """parent:
  child: value"""
    result = parse_nyml(text)
    assert result == {"parent": {"child": "value"}}


def test_comments():
    """Test comment handling."""
    text = """# This is a comment
key: value
# Another comment"""
    result = parse_nyml(text)
    assert result == {"key": "value"}


def test_quoted_keys():
    """Test quoted keys with special characters."""
    text = '"http://example.com": "URL"'
    result = parse_nyml(text)
    # value should include quotes as part of the string
    assert result == {"http://example.com": '"URL"'}


def test_multiline_string():
    """Test multiline string parsing."""
    text = """message: |
  This is a multiline
  string with content."""
    result = parse_nyml(text)
    expected = "This is a multiline\nstring with content.\n"
    assert result == {"message": expected}


def test_comprehensive_example():
    """Test the comprehensive example from README.md."""
    text = '''# Main configuration for the application
# All values will be parsed as strings.

app_name: "My App"
version: 1.2

# Server settings can be nested
server:
  # Host and port (this is a comment)
  host: localhost
  port: 8080
  
  # The value here includes the hash
  status_message: "OK # (production)"

# Use quoted keys for special characters
"http:routes": "/api/v1"
"user:admin": "admin-user"

# This multiline block contains markdown
# and demonstrates indentation handling.
welcome_message: |
  # This is NOT a comment.
  # It is the first line of the string.
  
  This is the main welcome message.
  
  Please see the following:
    * List item 1
    * List item 2
      * A nested item
  
  A line with a # is just text.

# This comment is outside the block.
# The multiline block ended on the line above.
logging:
  level: info'''

    result = parse_nyml(text)
    expected = {
        "app_name": '"My App"',
        "version": "1.2",
        "server": {
            "host": "localhost",
            "port": "8080",
            "status_message": '"OK # (production)"'
        },
        "http:routes": '"/api/v1"',
        "user:admin": '"admin-user"',
        "welcome_message": "# This is NOT a comment.\n# It is the first line of the string.\n\nThis is the main welcome message.\n\nPlease see the following:\n  * List item 1\n  * List item 2\n    * A nested item\n\nA line with a # is just text.\n",
        "logging": {
            "level": "info"
        }
    }
    assert result == expected


def test_missing_colon():
    """Test error for missing colon."""
    text = "key value"
    with pytest.raises(ParseError) as exc_info:
        parse_nyml(text)
    assert exc_info.value.code == 'MISSING_COLON'


def test_unmatched_quote():
    """Test error for unmatched quote in key."""
    text = '"key: value'
    with pytest.raises(ParseError) as exc_info:
        parse_nyml(text)
    assert exc_info.value.code == 'UNMATCHED_QUOTE'


def test_unterminated_multiline():
    """Test unterminated multiline block closes at EOF."""
    text = """key: |
  content"""
    result = parse_nyml(text)
    assert result == {'key': 'content\n'}


def test_entries_and_duplicates():
    """Test that parse_nyml(as_entries=True) preserves order and duplicates."""
    text = "a: 1\nb: 2\na: 3\n"
    doc = parse_nyml(text, as_entries=True)
    assert isinstance(doc, dict)
    entries = doc['entries']
    assert len(entries) == 3
    assert entries[0]['key'] == 'a' and entries[0]['value'] == '1'
    assert entries[1]['key'] == 'b' and entries[1]['value'] == '2'
    assert entries[2]['key'] == 'a' and entries[2]['value'] == '3'


def test_to_mapping_all_and_last():
    text = "a: 1\na: 2\nb: 3\n"
    doc = parse_nyml(text, as_entries=True)
    from nyml_parser import to_mapping
    last_map = to_mapping(doc, strategy='last')
    assert last_map['a'] == '2'
    all_map = to_mapping(doc, strategy='all')
    assert all_map['a'] == ['1', '2']