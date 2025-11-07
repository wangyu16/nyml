#!/usr/bin/env python3
"""Convert NYML file to JSON."""

import sys
import json
import os

# Add the parser to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'parsers', 'python'))

from nyml_parser import parse_nyml

def main():
    if len(sys.argv) != 2:
        print("Usage: python convert_nyml_to_json.py <nyml_file>")
        sys.exit(1)

    nyml_file = sys.argv[1]

    try:
        with open(nyml_file, 'r') as f:
            nyml_content = f.read()

        # Parse NYML
        result = parse_nyml(nyml_content)

        # Output as JSON
        print(json.dumps(result, indent=2))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        print(f"Type: {type(e)}", file=sys.stderr)
        if hasattr(e, 'code'):
            print(f"Code: {e.code}", file=sys.stderr)
        if hasattr(e, 'line'):
            print(f"Line: {e.line}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()