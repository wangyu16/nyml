"""Unit tests for NYML V2 parser."""

import pytest
from nyml_parser import parse_nyml_v2, serialize_nyml_v2


class TestBasicParsing:
    """Basic key-value parsing tests."""

    def test_empty_input(self):
        """Empty input returns empty list."""
        assert parse_nyml_v2("") == []

    def test_whitespace_only(self):
        """Whitespace-only input returns empty list."""
        assert parse_nyml_v2("   \n\n   \n") == []

    def test_single_key_value(self):
        """Single key-value pair."""
        result = parse_nyml_v2("name: Alice")
        assert result == [{"name": "Alice"}]

    def test_multiple_key_values(self):
        """Multiple key-value pairs become list items."""
        nyml = """name: Alice
age: 25"""
        result = parse_nyml_v2(nyml)
        assert result == [{"name": "Alice"}, {"age": "25"}]

    def test_duplicate_keys(self):
        """Duplicate keys are preserved as separate list items."""
        nyml = """item: one
item: two
item: three"""
        result = parse_nyml_v2(nyml)
        assert result == [{"item": "one"}, {"item": "two"}, {"item": "three"}]

    def test_value_with_colons(self):
        """Values can contain colons."""
        result = parse_nyml_v2("url: http://example.com:8080/path")
        assert result == [{"url": "http://example.com:8080/path"}]

    def test_value_with_hash(self):
        """Hash symbol in value is preserved (no comments in V2)."""
        result = parse_nyml_v2("comment: # this is not a comment")
        assert result == [{"comment": "# this is not a comment"}]


class TestQuotedKeys:
    """Tests for quoted keys containing special characters."""

    def test_quoted_key_with_colon(self):
        """Quoted key can contain colon."""
        result = parse_nyml_v2('"http:url": value')
        assert result == [{"http:url": "value"}]

    def test_quoted_key_with_spaces(self):
        """Quoted key can contain spaces."""
        result = parse_nyml_v2('"my key": my value')
        assert result == [{"my key": "my value"}]

    def test_multiple_quoted_keys(self):
        """Multiple quoted keys work correctly."""
        nyml = '''"key:one": value1
"key:two": value2'''
        result = parse_nyml_v2(nyml)
        assert result == [{"key:one": "value1"}, {"key:two": "value2"}]


class TestMultiValue:
    """Tests for multi-value fields (lists)."""

    def test_plain_strings(self):
        """Multi-value with plain strings."""
        nyml = """items:
  value1
  value2
  value3"""
        result = parse_nyml_v2(nyml)
        assert result == [{"items": ["value1", "value2", "value3"]}]

    def test_key_value_children(self):
        """Multi-value with key-value children."""
        nyml = """items:
  child1: a
  child2: b"""
        result = parse_nyml_v2(nyml)
        assert result == [{"items": [{"child1": "a"}, {"child2": "b"}]}]

    def test_mixed_content(self):
        """Multi-value with mixed strings and key-value pairs."""
        nyml = """items:
  value1
  child: a
  another plain value"""
        result = parse_nyml_v2(nyml)
        assert result == [{"items": ["value1", {"child": "a"}, "another plain value"]}]

    def test_duplicate_keys_in_list(self):
        """Duplicate keys within multi-value are preserved."""
        nyml = """items:
  child: a
  child: b"""
        result = parse_nyml_v2(nyml)
        assert result == [{"items": [{"child": "a"}, {"child": "b"}]}]

    def test_single_item_list(self):
        """Single item in multi-value still creates a list."""
        nyml = """item:
  only-one"""
        result = parse_nyml_v2(nyml)
        assert result == [{"item": ["only-one"]}]

    def test_single_keyvalue_in_list(self):
        """Single key-value in multi-value creates list with one object."""
        nyml = """item:
  only: one"""
        result = parse_nyml_v2(nyml)
        assert result == [{"item": [{"only": "one"}]}]

    def test_empty_lines_ignored(self):
        """Empty lines in multi-value context are ignored."""
        nyml = """items:
  value1

  value2"""
        result = parse_nyml_v2(nyml)
        assert result == [{"items": ["value1", "value2"]}]


