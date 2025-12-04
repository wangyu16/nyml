"""NYML V2 Parser implementation.

V2 introduces list-based output where:
- Root is always a list of entries
- Multi-value fields create nested lists
- Mixed content (strings + key/value pairs) is supported
- No comments (# is allowed in values)
"""

from typing import Any, List, Optional, Union


class ParseError(Exception):
    """Exception raised for parsing errors."""

    def __init__(self, code: str, message: str, line: int, column: Optional[int] = None):
        self.code = code
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"Line {line}: {message}")


def _leading_spaces(s: str) -> int:
    """Count leading spaces in a string."""
    return len(s) - len(s.lstrip(' '))


def _parse_key_value(stripped: str) -> tuple[Optional[str], Optional[str]]:
    """
    Parse a stripped line into (key, value) tuple.
    
    Returns (None, None) if no colon found (plain string).
    Returns (key, "") if colon found but no value.
    Returns (key, value) for normal key:value pairs.
    Returns (key, "|") for multiline marker.
    """
    if not stripped:
        return None, None
    
    # Handle quoted keys
    if stripped.startswith('"'):
        end = stripped.find('"', 1)
        if end == -1:
            # Unmatched quote - treat as plain string
            return None, None
        key = stripped[1:end]
        rest = stripped[end + 1:].lstrip()
        if not rest.startswith(':'):
            # No colon after quoted key - treat as plain string
            return None, None
        value = rest[1:].strip()
        return key, value
    
    # Regular key:value
    idx = stripped.find(':')
    if idx == -1:
        return None, None
    
    key = stripped[:idx].strip()
    value = stripped[idx + 1:].strip()
    return key, value


def _collect_multiline(lines: List[str], start_idx: int, base_indent: int) -> tuple[str, int]:
    """
    Collect multiline string content starting from start_idx + 1.
    
    Returns (content, next_index) where next_index is the first line
    not part of the multiline block.
    """
    raw_lines: List[str] = []
    i = start_idx + 1
    
    while i < len(lines):
        line = lines[i]
        indent = _leading_spaces(line)
        
        # Empty lines are included in multiline content
        if line.strip() == '':
            raw_lines.append('')
            i += 1
            continue
        
        # Line with less or equal indent ends the block
        if indent <= base_indent:
            break
        
        raw_lines.append(line)
        i += 1
    
    # Dedent: find minimum indent among non-blank lines
    nonblank = [r for r in raw_lines if r.strip() != '']
    if nonblank:
        min_indent = min(_leading_spaces(r) for r in nonblank)
    else:
        min_indent = 0
    
    # Apply dedent
    pieces: List[str] = []
    for r in raw_lines:
        if r.strip() == '':
            pieces.append('')
        else:
            pieces.append(r[min_indent:])
    
    # Collapse multiple trailing blank lines
    while len(pieces) >= 2 and pieces[-1] == '' and pieces[-2] == '':
        pieces.pop()
    
    # Build content with trailing newline
    if pieces and pieces[-1] == '':
        content = '\n'.join(pieces)
    else:
        content = '\n'.join(pieces) + '\n' if pieces else ''
    
    return content, i


def parse_nyml_v2(text: str) -> List[Any]:
    """
    Parse NYML V2 text into a list structure.
    
    Args:
        text: The NYML V2 content to parse
    
    Returns:
        A list representing the parsed data. Each element is either:
        - A dict with a single key-value pair: {"key": "value"}
        - A dict with a key and list value: {"key": [...]}
        - A plain string (in multi-value contexts)
    
    Raises:
        ParseError: If parsing fails
    """
    lines = text.splitlines()
    result: List[Any] = []
    
    # Stack of (container, base_indent)
    # container is a list that receives new items
    stack: List[tuple[List[Any], int]] = [(result, -1)]
    
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            i += 1
            continue
        
        indent = _leading_spaces(line)
        
        # Pop stack to find correct parent based on indent
        while len(stack) > 1 and indent <= stack[-1][1]:
            stack.pop()
        
        parent, parent_indent = stack[-1]
        
        # Parse the line
        key, value = _parse_key_value(stripped)
        
        if key is None:
            # No colon found - plain string
            if len(stack) > 1:
                # Inside a multi-value context: add as plain string
                parent.append(stripped)
            # At root level: ignore (Rule 9)
            i += 1
            continue
        
        if value == '|':
            # Multiline string
            content, i = _collect_multiline(lines, i, indent)
            parent.append({key: content})
            continue
        
        if value == '':
            # Multi-value field: create a list for children
            new_list: List[Any] = []
            parent.append({key: new_list})
            stack.append((new_list, indent))
            i += 1
            continue
        
        # Single-line key:value
        parent.append({key: value})
        i += 1
    
    return result


def serialize_nyml_v2(data: List[Any], indent: int = 0) -> str:
    """
    Serialize a V2 data structure back to NYML format.
    
    Args:
        data: List structure as returned by parse_nyml_v2()
        indent: Current indentation level (spaces)
    
    Returns:
        NYML formatted string
    """
    lines: List[str] = []
    prefix = ' ' * indent
    
    for item in data:
        if isinstance(item, str):
            # Plain string in multi-value context
            lines.append(f"{prefix}{item}")
        elif isinstance(item, dict):
            # Should have exactly one key
            for key, value in item.items():
                # Check if key needs quoting
                quoted_key = f'"{key}"' if ':' in key else key
                
                if isinstance(value, list):
                    # Multi-value field
                    lines.append(f"{prefix}{quoted_key}:")
                    lines.append(serialize_nyml_v2(value, indent + 2))
                elif isinstance(value, str) and '\n' in value:
                    # Multiline string
                    lines.append(f"{prefix}{quoted_key}: |")
                    for vline in value.rstrip('\n').split('\n'):
                        lines.append(f"{prefix}  {vline}")
                else:
                    # Single-line value
                    lines.append(f"{prefix}{quoted_key}: {value}")
    
    return '\n'.join(lines)
