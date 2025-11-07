# NYML Parsing Logic

## Overview

NYML (Not YAML) is a simple, human-readable key-value configuration format. Values are always strings and nesting is expressed by indentation using spaces (tabs are disallowed by default). This document corrects and clarifies the original parsing notes and provides a robust, implementable algorithm for both Python and JavaScript implementations.

## Key Concepts (clarified)

- Indentation: Uses spaces to denote nesting. The format compares absolute indentation counts (number of leading spaces); it does not assume a fixed "step" (2 or 4) unless a parser option enforces one.
- Key-Value Pairs: A single-line value uses `key: value` where the value is everything after the first colon (trimmed of surrounding whitespace).
- Comments: A line is a comment if its first non-space character is `#`. This rule is suspended when inside a multiline string block.
- Quoted Keys: Keys that include special characters (including `:`) may be wrapped in double quotes. The spec permits escaping `"` inside quoted keys.
- Multiline Strings: A line `key: |` signals that the value is a string block. The block contains subsequent lines that are more-indented than the `key: |` line. Blank lines inside the block are significant and preserved.
- Data Types: All values remain strings; there is no automatic type coercion.

## Design decisions and fixes

- Empty-line handling: Empty or whitespace-only lines are skipped only when not inside a multiline block. When collecting multiline content, preserve empty lines.
- Multiline vs nested object: `key: |` always yields a string value (the collected block). It does NOT create a nested object. By contrast, `key:` followed by more-indented `child: value` lines creates a nested object.
- Indentation handling: Track absolute indentation (number of leading spaces) on a stack of (object, indent) pairs. Do not hard-code a step value; instead, compare absolute indent counts to determine when to pop/push stack frames. Optionally, parsers may expose an `indentStep` option to enforce consistent steps.
- Dedent rule for multiline blocks: Use the minimum indentation found among content lines and strip this exact amount from every content line (similar to Python's textwrap.dedent). This is robust when content lines have a consistent baseline indent.
- Quoted keys: Accept `"` escapes inside quoted keys and raise a parse error for unmatched quotes.

## Parsing algorithm (high level)

1. Initialize:
   - root = {}
   - stack = [(root, 0)]  # pair of (object, indent)
   - multiline_state = None  # or { key, indent, content_lines }

2. For each line (preserve raw line for content):
   - Compute `indent = count_leading_spaces(line)`.
   - If `multiline_state` is active:
     - If the line is blank (all whitespace): append an empty string to content_lines.
     - Else if `indent` > `multiline_state.indent`: append the line substring after the multiline content baseline handling (store the raw line for later dedent).
     - Else: close the multiline block (process content_lines to create the final string) and continue processing the current line normally.
   - If not in multiline_state:
     - If line stripped is empty: skip it.
     - If line.lstrip().startswith('#'): skip it (comment).
     - Locate the appropriate parent object for this indent by popping stack while `indent` < top.indent.
     - Parse key:
       - If first non-space char is `"`, parse a quoted key allowing escaped quotes until the matching closing quote, then require a colon `:` afterwards.
       - Else, find the first colon `:` in the line; if none, raise MISSING_COLON parse error.
     - Extract `value_part` (everything after the first colon, trimmed left/right).
     - If `value_part` == `|` (exactly after trimming): enter multiline_state with { key, indent, content_lines = [] }.
     - Else if `value_part` is empty and the next non-blank, non-comment lines are more-indented keys/values: create an empty object for `key`, attach it to parent, and push (obj, indent_of_child) as new stack frame.
     - Else: assign `parent[key] = value_part`.

3. At EOF: if `multiline_state` is active, raise UNTERMINATED_MULTILINE error.

4. Return `root`.

## Corrected pseudocode (Python-style)

```python
def parse_nyml(text, *, allow_tabs=False, strict=False):
    def leading_spaces(s):
        return len(s) - len(s.lstrip(' '))

    lines = text.splitlines()
    root = {}
    # stack of (obj, indent)
    stack = [(root, 0)]

    multiline = None  # None or dict with keys: key, indent, raw_lines

    for i, raw in enumerate(lines, start=1):
        # raw includes trailing spaces; we use raw for content preservation
        indent = leading_spaces(raw)

        if multiline is not None:
            # We are collecting multiline block content.
            if raw.strip('') == '':
                multiline['raw_lines'].append('')
                continue
            if indent > multiline['indent']:
                # store the raw line (we will dedent later)
                multiline['raw_lines'].append(raw)
                continue
            else:
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
            # parse quoted key with simple escaping
            j = 1
            key_chars = []
            while j < len(stripped):
                ch = stripped[j]
                if ch == '\\' and j + 1 < len(stripped):
                    key_chars.append(stripped[j+1])
                    j += 2
                    continue
                if ch == '"':
                    j += 1
                    break
                key_chars.append(ch)
                j += 1
            else:
                raise ParseError('UNMATCHED_QUOTE', line=i)
            key = ''.join(key_chars)
            # now expect ':' after optional spaces
            rest = stripped[j:].lstrip()
            if not rest.startswith(':'):
                raise ParseError('MISSING_COLON', line=i)
            value_part = rest[1:].strip()
        else:
            idx = raw.find(':')
            if idx == -1:
                raise ParseError('MISSING_COLON', line=i)
            key = raw[:idx].rstrip()
            value_part = raw[idx+1:].strip()

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

    if multiline is not None:
        raise ParseError('UNTERMINATED_MULTILINE')

    return root
```

Notes:
- The Python pseudocode above is intentionally explicit rather than optimised. The important fixes are: 1) do not skip blank lines during multiline collection, 2) do not create an object for `key: |`, and 3) use absolute indent values on the stack.

## Errors and API (recommendation)

- Expose a single parse function that returns the nested dict/object. Example signatures:
  - Python: parse_nyml(text: str, *, strict: bool = False) -> dict
  - JavaScript/TypeScript: parseNyml(text: string, options?: { strict?: boolean }) => object
- Error shape: raise/throw a ParseError with fields: { code, message, line, column? }.
  - Codes to include: UNMATCHED_QUOTE, MISSING_COLON, UNTERMINATED_MULTILINE, BAD_INDENT

## Tests and edge cases to include

- Multiline blocks with blank lines preserved.
- Comments inside multiline blocks are treated as content, not comments.
- Quoted keys with colons and escaped quotes: `"user:id"` and `"a \"b\" c"`.
- Lines missing `:` should raise MISSING_COLON.
- Unclosed quoted key or unclosed multiline at EOF should raise appropriate errors.
- Deep nesting and mixed indentation widths (add a strict mode to error on inconsistent indent steps).

## Implementation tips (JS/Python)

- Keep parsing logic as a small line-based state machine. The same algorithm maps well to both languages.
- Use helper functions:
  - getIndent(line) -> number of leading spaces
  - parseQuotedKey(stripped_line) -> (key, rest)
  - collectMultiline(lines, start_index, base_indent) -> (content, next_index)
- Start by implementing a minimal parser and add unit tests for the comprehensive example in `README.md`.

## Example test cases (minimal)

- The comprehensive example from `README.md` -> verify JSON output matches expected.
- Quoted key with colon
- Multiline block with leading blank lines and nested indented bullets
- Error cases: missing colon, unmatched quote, unclosed multiline

---

If you want, I can now:
- Apply a small edit in this repository to update `parsingLogic.md` with the chosen pseudocode (done), or
- Implement a reference parser in Python and one in JavaScript with unit tests and include them in the repo.

Tell me which next step to take and I'll continue.