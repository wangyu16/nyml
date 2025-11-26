#!/usr/bin/env python3
"""Convert 'entries' document JSON into NYML format.

This tool expects a JSON document like:
{
  "type": "document",
  "entries": [ { "key": "a", "value": "1" }, { ... } ]
}

It will write NYML that matches the entries (preserving duplicate keys and ordering).
"""

import json
import sys
from typing import Any, Dict, List


def needs_quoting_key(key: str) -> bool:
    if key.startswith('"') and key.endswith('"'):
        return False
    return (
        ' ' in key or ':' in key or '@' in key or
        key[0].isdigit() or not key.replace('_', '').replace('-', '').replace('.', '').isalnum()
    )


def write_entry(e: Dict[str, Any], indent: int = 0) -> List[str]:
    lines: List[str] = []
    ind = '  ' * indent
    key = e.get('key')
    qk = e.get('quoted_key', False)
    if qk or needs_quoting_key(key):
        key_str = f'"{key}' + '"'
    else:
        key_str = key

    if 'children' in e and e['children'] is not None:
        lines.append(f"{ind}{key_str}:")
        for child in e['children']:
            lines.extend(write_entry(child, indent + 1))
    else:
        value = e.get('value', '')
        raw = e.get('raw', '')
        if value == '' and raw.strip().endswith('|'):
            # Explicitly a multiline with empty content
            lines.append(f"{ind}{key_str}: |")
            lines.append('')
        elif isinstance(value, str) and '\n' in value:
            # multiline
            lines.append(f"{ind}{key_str}: |")
            # For indentation of block, split lines, keep exact content (don't strip outer quotes)
            content_lines = value.split('\n')
            # If trailing empty string, we still want the trailing newline; the parser expects a trailing newline
            # Convert lines: each line should be indented by two spaces more
            for l in content_lines:
                if l == '':
                    lines.append(f"{ind}  ")
                else:
                    lines.append(f"{ind}  {l}")
            lines.append('')  # blank line after a multiline block
        else:
            # ensure we output values literally (they might include surrounding quotes)
            lines.append(f"{ind}{key_str}: {value}")
    return lines


def main():
    if len(sys.argv) != 2:
        print("Usage: python entries_json_to_nyml.py <entries_json>")
        sys.exit(1)

    p = sys.argv[1]
    with open(p, 'r') as f:
        data = json.load(f)

    if isinstance(data, dict) and data.get('type') == 'document' and 'entries' in data:
        entries = data['entries']
    elif isinstance(data, list):
        entries = data
    else:
        print('Invalid entries document: expected object with type=document or list of entries', file=sys.stderr)
        sys.exit(1)

    lines: List[str] = []
    for e in entries:
        lines.extend(write_entry(e, indent=0))

    print('\n'.join(lines))


if __name__ == '__main__':
    main()
