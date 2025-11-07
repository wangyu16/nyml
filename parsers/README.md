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

```python
from nyml_parser import parse_nyml

text = """
key: value
nested:
  child: data
"""

result = parse_nyml(text)
print(result)  # {'key': 'value', 'nested': {'child': 'data'}}
```

### Testing

```bash
cd parsers/python
source venv/bin/activate
pytest
```

## JavaScript Parser

Located in `parsers/javascript/`.

### Installation

```bash
cd parsers/javascript
npm install
```

### Usage

```javascript
const { parseNyml } = require('./nyml-parser');

const text = `
key: value
nested:
  child: data
`;

const result = parseNyml(text);
console.log(result);  // { key: 'value', nested: { child: 'data' } }
```

### Testing

```bash
cd parsers/javascript
npm test
```

## Development Notes

- Both parsers implement the same algorithm from `constructionNotes/parsingLogic.md`
- All values are parsed as strings
- Indentation uses spaces (tabs not allowed)
- Supports nested objects, comments, quoted keys, and multiline strings