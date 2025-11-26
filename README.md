# Not YAML

---

The basic idea of NYML is to define a simple, human-readable key-value format, similar to yaml but even simpler.

- Use indent to show parent/child relationships.
- Everything after the key is considered the value, unless it's a multiline string.
- Everything below the key with more indent is considered the multiline value to the key.

## 1. The Logic Rules

1. **Indentation:** Use spaces (not tabs) to show nesting.
2. **Data:** The format is `key: value` pairs. All values are parsed as strings.
3. **Comments:** A line is a comment if its first non-space character is a `#`. This rule does **not** apply inside a multiline string.
4. **Single-Line:** The value is **everything** after the first colon (`:`) (whitespace is trimmed).
5. **Quoted Keys:** Use `"` to create keys that contain a colon (e.g., `"http:key"`).
6. **Multiline:** `key: |` starts a multiline string. The value includes all subsequent lines that are **more indented** than the key. The block **ends** on the first line indented less than or equal to the key.

---

## 2. Scenarios Explained

### Rule 1: Indentation (Nesting)

You create nested objects (like in JSON) by indenting key-value pairs under a parent key. You **must** use spaces, not tabs.

```nyml
parent:
  child_key: value
```

This is parsed as:

```json
{ "parent": { "child_key": "value" } }
```

### Rule 2: Data (Keys & Values)

All values are treated as strings, even if they look like numbers or booleans.

```nyml
port: 8080
active: true
```

This is parsed as:

```json
{ "port": "8080", "active": "true" }
```

### Rule 3: Comments

The parser checks for comments **first**. If a line's first non-whitespace character is a `#`, the entire line is ignored. This rule is suspended inside a multiline block.

```nyml
# This entire line is a comment.
  # This indented comment is also ignored.

# The value for 'message' will be "hello # world"
message: hello # world
```

### Rule 4: Single-Line Values

If a line is not a comment, the parser splits it at the **first colon (`:`)**. The key and value are trimmed of surrounding whitespace.

```nyml
my key  :   This is the value.
```

This is parsed as:

```json
{ "my key": "This is the value." }
```

### Rule 5: Quoted Keys

If a key needs to contain a colon (`:`), you must enclose the key in double quotes (`"`).

```nyml
"http://example.com": "A URL"
"user:id": "12345"
```

This is parsed as:

```json
{ "http://example.com": "A URL", "user:id": "12345" }
```

### Rule 6: Multiline String Values

This rule is for storing large blocks of text, like markdown or code.

- **Trigger:** The line must be `key: |`.
- **Value Content:** The value begins on the _next line_. Every subsequent line is part of the string **as long as it is indented more** than the `key: |` line.
- **Termination:** The block **stops** on the very first line encountered with indentation **less than or equal to** the `key: |` line.
- **Dedent (Trimming):** The parser finds the indentation of the _first_ line of content (e.g., 2 spaces) and strips that exact amount from _every_ line in the block. If a line has more indentation, the extra spaces are kept.

---

## 3. Comprehensive Example

### Example Input File (`config.txt`)

```nyml
# Main configuration for the application
# All values will be parsed as strings.

app_name: "My App"
version: 1.2

# Server settings can be nested
server:
  # Host and port (this is a comment)
  host: localhost
  port: 8080

  # The value here includes the hash
  status_message: "OK # (production)"

# Use quoted keys for special characters
"http:routes": "/api/v1"
"user:admin": "admin-user"

# This multiline block contains markdown
# and demonstrates indentation handling.
welcome_message: |
  # This is NOT a comment.
  # It is the first line of the string.

  This is the main welcome message.

  Please see the following:
    * List item 1
    * List item 2
      * A nested item

  A line with a # is just text.

# This comment is outside the block.
# The multiline block ended on the line above.
logging:
  level: info
```

### Expected Output (as JSON)

```json
{
  "app_name": "My App",
  "version": "1.2",
  "server": {
    "host": "localhost",
    "port": "8080",
    "status_message": "OK # (production)"
  },
  "http:routes": "/api/v1",
  "user:admin": "admin-user",
  "welcome_message": "# This is NOT a comment.\n# It is the first line of the string.\n\nThis is the main welcome message.\n\nPlease see the following:\n  * List item 1\n  * List item 2\n    * A nested item\n\nA line with a # is just text.\n",
  "logging": {
    "level": "info"
  }
}
```

