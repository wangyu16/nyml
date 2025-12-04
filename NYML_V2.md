This is an extensive change to previous version of NYML.

The basic idea of NYML is to define a simple, human-readable key-value format, similar to yaml but even simpler.

- Use indent to show parent/child relationships.
- All end level values are strings.
- For a single line key value pair, everything after the `key: ` is considered the value.
- To include multiline values, use the syntax `key: |`. Everything below the `key: |` with more indent is considered the multiline value to the key.

Key differences from previous version:

- All fields at the same level are converted to a list by default. Thus, the root becomes a list of entries. Sibling keys become list items. The previous version does not support list.
- Values to a key at the same level are converted to a list as well.
- Acceptable values are: a string, a list of strings, a list of key/value pairs and strings.

Planned usage:

- Use within a NYML plugin that is embedded in markdown file.
- Use customized markdown parser to render the markdown file with plugins.
- The end level values are parsed as raw markdown, and output as inline or block html elements with labels assembled, such as `<strong>`, `<span>`, `<div>`, `<img>`, etc.
- The NYML block will be returned as a `<div>` element with the extracted JSON object embedded in `<script>`. This `<div>` element would be invisible if the rendered HTML is loaded in a browser directly. The client side will extract the information embedded in the JSON object and inject visible structured elements into the `<div>`.
- NYML blocks are typically short, or with repeating entries, comments inside is not necessary. Instructions can be added outside the NYML blocks.

## 1. The Logic Rules

1. **Indentation:** Use spaces (not tabs) to show nesting.
2. **Data:** The format is `key: value` pairs. All end level values are parsed as strings.
3. **Comments:** Do not accept comments, so a string starting with `#` can be used as a value.
4. **Single-Line:** The value is **everything** after the first colon (`:`) (whitespace is trimmed).
5. **Quoted Keys:** Use `"` to create keys that contain a colon (e.g., `"http:key"`).
6. **Multiline:** `key: |` followed by a new line starts a multiline string. The value includes all subsequent lines that are **more indented** than the key, including empty lines. The block **ends** on the first line indented less than or equal to the key. The multiline string indents are trimmed the same way as in V1, thus markdown syntax with intentional indents will be preserved.
7. **Multi Values:** `key:` followed by a new line starts a multi-value field. The values must be indented more than the key, and all values at the same level must have the same indent. Each value can be either a single-line string or a child key/value pair. Empty lines are ignored.
8. All fields at the same level are parsed into a list.
9. Root-level plain strings without colons are ignored. This can be used for comments, but is not recommended.

## Parsing criteria

- A NYML file must be able to parse into a JSON object and then back to the original identical NYML format (information must be preserved, though actual structure can vary if they have identical meaning).
- An arbitrary JSON object can be parsed into a NYML file, but when converted back to JSON format, the structure could be different.

## Examples

```
name: Alice
age: 25
```

results in `[{"name": "Alice"}, {"age": "25"}]`.

```
items:
  value1
  value2
  child: a
  child: b
```

results in `[{"items":["value1","value2",{"child": "a"},{"child": "b"}]}]`

```
items:
  value1
  child: a
  another plain value
```

becomes `[{"items": ["value1", {"child": "a"}, "another plain value"]}]`

````
markdown-example: |
  # Head
  This is a markdown example with a code block
  ```python
  if temperature > 30:
      print("It's a hot day!")
  elif temperature > 20:
      print("It's a pleasant day.")
  else:
      print("It's a bit chilly.")
````

```


This results in a single key/value pair, with `markdown-example` as the key and all the following lines as one multiline string value. Each line in the value will have its leading two spaces trimmed.

```

item:
only-one

```

results in a key with a single-item list as the value: `[{"item": ["only-one"]}]`. This becomes useful when you want to add something like

```

item:
only: one

```
which produces a key `item` with a single-item list containing a key/value pair: `[{"item": [{"only": "one"}]}]`. On the other hand,
```

item: only: one

```
treats `only: one` as a plain string value: `[{"item": "only: one"}]`.

```

outer:
inner:
a
b

```

results in `[{"outer": [{"inner": ["a", "b"]}]}]`
```
