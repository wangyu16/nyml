"""NYML Parser implementation."""

import re
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, List


class ParseError(Exception):
    """Exception raised for parsing errors."""

    def __init__(self, code: str, message: str, line: int, column: Optional[int] = None):
        self.code = code
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"Line {line}: {message}")


@dataclass
class NYMLEntry:
    key: str
    value: Optional[str] = None
    children: Optional[List["NYMLEntry"]] = None
    quoted_key: bool = False
    line: Optional[int] = None
    indent: Optional[int] = None
    raw: Optional[str] = None


def _entry_to_dict(e: NYMLEntry) -> Dict[str, Any]:
    d: Dict[str, Any] = {"key": e.key}
    if e.value is not None:
        d["value"] = e.value
    if e.children is not None:
        d["children"] = [ _entry_to_dict(c) for c in e.children ]
    if e.quoted_key:
        d["quoted_key"] = True
    if e.line is not None:
        d["line"] = e.line
    if e.indent is not None:
        d["indent"] = e.indent
    if e.raw is not None:
        d["raw"] = e.raw
    return d


def parse_nyml(text: str, *, strict: bool = False, as_entries: bool = False) -> Dict[str, Any]:
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
    # Document represented as ordered entries
    root_entries: List[NYMLEntry] = []
    # stack of (entries_list, indent)
    stack: List[Any] = [(root_entries, 0)]

    multiline: Optional[Dict[str, Any]] = None  # None or dict with keys: entry (NYMLEntry), indent, raw_lines

    for i, raw in enumerate(lines, start=1):
        # raw includes trailing spaces; we use raw for content preservation
        indent = leading_spaces(raw)

        if multiline is not None:
            if raw.strip() == '':
                multiline['raw_lines'].append('')
                continue
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
                # collapse multiple trailing blank lines to a single one to match original behavior
                while len(pieces) >= 2 and pieces[-1] == '' and pieces[-2] == '':
                    pieces.pop()
                if pieces and pieces[-1] == '':
                    # join will already end with a trailing newline
                    content = '\n'.join(pieces)
                else:
                    content = '\n'.join(pieces) + '\n'
                # assign to the entry
                entry = multiline['entry']
                entry.value = content
                multiline = None
                # fall through to process current line as normal
            else:
                multiline['raw_lines'].append(raw)
                continue

        # not in multiline state
        if raw.strip() == '':
            continue
        stripped = raw.lstrip(' ')
        if stripped.startswith('#'):
            continue

        # find parent for current indent (entries list)
        while stack and indent < stack[-1][1]:
            stack.pop()
        parent_entries = stack[-1][0]

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
            
            entry = NYMLEntry(key=key, quoted_key=True, line=i, indent=indent, raw=raw)
            parent_entries.append(entry)
            if value_part == '|':
                # start multiline collection
                multiline = {'entry': entry, 'indent': indent, 'raw_lines': []}
                continue
            
            # If value_part is empty, it might be an object if following lines are more-indented.
            if value_part == '':
                # create nested object container of entries
                entry.children = []
                stack.append((entry.children, indent + 1))
            else:
                entry.value = value_part
        else:
            idx = raw.find(':')
            if idx == -1:
                raise ParseError('MISSING_COLON', 'Missing colon in key-value pair', line=i)
            key = raw[:idx].strip()
            value_part = raw[idx+1:].strip()
            # Unquote if quoted
            if value_part.startswith('"') and value_part.endswith('"') and value_part.count('"') == 2:
                value_part = value_part[1:-1]

            entry = NYMLEntry(key=key, quoted_key=False, line=i, indent=indent, raw=raw)
            parent_entries.append(entry)
            if value_part == '|':
                # start multiline collection
                multiline = {'entry': entry, 'indent': indent, 'raw_lines': []}
                continue

            # Unquote if quoted
            if value_part.startswith('"') and value_part.endswith('"') and value_part.count('"') == 2:
                value_part = value_part[1:-1]

            # If value_part is empty, it might be an object if following lines are more-indented.
            if value_part == '':
                entry.children = []
                stack.append((entry.children, indent + 1))
            else:
                entry.value = value_part

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
        while len(pieces) >= 2 and pieces[-1] == '' and pieces[-2] == '':
            pieces.pop()
        if pieces and pieces[-1] == '':
            content = '\n'.join(pieces)
        else:
            content = '\n'.join(pieces) + '\n'
        entry = multiline['entry']
        entry.value = content
        multiline = None

    # If caller wants entries, return document form
    if as_entries:
        return {"type": "document", "entries": [ _entry_to_dict(e) for e in root_entries ]}

    # Otherwise convert to mapping for backward compatibility
    def entries_to_mapping(entries: List[NYMLEntry]):
        result: Dict[str, Any] = {}
        for e in entries:
            if e.children is not None:
                value = entries_to_mapping(e.children)
            else:
                value = e.value if e.value is not None else ''
            # last-write wins by default for backward compatibility
            result[e.key] = value
        return result

    return entries_to_mapping(root_entries)


def to_mapping(document: Any, strategy: str = 'last') -> Dict[str, Any]:
    """Convert parsed entries into a mapping using the given strategy.

    document: Document dict as returned when parse_nyml(..., as_entries=True) or list of NYMLEntry
    strategy: 'last', 'first', or 'all'.
    """
    if isinstance(document, dict) and document.get('type') == 'document':
        entries = document['entries']
    else:
        # assume a list of entries (NYMLEntry or dict-like)
        entries = document

    def value_from_entry(e: Any):
        # e may be NYMLEntry or dict
        if isinstance(e, NYMLEntry):
            if e.children is not None:
                return to_mapping({ 'type': 'document', 'entries': [ _entry_to_dict(c) for c in e.children ] }, strategy)
            return e.value if e.value is not None else ''
        else:
            # dict-like entry
            if 'children' in e and e['children'] is not None:
                return to_mapping({ 'type': 'document', 'entries': e['children'] }, strategy)
            return e.get('value', '')

    result: Dict[str, Any] = {}
    for e in entries:
        key = e['key'] if isinstance(e, dict) else e.key
        val = value_from_entry(e)
        if strategy == 'all':
            if key not in result:
                result[key] = []
            result[key].append(val)
        elif strategy == 'first':
            if key not in result:
                result[key] = val
        else:  # last
            result[key] = val
    return result


def get_all(document: Any, key: str) -> List[Any]:
    """Return all values with the given key (search only top-level entries)."""
    if isinstance(document, dict) and document.get('type') == 'document':
        entries = document['entries']
    else:
        entries = document
    out = []
    for e in entries:
        en_key = e['key'] if isinstance(e, dict) else e.key
        if en_key == key:
            val = e['value'] if isinstance(e, NYMLEntry) else e.get('value', '')
            out.append(val)
    return out


def get_first(document: Any, key: str) -> Optional[Any]:
    vals = get_all(document, key)
    return vals[0] if vals else None


def get_last(document: Any, key: str) -> Optional[Any]:
    vals = get_all(document, key)
    return vals[-1] if vals else None