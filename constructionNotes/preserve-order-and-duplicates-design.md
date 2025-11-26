# Preserve Field Order & Allow Duplicated Fields — Design

## Overview

This document explains the design and implementation plan for updating the NYML parsers (Python and JavaScript) to preserve the order of fields and allow duplicate fields. The major change is to move from a mapping-based internal model to an ordered sequence of entries that captures all input information (keys, values, nested structure, and metadata). This preserves input order and duplicates, and allows structured views that include all original data.

This document outlines the data model, parser changes, API changes, tests, migration guidance, and example usage for both languages. It also mentions edge cases, performance considerations, and next steps.

---

## Goals

- Preserve field insertion order exactly as in the NYML source.
- Allow duplicate keys at the same or different nest levels without overwriting prior values.
- Preserve source metadata (line numbers, indentation, quoted keys) to support roundtrips and debugging.
- Provide utility helpers to convert entries into more convenient representations (mapping, first/last/all strategies), keeping them backward-compatible.
- Keep API surface intuitive and provide a migration path for existing consumers.

---

## Key Design Decisions

- Use an Ordered/Sequence model (Document with list of `Entry` nodes) as the canonical representation for parsed NYML.
- Maintain `as_entries` mode (configurable): parsers may return the old mapping for compatibility, but the default or recommended usage is to work with `entries` for preservation.
- Add helpers `to_mapping(strategy='last')` and `to_metadata(entries)` for convenience.
- Keep the parse algorithm line-oriented and streaming-friendly.

---

## Data Model

The canonical representation will be a `Document` composed of an ordered list of `Entry` nodes.

Entry schema (JSON-like):

```
Entry {
  key: string,
  value?: string,         // defined for simple key: value pairs or collected multiline string
  children?: Entry[],     // present for nested objects
  quoted_key?: bool,      // true if key was explicitly quoted in source
  line?: number,          // source line number where entry begins
  indent?: number,        // absolute leading space count
  raw?: string,           // original raw line (optional)
}

Document { type: 'document', entries: Entry[] }
```

Notes:

- A value is a string only. If `children` is present, `value` may be absent or null.
- Duplicated keys are represented as separate `Entry` objects, in the input order.
- The `children` property is also an ordered sequence and may contain duplicate keys.

Example:

```
{
  "type": "document",
  "entries": [
    {"key":"x","value":"1","line":1},
    {"key":"x","value":"2","line":2},
    {"key":"y","children":[{"key":"z","value":"3"}],"line":3}
  ]
}
```

---

## Parser Algorithm Changes

The high-level parser remains a streaming line-based algorithm computing `indent` and parsing each line. The key changes are how we store parsed results:

1. Replace `dict` parent containers with an `entries` list container in both Python and JavaScript:
   - Each stack frame will reference an `entries` list and its indent level.
2. When creating a new key entry:
   - Construct an `Entry` object and append it to the current parent's `entries` list.
   - If the entry has nested children (key followed by an indented block), set `children` = [] and push the new `children` list onto the stack with its indent level.
3. Do not collapse repeated keys; always append duplicate `Entry` nodes.
4. For `key: |` multiline blocks:
   - Create an `Entry` object with `value` set to the collected string when multiline ends (preserving blanks exactly).
5. Preserve metadata:
   - Store `line`, `indent`, `quoted_key`, and optionally `raw` for possible roundtrips and diagnostics.
6. Maintain backward compatibility by providing a `to_mapping()` helper that will merge entries using an explicit strategy (first, last, all as array) if the user requests a map.

### Pseudocode (high level)

```
root = { type: 'document', entries: [] }
stack = [(root.entries, 0)]
for each line:
  indent = leading_spaces(line)
  if in multiline: collect until dedent
  if blank or comment -> skip
  parent_entries = find_parent_for_indent(stack, indent)
  parse key, optional value
  entry = Entry(key=key, value=value, line=i, indent=indent, quoted_key=quoted)
  parent_entries.append(entry)
  if value == '' (object):
    entry.children = []
    stack.append((entry.children, indent))
```

This algorithm keeps the parser complexity O(lines) and is robust for streaming consumption.

---

## API Changes & Helpers

Add optional return or flag to `parse_nyml`:

```
parse_nyml(text: str, *, as_entries: bool = False) -> Union[Dict, Document]
```

- Default remains backward-compatible (`as_entries=False`) unless you choose to flip default.

New utilities (both languages):

