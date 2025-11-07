#!/usr/bin/env node

/**
 * Convert JSON to NYML format
 */

function jsonToNyml(obj, indent = 0) {
  const lines = [];
  const indentStr = '  '.repeat(indent);

  if (typeof obj === 'object' && obj !== null) {
    if (Array.isArray(obj)) {
      // Array - convert to multiline string
      lines.push(`${indentStr}|`);
      for (const item of obj) {
        lines.push(`${indentStr}  ${item}`);
      }
      if (obj.length > 0) {
        lines.push(''); // Empty line after multiline
      }
    } else {
      // Object
      for (const [key, value] of Object.entries(obj)) {
        // Quote key if it contains special characters or spaces
        const keyStr = needsQuoting(key) ? `"${key}"` : key;

        if (typeof value === 'object' && value !== null) {
          if (Array.isArray(value)) {
            // Array - convert to multiline string
            lines.push(`${indentStr}${keyStr}: |`);
            for (const item of value) {
              lines.push(`${indentStr}  ${item}`);
            }
            if (value.length > 0) {
              lines.push(''); // Empty line after multiline
            }
          } else {
            // Nested object
            lines.push(`${indentStr}${keyStr}:`);
            lines.push(...jsonToNyml(value, indent + 1));
          }
        } else if (typeof value === 'string' && value.includes('\n')) {
          // Multiline string - convert back to | syntax
          lines.push(`${indentStr}${keyStr}: |`);
          const contentLines = value.split('\n');
          // Remove trailing empty line if present
          if (contentLines.length > 0 && contentLines[contentLines.length - 1] === '') {
            contentLines.pop();
          }
          for (const line of contentLines) {
            lines.push(`${indentStr}  ${line}`);
          }
          lines.push(''); // Empty line after multiline
        } else {
          // Simple value
          let valueStr = String(value);
          // Quote value if it contains special characters
          if (needsQuotingValue(valueStr)) {
            valueStr = `"${valueStr}"`;
          }
          lines.push(`${indentStr}${keyStr}: ${valueStr}`);
        }
      }
    }
  } else {
    // Primitive value
    lines.push(`${indentStr}value: ${obj}`);
  }

  return lines;
}

function needsQuoting(key) {
  // Quote if contains spaces, colons, special chars, or starts with digit
  return (key.includes(' ') ||
          key.includes(':') ||
          key.includes('@') ||
          key.startsWith('"') ||
          key.startsWith('#') ||
          /^\d/.test(key) ||
          !/^[a-zA-Z0-9._-]+$/.test(key));
}

function needsQuotingValue(value) {
  // Quote if contains spaces, quotes, or special characters
  return (value.includes(' ') ||
          value.includes('"') ||
          value.includes("'") ||
          /[#@:$]/.test(value) ||
          (/^\d/.test(value) && /[-.]/.test(value)));
}

// Main execution
if (require.main === module) {
  const fs = require('fs');

  if (process.argv.length !== 3) {
    console.error('Usage: node convert_json_to_nyml.js <json_file>');
    process.exit(1);
  }

  const jsonFile = process.argv[2];

  try {
    const data = JSON.parse(fs.readFileSync(jsonFile, 'utf8'));
    const lines = jsonToNyml(data);
    console.log(lines.join('\n'));
  } catch (error) {
    console.error(`Error: ${error.message}`);
    process.exit(1);
  }
}

module.exports = { jsonToNyml, needsQuoting, needsQuotingValue };