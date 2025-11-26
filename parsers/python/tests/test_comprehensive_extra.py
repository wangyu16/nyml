"""Extra comprehensive tests for NYML parser."""
import json
import os
import subprocess
import sys

import pytest

from nyml_parser import parse_nyml, to_mapping, get_all


def test_entries_for_comprehensive_example():
    path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'examples', 'comprehensive_example.nyml')
    with open(path, 'r') as f:
        text = f.read()
    doc = parse_nyml(text, as_entries=True)
    assert isinstance(doc, dict)
    entries = doc['entries']
    # basic checks
    keys = [e['key'] for e in entries]
    assert 'app_name' in keys
    assert 'messages' in keys
    # find 'messages' entry and its children 'welcome'
    messages_entries = [e for e in entries if e['key'] == 'messages']
    assert len(messages_entries) == 1
    # dive into messages.children to find welcome key
    msg_children = messages_entries[0]['children']
    welcome_entries = [c for c in msg_children if c['key'] == 'welcome']
    assert len(welcome_entries) == 1
    welcome_val = welcome_entries[0]['value']
    assert 'NOT a comment' in welcome_val


def test_cli_python_entries_and_mapping(tmp_path):
    script = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'examples', 'nyml_cli.py')
    file = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'examples', 'comprehensive_example.nyml')
    python_exe = os.path.join(os.path.dirname(__file__), '..', 'venv', 'bin', 'python')
    # entries
    out = subprocess.check_output([python_exe, script, '--entries', file])
    doc = json.loads(out)
    assert doc['type'] == 'document'
    assert any(e['key'] == 'messages' for e in doc['entries'])
    # mapping all
    out = subprocess.check_output([python_exe, script, '--strategy', 'all', file])
    mapping = json.loads(out)
    # 'app_name' should be a string in mapping
    assert 'app_name' in mapping
    # array handling: items should show up as strings when roundtrip
    # test using array_test.json conversion


def test_array_roundtrip_json_to_nyml_to_json():
    # convert the array_test.json to nyml and parse back
    json_file = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'examples', 'array_test.json')
    script_py = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'examples', 'convert_json_to_nyml.py')
    nyml_out = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'examples', 'array_test.nyml')
    python_exe = os.path.join(os.path.dirname(__file__), '..', 'venv', 'bin', 'python')
    # create nyml
    out = subprocess.check_output([python_exe, script_py, json_file])
    with open(nyml_out, 'wb') as f:
        f.write(out)
    # parse nyml back
    parsed = parse_nyml(out.decode('utf-8'))
    # items should be a string (multiline)
    assert isinstance(parsed['items'], str)


def test_unicode_and_large_numbers_roundtrip():
    # Use in-repo JSON for edge cases
    json_in = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'examples', 'edge_case_test.json')
    script_py = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'examples', 'convert_json_to_nyml.py')
    python_exe = os.path.join(os.path.dirname(__file__), '..', 'venv', 'bin', 'python')
    out = subprocess.check_output([python_exe, script_py, json_in])
    parsed = parse_nyml(out.decode('utf-8'))
    # The number should be string and preserved as text
    assert parsed['big_number'] == '123456789012345678901234567890'
    assert 'This is a very long string' in parsed['very_long_string']
