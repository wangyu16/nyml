"""NYML Parser implementation."""

import re
from typing import Dict, Any, Optional


class ParseError(Exception):
    """Exception raised for parsing errors."""

    def __init__(self, code: str, message: str, line: int, column: Optional[int] = None):
        self.code = code
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"Line {line}: {message}")


def parse_nyml(text: str, *, strict: bool = False) -> Dict[str, Any]:
    """
    Parse NYML text into a nested dictionary.

    Args:
        text: The NYML content to parse
        strict: If True, enforce consistent indentation steps

    Returns:
        A nested dictionary representing the parsed data

    Raises:
        ParseError: If parsing fails
    """
    def leading_spaces(s: str) -> int:
        """Count leading spaces in a string."""
        return len(s) - len(s.lstrip(' '))

    lines = text.splitlines()
    root: Dict[str, Any] = {}
    # stack of (obj, indent)
    stack = [(root, 0)]

    multiline: Optional[Dict[str, Any]] = None  # None or dict with keys: key, indent, raw_lines

    for i, raw in enumerate(lines, start=1):
        # raw includes trailing spaces; we use raw for content preservation
        indent = leading_spaces(raw)

        if multiline is not None:
            if indent <= multiline['indent']:
                # close multiline: compute content and assign
                # find min indent among non-blank raw_lines
                nonblank = [r for r in multiline['raw_lines'] if r.strip() != '']
                if nonblank:
                    min_indent = min(leading_spaces(r) for r in nonblank)
                else:
                    min_indent = 0
                pieces = []
                for r in multiline['raw_lines']:
                    if r.strip() == '':
                        pieces.append('')
                    else:
                        pieces.append(r[min_indent:])
                content = '\n'.join(pieces) + '\n'
                parent = stack[-1][0]
                parent[multiline['key']] = content
                multiline = None
                # fall through to process current line as normal
            else:
                if raw.strip() == '':
                    multiline['raw_lines'].append('')
                else:
                    multiline['raw_lines'].append(raw)
                continue

        # not in multiline state
        if raw.strip() == '':
            continue
        stripped = raw.lstrip(' ')
        if stripped.startswith('#'):
            continue

        # find parent for current indent
        while stack and indent < stack[-1][1]:
            stack.pop()
        parent = stack[-1][0]

        # parse key (handle quoted keys)
        if stripped.startswith('"'):
            end = stripped.find('"', 1)
            if end == -1:
                raise ParseError('UNMATCHED_QUOTE', 'Unmatched quote in key', line=i)
            key = stripped[1:end]
            rest = stripped[end+1:].lstrip()
            if not rest.startswith(':'):
                raise ParseError('MISSING_COLON', 'Missing colon after quoted key', line=i)
            value_part = rest[1:].strip()
            # Unquote if quoted
            if value_part.startswith('"') and value_part.endswith('"') and value_part.count('"') == 2:
                value_part = value_part[1:-1]
            
            if value_part == '|':
                # start multiline collection
                multiline = {'key': key, 'indent': indent, 'raw_lines': []}
                continue
            
            # If value_part is empty, it might be an object if following lines are more-indented.
            if value_part == '':
                # create nested object and push with its indent (child lines must be more indented)
                obj = {}
                parent[key] = obj
                stack.append((obj, indent + 1))
            else:
                parent[key] = value_part
        else:
            idx = raw.find(':')
            if idx == -1:
                raise ParseError('MISSING_COLON', 'Missing colon in key-value pair', line=i)
            key = raw[:idx].strip()
            value_part = raw[idx+1:].strip()
            # Unquote if quoted
            if value_part.startswith('"') and value_part.endswith('"') and value_part.count('"') == 2:
                value_part = value_part[1:-1]

            if value_part == '|':
                # start multiline collection
                multiline = {'key': key, 'indent': indent, 'raw_lines': []}
                continue

            # Unquote if quoted
            if value_part.startswith('"') and value_part.endswith('"') and value_part.count('"') == 2:
                value_part = value_part[1:-1]

            # If value_part is empty, it might be an object if following lines are more-indented.
            if value_part == '':
                # create nested object and push with its indent (child lines must be more indented)
                obj = {}
                parent[key] = obj
                stack.append((obj, indent + 1))
            else:
                parent[key] = value_part

    if multiline is not None:
        # close multiline at EOF
        nonblank = [r for r in multiline['raw_lines'] if r.strip() != '']
        if nonblank:
            min_indent = min(leading_spaces(r) for r in nonblank)
        else:
            min_indent = 0
        pieces = []
        for r in multiline['raw_lines']:
            if r.strip() == '':
                pieces.append('')
            else:
                pieces.append(r[min_indent:])
        content = '\n'.join(pieces) + '\n'
        parent = stack[-1][0]
        parent[multiline['key']] = content
        multiline = None

    return root