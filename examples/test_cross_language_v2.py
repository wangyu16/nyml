#!/usr/bin/env python3
"""Cross-language consistency test for NYML V2 parsers.

This script verifies that Python and JavaScript V2 parsers produce
identical output for all test cases.
"""

import json
import subprocess
import sys
from pathlib import Path

# Add parser to path
sys.path.insert(0, str(Path(__file__).parent.parent / "parsers" / "python"))

from nyml_parser import parse_nyml_v2

# Test cases: (name, nyml_content)
TEST_CASES = [
    ("empty", ""),
    ("single_kv", "name: Alice"),
    ("multiple_kv", "name: Alice\nage: 25"),
    ("duplicate_keys", "item: one\nitem: two\nitem: three"),
    ("value_with_colons", "url: http://example.com:8080/path"),
    ("value_with_hash", "comment: # this is not a comment"),
    ("quoted_key", '"http:url": value'),
    ("plain_strings", "items:\n  value1\n  value2\n  value3"),
    ("key_value_children", "items:\n  child1: a\n  child2: b"),
    ("mixed_content", "items:\n  value1\n  child: a\n  another plain value"),
    ("nested", "outer:\n  inner:\n    a\n    b"),
    ("deep_nesting", "level1:\n  level2:\n    level3:\n      value: deep"),
    ("multiline", "text: |\n  line1\n  line2"),
    ("multiline_with_empty", "text: |\n  line1\n\n  line2"),
    ("multiline_dedent", "text: |\n    indented\n    content"),
    ("root_plain_ignored", "ignored\nkey: value\nalso ignored"),
    ("single_item_list", "item:\n  only-one"),
    ("inline_colon", "item: only: one"),
]


def run_js_parser(nyml_content: str) -> list:
    """Run JavaScript parser and return result."""
    js_code = f"""
const {{ parseNymlV2 }} = require('./parsers/javascript/nyml-parser-v2');
const content = {json.dumps(nyml_content)};
const result = parseNymlV2(content);
console.log(JSON.stringify(result));
"""
    result = subprocess.run(
        ["node", "-e", js_code],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent,
    )
    if result.returncode != 0:
        raise RuntimeError(f"JS parser error: {result.stderr}")
    return json.loads(result.stdout)


def main():
    """Run cross-language consistency tests."""
    print("=" * 60)
    print("NYML V2 Cross-Language Consistency Test")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for name, nyml_content in TEST_CASES:
        try:
            py_result = parse_nyml_v2(nyml_content)
            js_result = run_js_parser(nyml_content)
            
            if py_result == js_result:
                print(f"✓ {name}")
                passed += 1
            else:
                print(f"✗ {name}")
                print(f"  Python: {json.dumps(py_result)}")
                print(f"  JS:     {json.dumps(js_result)}")
                failed += 1
        except Exception as e:
            print(f"✗ {name} - Error: {e}")
            failed += 1
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