class TestNesting:
    """Tests for nested structures."""

    def test_nested_multi_value(self):
        """Nested multi-value fields."""
        nyml = """outer:
  inner:
    a
    b"""
        result = parse_nyml_v2(nyml)
        assert result == [{"outer": [{"inner": ["a", "b"]}]}]

    def test_deep_nesting(self):
        """Deeply nested structure."""
        nyml = """level1:
  level2:
    level3:
      value: deep"""
        result = parse_nyml_v2(nyml)
        assert result == [{"level1": [{"level2": [{"level3": [{"value": "deep"}]}]}]}]

    def test_sibling_nested_structures(self):
        """Multiple nested structures at same level."""
        nyml = """first:
  a: 1
second:
  b: 2"""
        result = parse_nyml_v2(nyml)
        assert result == [{"first": [{"a": "1"}]}, {"second": [{"b": "2"}]}]


class TestMultilineStrings:
    """Tests for multiline string values."""

    def test_basic_multiline(self):
        """Basic multiline string."""
        nyml = """text: |
  line1
  line2"""
        result = parse_nyml_v2(nyml)
        assert result == [{"text": "line1\nline2\n"}]

    def test_multiline_with_empty_lines(self):
        """Multiline string preserves empty lines."""
        nyml = """text: |
  line1

  line2"""
        result = parse_nyml_v2(nyml)
        assert result == [{"text": "line1\n\nline2\n"}]

    def test_multiline_dedent(self):
        """Multiline string dedents content."""
        nyml = """text: |
    indented
    content"""
        result = parse_nyml_v2(nyml)
        assert result == [{"text": "indented\ncontent\n"}]

    def test_multiline_preserves_relative_indent(self):
        """Multiline string preserves relative indentation."""
        nyml = """code: |
  if true:
    print("yes")
  else:
    print("no")"""
        result = parse_nyml_v2(nyml)
        expected = "if true:\n  print(\"yes\")\nelse:\n  print(\"no\")\n"
        assert result == [{"code": expected}]

    def test_multiline_with_hash(self):
        """Hash in multiline is preserved (not a comment)."""
        nyml = """md: |
  # Heading
  Content"""
        result = parse_nyml_v2(nyml)
        assert result == [{"md": "# Heading\nContent\n"}]

    def test_multiline_followed_by_key(self):
        """Content after multiline block is parsed correctly."""
        nyml = """text: |
  multiline
  content
next: value"""
        result = parse_nyml_v2(nyml)
        assert result == [{"text": "multiline\ncontent\n"}, {"next": "value"}]


class TestRootLevelBehavior:
    """Tests for root-level parsing behavior."""

    def test_root_plain_string_ignored(self):
        """Plain strings at root level are ignored (Rule 9)."""
        nyml = """this is ignored
name: Alice
also ignored
age: 25"""
        result = parse_nyml_v2(nyml)
        assert result == [{"name": "Alice"}, {"age": "25"}]

    def test_root_string_like_comment(self):
        """Root strings can be used like comments."""
        nyml = """This is like a comment
key: value"""
        result = parse_nyml_v2(nyml)
        assert result == [{"key": "value"}]


class TestEdgeCases:
    """Edge case tests."""

    def test_value_only_colon(self):
        """Value that is just spaces after colon creates multi-value."""
        nyml = """items:   
  value1"""
        result = parse_nyml_v2(nyml)
        assert result == [{"items": ["value1"]}]

    def test_key_only_spaces_before_colon(self):
        """Key can have spaces."""
        result = parse_nyml_v2("my key: value")
        assert result == [{"my key": "value"}]

    def test_value_with_leading_spaces(self):
        """Leading spaces in value are trimmed."""
        result = parse_nyml_v2("key:    value with spaces   ")
        assert result == [{"key": "value with spaces"}]

    def test_inline_value_with_colon(self):
        """Inline value containing colon is plain string."""
        result = parse_nyml_v2("item: only: one")
        assert result == [{"item": "only: one"}]