- `to_mapping(entries, strategy='last'|'first'|'all')` — converts the ordered entries list into a mapping with chosen duplicate resolution; `all` stores values as arrays.
- `get_all(entries, key_path=None)` — returns list of all matched values, preserving order, with ability to search nested entries by key or path.
- `get_first(entries, key)` and `get_last(entries, key)` for single-value access.
- `to_json_document(entries)` — transforms Document to a JSON object preserving duplicates as entries array structure.

Compatibility helpers:

- `as_map = to_mapping(document.entries, strategy='last')` will allow existing clients to get old dict behavior.

---

## Tests

Update and add tests to cover the following:

- Duplicate keys at the same depth: ensure both entries are preserved in order (assert `entries` list size and content).
- Duplicate keys across different depths: ensure nested duplicates are preserved and do not conflict.
- `to_mapping()` strategies: `first`, `last`, `all` should produce correct mappings.
- Roundtrip stability: `NYML -> entries -> NYML` should preserve textual content and order.
- Parameterized tests to check `as_entries=True` and `as_entries=False` outputs for compatibility.

Add new test files for both Python (pytest) and JavaScript (Jest). Keep the old tests that assert mapping outputs (when `as_entries=False`) so backward compatibility continues.

---

## Migration & Compatibility Plan

To ensure smooth migration:

1. Preserve the behavior of `parse_nyml()` unless `as_entries=True` is requested (or toggled by default after a deprecation period).
2. Provide `to_mapping()` utility to convert entries into old mapping when needed.
3. Document upgrade steps in `README.md` and `parsingLogic.md`.
4. Add a deprecation notice and sample migration code:

```
# Python
doc = parse_nyml(text, as_entries=True)
# convert to legacy dict
legacy = to_mapping(doc.entries, strategy='last')
# or keep doc.entries for full fidelity
```

---

## Example

NYML input (with duplicates & order):

```
a: 1
b: 2
a: 3
b:
  c: 4
  b: 5
```

`entries` representation:

```
entries: [
  { key: 'a', value: '1' },
  { key: 'b', value: '2' },
  { key: 'a', value: '3' },
  { key: 'b', children: [ { key: 'c', value: '4' }, { key: 'b', value: '5' } ] }
]
```

`tapping legacy mapping` with `strategy='last'` will return `{ a: '3', b: { c: '4', b: '5' } }` while `strategy='all'` will return arrays where duplicates exist.

---

## Implementation Plan & Steps (Actionable)

1. Update the Python parser (`parsers/python/nyml_parser/parser.py`):

   - Replace `dict` container usage with `entries` list.
   - Update stack frames to track `(entries, indent)` instead of `(obj, indent)`.
   - Add `Entry` data class.
   - Implement `to_mapping()` and helper methods.
   - Update Python tests and add new tests for duplicates and order.

2. Update JavaScript parser (`parsers/javascript/nyml-parser.js`):

   - Mirror the Python changes in JS (entries arrays and stack frames).
   - Provide `parseNyml(..., { asEntries: true })` option and helpers.
   - Update tests.

3. Documentation & README updates:

   - Document the new default behavior/flag and usage examples.
   - Add migration guide and sample code.

4. Testing & Validation:

   - Ensure old tests still pass for `as_entries=False`.
   - Add new unit tests for `as_entries=True` expected behaviour.
   - Run JS and Python test suites, ensure roundtrip tests succeed.

5. Release & Deprecation:
   - Provide a deprecation period (if changing default) to allow users to adjust.
   - Add a migration note to README and release notes.

---

## Edge Cases & Notes

- Memory usage: the `entries` model stores more metadata and may consume more memory for large files, but NYML is primarily a config format so typical files are small.
- Streaming: It remains possible to expose streaming hooks (e.g., emit entries as they are parsed) to enable incremental processing.
- JSON conversion: JSON cannot directly encode duplicate object keys—`to_mapping()` must use arrays or strategies; `to_json_document()` should retain entries as `entries` array to avoid data loss.

---

## Next Steps

1. Implement the Python parser changes and tests (recommended first pass). The Python implementation is typically easier to iterate and test.
2. Implement the JS parser changes to match the behavior.
3. Update README and `parsingLogic.md` with detailed examples and the migration guide.
4. Release and communicate the change to users.

---

If you would like, I can proceed now to implement the changes in the Python parser as a first pass, including tests and README changes. Or, as you chose previously, I can implement both Python and JS changes in tandem, including tests and Docs (the second option). Which would you like me to start next?
