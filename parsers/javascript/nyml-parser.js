/**
 * NYML Parser - A simple configuration format parser
 * @module nyml-parser
 */

/**
 * Error thrown during NYML parsing
 */
class ParseError extends Error {
  /**
   * @param {string} code - Error code
   * @param {string} message - Error message
   * @param {number} line - Line number where error occurred
   * @param {number|null} column - Column number (optional)
   */
  constructor(code, message, line, column = null) {
    super(`Line ${line}: ${message}`);
    this.code = code;
    this.message = message;
    this.line = line;
    this.column = column;
    this.name = 'ParseError';
  }
}

/**
 * Count leading spaces in a string
 * @param {string} s - Input string
 * @returns {number} Number of leading spaces
 */
function leadingSpaces(s) {
  return s.length - s.trimStart().length;
}

/**
 * Parse NYML text into a nested object
 * @param {string} text - The NYML content to parse
 * @param {Object} options - Parsing options
 * @param {boolean} options.strict - If true, enforce consistent indentation steps
 * @returns {Object} Parsed nested object
 * @throws {ParseError} If parsing fails
 */
function parseNyml(text, options = {}) {
  const { strict = false, asEntries = false } = options;

  const lines = text.split('\n');
  // document entries root
  const rootEntries = [];
  // stack of [entriesList, indent]
  const stack = [[rootEntries, 0]];

  let multiline = null; // null or { key, indent, rawLines }

  for (let i = 0; i < lines.length; i++) {
    const raw = lines[i];
    const indent = leadingSpaces(raw);

  if (multiline !== null) {
    // Collecting multiline block content
    if (raw.trim() === '') {
      multiline.rawLines.push('');
      continue;
    }
    if (indent <= multiline.indent) {
      // Close multiline: compute content and assign
      // Find min indent among non-blank rawLines
      const nonblank = multiline.rawLines.filter(r => r.trim() !== '');
      let minIndent = 0;
      if (nonblank.length > 0) {
        minIndent = Math.min(...nonblank.map(r => leadingSpaces(r)));
      }
      const pieces = [];
      for (const r of multiline.rawLines) {
        if (r.trim() === '') {
          pieces.push('');
        } else {
          pieces.push(r.slice(minIndent));
        }
      }
      // collapse multiple trailing blank lines into a single one to match previous behavior
      while (pieces.length >= 2 && pieces[pieces.length - 1] === '' && pieces[pieces.length - 2] === '') {
        pieces.pop();
      }
      let content;
      if (pieces.length && pieces[pieces.length - 1] === '') {
        content = pieces.join('\n');
      } else {
        content = pieces.join('\n') + '\n';
      }
      const entry = multiline.entry;
      entry.value = content;
      multiline = null;
      // Fall through to process current line as normal
    } else {
      multiline.rawLines.push(raw);
      continue;
    }
  }    // Not in multiline state
    if (raw.trim() === '') {
      continue;
    }
    const stripped = raw.trimStart();
    if (stripped.startsWith('#')) {
      continue;
    }

    // Find parent for current indent
    while (stack.length > 0 && indent < stack[stack.length - 1][1]) {
      stack.pop();
    }
    const parentEntries = stack[stack.length - 1][0];

    // Parse key (handle quoted keys)
    let key, valuePart;
    if (stripped.startsWith('"')) {
      const end = stripped.indexOf('"', 1);
      if (end === -1) {
        throw new ParseError('UNMATCHED_QUOTE', 'Unmatched quote in key', i + 1);
      }
      key = stripped.slice(1, end);
      const rest = stripped.slice(end + 1).trimStart();
      if (!rest.startsWith(':')) {
        throw new ParseError('MISSING_COLON', 'Missing colon after quoted key', i + 1);
      }
      valuePart = rest.slice(1).trim();
      // Keep value as-is (do not remove surrounding quotes)
    } else {
      const idx = raw.indexOf(':');
      if (idx === -1) {
        throw new ParseError('MISSING_COLON', 'Missing colon in key-value pair', i + 1);
      }
      key = raw.slice(0, idx).trim();
      valuePart = raw.slice(idx + 1).trim();
      // Keep value as-is (do not remove surrounding quotes)
    }

    const entry = { key, quoted_key: stripped.startsWith('"'), line: i + 1, indent, raw };
    parentEntries.push(entry);
    if (valuePart === '|') {
      // Start multiline collection
      multiline = { entry, indent, rawLines: [] };
      continue;
    }

    // Keep value as-is

    // If valuePart is empty, it might be an object if following lines are more-indented
    if (valuePart === '') {
      entry.children = [];
      stack.push([entry.children, indent + 1]);
    } else {
      entry.value = valuePart;
    }
  }

  if (multiline !== null) {
    // Close multiline at EOF
    const nonblank = multiline.rawLines.filter(r => r.trim() !== '');
    let minIndent = 0;
    if (nonblank.length > 0) {
      minIndent = Math.min(...nonblank.map(r => leadingSpaces(r)));
    }
    const pieces = [];
    for (const r of multiline.rawLines) {
      if (r.trim() === '') {
        pieces.push('');
      } else {
        pieces.push(r.slice(minIndent));
      }
    }
    while (pieces.length >= 2 && pieces[pieces.length - 1] === '' && pieces[pieces.length - 2] === '') {
      pieces.pop();
    }
    let content;
    if (pieces.length && pieces[pieces.length - 1] === '') {
      content = pieces.join('\n');
    } else {
      content = pieces.join('\n') + '\n';
    }
    const entry = multiline.entry;
    entry.value = content;
    multiline = null;
  }

  // If asEntries is requested, return the structured document
  if (asEntries) {
    return { type: 'document', entries: rootEntries };
  }

  // Otherwise produce mapping (last-write wins)
  function entriesToMapping(entries) {
    const result = {};
    for (const e of entries) {
      let value;
      if (e.children) {
        value = entriesToMapping(e.children);
      } else {
        value = e.value == null ? '' : e.value;
      }
      result[e.key] = value;
    }
    return result;
  }

  return entriesToMapping(rootEntries);
}

function toMapping(document, strategy = 'last') {
  let entries = document;
  if (document && document.type === 'document') entries = document.entries;
  const result = {};
  function valueFromEntry(e) {
    if (e.children) return toMapping({ type: 'document', entries: e.children }, strategy);
    return e.value == null ? '' : e.value;
  }
  for (const e of entries) {
    const key = e.key;
    const val = valueFromEntry(e);
    if (strategy === 'all') {
      if (!result[key]) result[key] = [];
      result[key].push(val);
    } else if (strategy === 'first') {
      if (!(key in result)) result[key] = val;
    } else {
      result[key] = val;
    }
  }
  return result;
}

function getAll(document, key) {
  let entries = document;
  if (document && document.type === 'document') entries = document.entries;
  const out = [];
  for (const e of entries) {
    if (e.key === key) out.push(e.value == null ? '' : e.value);
  }
  return out;
}

function getFirst(document, key) {
  const vals = getAll(document, key);
  return vals[0] === undefined ? null : vals[0];
}

function getLast(document, key) {
  const vals = getAll(document, key);
  return vals.length ? vals[vals.length - 1] : null;
}

module.exports = {
  parseNyml,
  ParseError,
  toMapping,
  getAll,
  getFirst,
  getLast
};