class TestSpecExamples:
    """Tests based on examples from NYML_V2.md spec."""

    def test_spec_example_1(self):
        """First spec example: name and age."""
        nyml = """name: Alice
age: 25"""
        result = parse_nyml_v2(nyml)
        assert result == [{"name": "Alice"}, {"age": "25"}]

    def test_spec_example_2(self):
        """Second spec example: items with mixed content."""
        nyml = """items:
  value1
  value2
  child: a
  child: b"""
        result = parse_nyml_v2(nyml)
        assert result == [{"items": ["value1", "value2", {"child": "a"}, {"child": "b"}]}]

    def test_spec_example_3(self):
        """Third spec example: mixed strings and key-values."""
        nyml = """items:
  value1
  child: a
  another plain value"""
        result = parse_nyml_v2(nyml)
        assert result == [{"items": ["value1", {"child": "a"}, "another plain value"]}]

    def test_spec_example_single_item(self):
        """Spec example: single item list."""
        nyml = """item:
  only-one"""
        result = parse_nyml_v2(nyml)
        assert result == [{"item": ["only-one"]}]

    def test_spec_example_single_keyvalue(self):
        """Spec example: single key-value in list."""
        nyml = """item:
  only: one"""
        result = parse_nyml_v2(nyml)
        assert result == [{"item": [{"only": "one"}]}]

    def test_spec_example_inline_colon(self):
        """Spec example: inline colon treated as plain value."""
        nyml = "item: only: one"
        result = parse_nyml_v2(nyml)
        assert result == [{"item": "only: one"}]

    def test_spec_example_nested(self):
        """Spec example: nested multi-value."""
        nyml = """outer:
  inner:
    a
    b"""
        result = parse_nyml_v2(nyml)
        assert result == [{"outer": [{"inner": ["a", "b"]}]}]


class TestSerialization:
    """Tests for serialize_nyml_v2."""

    def test_serialize_simple(self):
        """Serialize simple key-value pairs."""
        data = [{"name": "Alice"}, {"age": "25"}]
        result = serialize_nyml_v2(data)
        assert result == "name: Alice\nage: 25"

    def test_serialize_multivalue(self):
        """Serialize multi-value list."""
        data = [{"items": ["a", "b", "c"]}]
        result = serialize_nyml_v2(data)
        expected = """items:
  a
  b
  c"""
        assert result == expected

    def test_serialize_mixed_list(self):
        """Serialize mixed content list."""
        data = [{"items": ["value", {"key": "val"}]}]
        result = serialize_nyml_v2(data)
        expected = """items:
  value
  key: val"""
        assert result == expected

    def test_serialize_multiline(self):
        """Serialize multiline string."""
        data = [{"text": "line1\nline2\n"}]
        result = serialize_nyml_v2(data)
        expected = """text: |
  line1
  line2"""
        assert result == expected

    def test_serialize_quoted_key(self):
        """Serialize key containing colon."""
        data = [{"http:url": "value"}]
        result = serialize_nyml_v2(data)
        assert result == '"http:url": value'


class TestRoundtrip:
    """Roundtrip tests: parse -> serialize -> parse."""

    def test_roundtrip_simple(self):
        """Roundtrip simple key-value."""
        original = "name: Alice"
        data = parse_nyml_v2(original)
        serialized = serialize_nyml_v2(data)
        reparsed = parse_nyml_v2(serialized)
        assert data == reparsed

    def test_roundtrip_multivalue(self):
        """Roundtrip multi-value list."""
        original = """items:
  value1
  value2"""
        data = parse_nyml_v2(original)
        serialized = serialize_nyml_v2(data)
        reparsed = parse_nyml_v2(serialized)
        assert data == reparsed

    def test_roundtrip_nested(self):
        """Roundtrip nested structure."""
        original = """outer:
  inner:
    a
    b"""
        data = parse_nyml_v2(original)
        serialized = serialize_nyml_v2(data)
        reparsed = parse_nyml_v2(serialized)
        assert data == reparsed

    def test_roundtrip_mixed(self):
        """Roundtrip mixed content."""
        original = """items:
  value1
  child: a
  value2"""
        data = parse_nyml_v2(original)
        serialized = serialize_nyml_v2(data)
        reparsed = parse_nyml_v2(serialized)
        assert data == reparsed