---

## 4. JSON Conversion Notes

NYML is designed on purpose to make human reading and editing very simple and is able to convert into JSON and back easily. However, not all features of JSON are supported. One important aspect is that only string type values are allowed, and array, number, boolean, and null types are not supported. But within the design scope, NYML and JSON can be converted perfectly from one to the other.

### Array Handling

NYML does not have native support for arrays. When converting JSON to NYML:

- **JSON arrays** are converted to **multiline strings** (one item per line)
- **Roundtrip conversion** (JSON → NYML → JSON) will convert arrays to multiline strings
- This is by design - NYML prioritizes human readability over complex data structures

**Example:**

```json
{
  "items": ["item1", "item2", "item3"]
}
```

Converts to:

```nyml
items: |
  item1
  item2
  item3
```

When parsed back to JSON:

```json
{
  "items": "item1\nitem2\nitem3\n"
}
```

### Available Converters

- **NYML to JSON**: `parsers/python/nyml_parser/parser.py` and `parsers/javascript/nyml-parser.js`
- **JSON to NYML**: `examples/convert_json_to_nyml.py` and `examples/convert_json_to_nyml.js`

### Other Conversion Issues

**Type Loss:** NYML treats all values as strings. JSON types are converted to their string representations:

- Numbers: `42` → `"42"`
- Booleans: `true` → `"true"` (or `"True"` in Python)
- Null: `null` → `"null"` (or `"None"` in Python)

**Comment Loss:** NYML comments are not preserved when converting to JSON.

**Special Characters in Strings:** Strings containing newlines (`\n`) or tabs (`\t`) are converted to multiline format in NYML.

**Unicode Handling:** Unicode characters are preserved but may be escaped in JSON output.

**Empty Values:** Empty objects work correctly, but empty arrays become empty multiline strings.

**Key Ordering:** Object key insertion order is preserved during conversion.

**Duplicates & Order Preservation:** NYML parsers now provide an option to return the parsed document as a sequence of ordered entries that preserves field order and allows duplicate keys. This is especially useful when you want to:

- Keep every occurrence of a repeated key (for example, configuration overlays, multiple settings with same key)
- Preserve the exact source ordering for roundtrip or audit purposes

The default `parse_nyml()` behavior remains compatible with earlier versions (returns a mapping where the last occurrence wins). Use `as_entries=True` (Python) or `{ asEntries: true }` (JS) to obtain the full ordered entries representation.

### Entries model

The entries model returns a document with the following shape:

```json
{
  "type": "document",
  "entries": [
    { "key": "a", "value": "1", "line": 1, "indent": 0 },
    { "key": "a", "value": "2", "line": 2, "indent": 0 },
    { "key": "b", "children": [{ "key": "c", "value": "3" }] }
  ]
}
```

Each entry includes optional metadata: `quoted_key`, `line`, `indent`, and `raw` (original raw line), plus either `value` or `children` (for nested blocks).

### Helpers & Strategies

To convert the entries representation back into a plain mapping, use `to_mapping()` with a duplicate-resolution strategy:

- `strategy='last'` (default): last occurrence wins
- `strategy='first'`: first occurrence wins
- `strategy='all'`: values for duplicated keys are collected into arrays

Examples:

```python
from nyml_parser import parse_nyml, to_mapping
doc = parse_nyml(text, as_entries=True)
print(to_mapping(doc, strategy='last'))
print(to_mapping(doc, strategy='all'))
```

```javascript
const { parseNyml, toMapping } = require("./parsers/javascript/nyml-parser");
const doc = parseNyml(text, { asEntries: true });
console.log(toMapping(doc, "last"));
console.log(toMapping(doc, "all"));
```

### Migration Note

Existing code that expects `parse_nyml(text)` to return a dictionary will continue to work by default. If you opt into `as_entries`, update your code to either:

- consume the `entries` array directly (recommended for full fidelity), or
- convert to a mapping using `to_mapping()` with an appropriate duplicate strategy.

**Large Numbers:** Precision is maintained as strings, avoiding floating-point issues.
