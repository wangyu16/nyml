# NYML Parsers

This directory contains implementations of NYML parsers in multiple languages.

## Python Parser

Located in `parsers/python/`.

### Installation

```bash
cd parsers/python
source venv/bin/activate
pip install -e .
```

### Usage

````python
from nyml_parser import parse_nyml

text = """
key: value
nested:
  child: data
"""

result = parse_nyml(text)
print(result)  # {'key': 'value', 'nested': {'child': 'data'}}

### Preserving Order and Duplicates (New)

You can parse NYML into an ordered entries representation that preserves duplicate keys and the source order:

```python
from nyml_parser import parse_nyml, to_mapping

text = """
a: 1
b: 2
a: 3
"""
# return ordered entries (document form)
doc = parse_nyml(text, as_entries=True)
print(doc['entries'])

# convert to mapping with a strategy (last/first/all)
map_last = to_mapping(doc, strategy='last')
map_all = to_mapping(doc, strategy='all')
print(map_last)  # {'a': '3', 'b': '2'}
print(map_all)   # {'a': ['1','3'], 'b': ['2']}
````

````

### Converting JSON to NYML

```python
# Python
from convert_json_to_nyml import json_to_nyml
import json

data = {"key": "value", "nested": {"child": "data"}}
lines = json_to_nyml(data)
print('\n'.join(lines))
````

```javascript
// JavaScript
const { jsonToNyml } = require("./convert_json_to_nyml");

const data = { key: "value", nested: { child: "data" } };
const lines = jsonToNyml(data);
console.log(lines.join("\n"));
```

## Development Notes

- Both parsers implement the same algorithm from `constructionNotes/parsingLogic.md`
- All values are parsed as strings
- Indentation uses spaces (tabs not allowed)
- Supports nested objects, comments, quoted keys, and multiline strings
- Arrays in JSON are converted to multiline strings in NYML
- Multiline strings in JSON are converted back to `|` syntax in NYML
