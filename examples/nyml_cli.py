#!/usr/bin/env python3
"""NYML CLI: Parse NYML and output JSON mapping or entries document.

Usage:
  python nyml_cli.py [--entries] [--strategy last|first|all] [-o OUTPUT] FILE

Examples:
  python nyml_cli.py config.nyml
  python nyml_cli.py --entries config.nyml
  python nyml_cli.py --strategy=all config.nyml
"""
import argparse
import json
import os
import sys

# Make sure parsers/python is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'parsers', 'python'))
from nyml_parser import parse_nyml, to_mapping


def main():
    parser = argparse.ArgumentParser(description='Parse NYML and output JSON (mapping or ordered entries)')
    parser.add_argument('file', help='NYML file to parse')
    parser.add_argument('--entries', '-e', action='store_true', help='Output ordered entries document (preserve duplicates)')
    parser.add_argument('--strategy', '-s', choices=['last', 'first', 'all'], default='last', help='Duplicate resolution strategy when converting entries to mapping')
    parser.add_argument('--output', '-o', help='Output file (defaults to stdout)')

    args = parser.parse_args()

    with open(args.file, 'r') as f:
        text = f.read()

    if args.entries:
        doc = parse_nyml(text, as_entries=True)
        out = json.dumps(doc, indent=2)
    else:
        # Use mapping directly
        # For backward compatibility parse_nyml(text) returns mapping (last wins)
        # If user wants ``all`` strategy they can request entries then to_mapping
        if args.strategy == 'last':
            mapping = parse_nyml(text)
        else:
            doc = parse_nyml(text, as_entries=True)
            mapping = to_mapping(doc, strategy=args.strategy)
        out = json.dumps(mapping, indent=2)

    if args.output:
        with open(args.output, 'w') as out_f:
            out_f.write(out)
    else:
        print(out)


if __name__ == '__main__':
    main()
