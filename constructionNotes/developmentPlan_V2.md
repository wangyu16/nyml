# NYML V2 Parser Development Plan

## Overview

This document outlines the development plan for NYML V2 parsers in Python and JavaScript. V2 introduces significant changes from V1, primarily the list-based output structure.

## Key Changes from V1

1. **Root is always a list** - All root-level entries become list items
2. **Multi-value fields** - `key:` + newline creates a list of values
3. **No comments** - `#` is allowed in values
4. **Mixed content lists** - Lists can contain strings and key/value pairs

## V2 Parsing Rules Summary

| Rule                 | Syntax                            | Result                         |
| -------------------- | --------------------------------- | ------------------------------ |
| Single-line          | `key: value`                      | `{"key": "value"}`             |
| Multiline            | `key: \|` + indented content      | `{"key": "multiline\nstring"}` |
| Multi-value          | `key:` + newline + indented items | `{"key": [...]}`               |
| Plain string in list | indented text without `:`         | `"text"`                       |
| Key/value in list    | indented `key: value`             | `{"key": "value"}`             |

## Parsing Algorithm

### High-Level Algorithm

```
1. Initialize result = []
2. For each line:
   a. Skip empty lines (except in multiline mode)
   b. Skip lines without colons at root level (Rule 9)
   c. Calculate indent level
   d. Parse key and value
   e. If value is "|" -> enter multiline mode
   f. If value is empty -> enter multi-value mode
   g. Otherwise -> add {key: value} to current context
3. Return result list
```

### State Machine

```
States:
- NORMAL: Processing regular key:value pairs
- MULTILINE: Collecting multiline string content
- MULTIVALUE: Collecting list items

Transitions:
- NORMAL + "key: |" -> MULTILINE
- NORMAL + "key:" (empty value) -> MULTIVALUE
- MULTILINE + less/equal indent -> NORMAL
- MULTIVALUE + less/equal indent -> NORMAL
```

### Pseudocode

```python
def parse_nyml_v2(text: str) -> list:
    lines = text.splitlines()
    result = []
    stack = [(result, -1)]  # (container, indent)

    i = 0
    while i < len(lines):
        line = lines[i]
        indent = count_leading_spaces(line)
        stripped = line.strip()

        # Skip empty lines in normal mode
        if not stripped:
            i += 1
            continue

        # Pop stack to find correct parent
        while len(stack) > 1 and indent <= stack[-1][1]:
            stack.pop()

        parent, parent_indent = stack[-1]

        # Check if line has a colon (key:value or key:)
        key, value = parse_key_value(stripped)

        if key is None:
            # No colon found - plain string in multi-value context
            if isinstance(parent, list):
                parent.append(stripped)
            # At root level, ignore (Rule 9)
            i += 1
            continue

        if value == '|':
            # Multiline string
            content, i = collect_multiline(lines, i, indent)
            parent.append({key: content})
        elif value == '':
            # Multi-value field - create list
            new_list = []
            parent.append({key: new_list})
            stack.append((new_list, indent))
            i += 1
        else:
            # Single-line value
            parent.append({key: value})
            i += 1

    return result
```

## Test Cases

### Basic Tests

1. **Empty input** -> `[]`
2. **Single key-value** -> `[{"key": "value"}]`
3. **Multiple key-values** -> `[{"a": "1"}, {"b": "2"}]`
4. **Duplicate keys** -> `[{"a": "1"}, {"a": "2"}]`

### Multi-Value Tests

5. **Plain strings** -> `[{"items": ["a", "b", "c"]}]`
6. **Key-value pairs** -> `[{"items": [{"x": "1"}, {"y": "2"}]}]`
7. **Mixed content** -> `[{"items": ["a", {"x": "1"}, "b"]}]`
8. **Nested multi-value** -> `[{"outer": [{"inner": ["a", "b"]}]}]`
9. **Single item** -> `[{"item": ["only"]}]`

### Multiline Tests

10. **Basic multiline** -> `[{"text": "line1\nline2\n"}]`
11. **Multiline with empty lines** -> preserved
12. **Multiline with code block** -> preserved with indentation
13. **Multiline dedent** -> leading spaces trimmed uniformly

### Edge Cases

14. **Quoted keys** -> `[{"http:url": "value"}]`
15. **Value with colons** -> `[{"key": "a:b:c"}]`
16. **Hash in value** -> `[{"key": "#comment"}]`
17. **Root plain strings ignored** -> only key:value pairs captured
18. **Deeply nested** -> multiple levels of nesting

### Roundtrip Tests

19. **Parse -> Serialize -> Parse** yields identical result
20. **All examples from spec** produce expected output

## Implementation Phases

### Phase 1: Python Parser (Core)

1. Create `parsers/python/nyml_parser/parser_v2.py`
2. Implement `parse_nyml_v2()` function
3. Implement helper functions:
   - `count_leading_spaces()`
   - `parse_key_value()`
   - `collect_multiline()`
4. Add `ParseError` exception class

### Phase 2: Python Tests

1. Create `parsers/python/tests/test_parser_v2.py`
2. Implement all test cases from above
3. Add spec example tests
4. Run and verify all pass

### Phase 3: JavaScript Parser

1. Create `parsers/javascript/nyml-parser-v2.js`
2. Port Python implementation
3. Match API: `parseNymlV2(text) -> array`

### Phase 4: JavaScript Tests

1. Create `parsers/javascript/__tests__/nyml-parser-v2.test.js`
2. Mirror Python test cases
3. Run with Jest

### Phase 5: Serializer (NYML -> JSON -> NYML)

1. Implement `serialize_nyml_v2()` in both languages
2. Test roundtrip guarantee

### Phase 6: Integration

1. Update `__init__.py` to export V2 functions
2. Update CLI tools for V2
3. Create V2 example files
4. Update documentation

## File Structure

```
parsers/
  python/
    nyml_parser/
      __init__.py        # Update exports
      parser.py          # V1 (keep)
      parser_v2.py       # NEW: V2 parser
    tests/
      test_parser.py     # V1 tests (keep)
      test_parser_v2.py  # NEW: V2 tests
  javascript/
    nyml-parser.js       # V1 (keep)
    nyml-parser-v2.js    # NEW: V2 parser
    __tests__/
      nyml-parser.test.js      # V1 tests (keep)
      nyml-parser-v2.test.js   # NEW: V2 tests
```

## Success Criteria

1. All test cases pass in both languages
2. Both parsers produce identical JSON output
3. All spec examples produce expected results
4. Roundtrip (parse -> serialize -> parse) preserves data
5. Clear error messages for invalid input
