const { parseNyml, ParseError } = require('../nyml-parser');

describe('NYML Parser', () => {
  test('basic key-value parsing', () => {
    const text = 'key: value';
    const result = parseNyml(text);
    expect(result).toEqual({ key: 'value' });
  });

  test('nested object parsing', () => {
    const text = `parent:
  child: value`;
    const result = parseNyml(text);
    expect(result).toEqual({ parent: { child: 'value' } });
  });

  test('comment handling', () => {
    const text = `# This is a comment
key: value
# Another comment`;
    const result = parseNyml(text);
    expect(result).toEqual({ key: 'value' });
  });

  test('quoted keys with special characters', () => {
    const text = '"http://example.com": "URL"';
    const result = parseNyml(text);
    expect(result).toEqual({ 'http://example.com': 'URL' });
  });

  test('multiline string parsing', () => {
    const text = `message: |
  This is a multiline
  string with content.`;
    const result = parseNyml(text);
    const expected = 'This is a multiline\nstring with content.\n';
    expect(result).toEqual({ message: expected });
  });

  test('comprehensive example', () => {
    const text = `# Main configuration for the application
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
  level: info`;

    const result = parseNyml(text);
    const expected = {
      app_name: 'My App',
      version: '1.2',
      server: {
        host: 'localhost',
        port: '8080',
        status_message: 'OK # (production)'
      },
      'http:routes': '/api/v1',
      'user:admin': 'admin-user',
      welcome_message: '# This is NOT a comment.\n# It is the first line of the string.\n\nThis is the main welcome message.\n\nPlease see the following:\n  * List item 1\n  * List item 2\n    * A nested item\n\nA line with a # is just text.\n',
      logging: {
        level: 'info'
      }
    };
    expect(result).toEqual(expected);
  });

  test('missing colon error', () => {
    const text = 'key value';
    expect(() => parseNyml(text)).toThrow(ParseError);
    expect(() => parseNyml(text)).toThrow('Missing colon in key-value pair');
  });

  test('unmatched quote error', () => {
    const text = '"key: value';
    expect(() => parseNyml(text)).toThrow(ParseError);
    expect(() => parseNyml(text)).toThrow('Unmatched quote in key');
  });

  test('unterminated multiline closes at EOF', () => {
    const text = `key: |
  content`;
    const result = parseNyml(text);
    expect(result).toEqual({ key: 'content\n' });
  });
});