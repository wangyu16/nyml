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
  const { strict = false } = options;

  const lines = text.split('\n');
  const root = {};
  // stack of [obj, indent]
  const stack = [[root, 0]];

  let multiline = null; // null or { key, indent, rawLines }

  for (let i = 0; i < lines.length; i++) {
    const raw = lines[i];
    const indent = leadingSpaces(raw);

  if (multiline !== null) {
    // Collecting multiline block content
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
      const content = pieces.join('\n') + '\n';
      const parent = stack[stack.length - 1][0];
      parent[multiline.key] = content;
      multiline = null;
      // Fall through to process current line as normal
    } else {
      if (raw.trim() === '') {
        multiline.rawLines.push('');
      } else {
        multiline.rawLines.push(raw);
      }
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
    const parent = stack[stack.length - 1][0];

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
      // Unquote if quoted
      if (valuePart.startsWith('"') && valuePart.endsWith('"') && (valuePart.match(/"/g) || []).length === 2) {
        valuePart = valuePart.slice(1, -1);
      }
    } else {
      const idx = raw.indexOf(':');
      if (idx === -1) {
        throw new ParseError('MISSING_COLON', 'Missing colon in key-value pair', i + 1);
      }
      key = raw.slice(0, idx).trim();
      valuePart = raw.slice(idx + 1).trim();
      // Unquote if quoted
      if (valuePart.startsWith('"') && valuePart.endsWith('"') && (valuePart.match(/"/g) || []).length === 2) {
        valuePart = valuePart.slice(1, -1);
      }
    }

    if (valuePart === '|') {
      // Start multiline collection
      multiline = { key, indent, rawLines: [] };
      continue;
    }

    // Unquote if quoted
    if (valuePart.startsWith('"') && valuePart.endsWith('"') && (valuePart.match(/"/g) || []).length === 2) {
      valuePart = valuePart.slice(1, -1);
    }

    // If valuePart is empty, it might be an object if following lines are more-indented
    if (valuePart === '') {
      // Create nested object and push with its indent (child lines must be more indented)
      const obj = {};
      parent[key] = obj;
      stack.push([obj, indent + 1]);
    } else {
      parent[key] = valuePart;
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
    const content = pieces.join('\n') + '\n';
    const parent = stack[stack.length - 1][0];
    parent[multiline.key] = content;
    multiline = null;
  }

  return root;
}

module.exports = {
  parseNyml,
  ParseError
};