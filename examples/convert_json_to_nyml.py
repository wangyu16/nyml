#!/usr/bin/env python3
"""Convert JSON to NYML format."""

import json
import sys

def json_to_nyml(obj, indent=0):
    """Convert a JSON object to NYML format."""
    lines = []
    indent_str = '  ' * indent

    if isinstance(obj, dict):
        for key, value in obj.items():
            # Quote key if it contains special characters or spaces
            if needs_quoting(key):
                key_str = f'"{key}"'
            else:
                key_str = key

            if isinstance(value, dict):
                # Nested object
                lines.append(f'{indent_str}{key_str}:')
                lines.extend(json_to_nyml(value, indent + 1))
            elif isinstance(value, list):
                # Array - convert to multiline string
                lines.append(f'{indent_str}{key_str}: |')
                for item in value:
                    lines.append(f'{indent_str}  {item}')
                # Add empty line after multiline
                if value:  # Only if array is not empty
                    lines.append('')
            elif isinstance(value, str) and '\n' in value:
                # Multiline string - convert back to | syntax
                lines.append(f'{indent_str}{key_str}: |')
                # Split by lines and add proper indentation
                content_lines = value.split('\n')
                # Remove trailing empty line if present (multiline strings end with \n)
                if content_lines and content_lines[-1] == '':
                    content_lines.pop()
                
                for line in content_lines:
                    lines.append(f'{indent_str}  {line}')
                lines.append('')  # Empty line after multiline
            else:
                # Simple value
                value_str = str(value)
                # Quote value if it contains special characters
                if needs_quoting_value(value_str):
                    value_str = f'"{value_str}"'
                lines.append(f'{indent_str}{key_str}: {value_str}')

    elif isinstance(obj, list):
        # Top-level array (shouldn't normally happen, but handle it)
        for i, item in enumerate(obj):
            key = f'item{i}'
            if isinstance(item, (dict, list)):
                lines.append(f'{indent_str}{key}:')
                lines.extend(json_to_nyml(item, indent + 1))
            else:
                lines.append(f'{indent_str}{key}: {item}')

    else:
        # Top-level primitive (shouldn't normally happen)
        lines.append(f'{indent_str}value: {obj}')

    return lines

def needs_quoting(key):
    """Check if a key needs to be quoted."""
    # Quote if contains spaces, colons, special chars, or starts with digit
    return (' ' in key or
            ':' in key or
            '@' in key or
            key.startswith(('"', '#')) or
            key[0].isdigit() or
            not key.replace('_', '').replace('-', '').replace('.', '').isalnum())

def needs_quoting_value(value):
    """Check if a value needs to be quoted."""
    # Always quote strings that contain spaces, quotes, or special characters
    # Also quote if it looks like a number but contains special chars
    return (' ' in value or 
            '"' in value or 
            "'" in value or
            any(char in value for char in '#@:$') or
            (value.replace('.', '').replace('-', '').isdigit() and ('.' in value or '-' in value)))

def main():
    if len(sys.argv) != 2:
        print("Usage: python convert_json_to_nyml.py <json_file>")
        sys.exit(1)

    json_file = sys.argv[1]

    try:
        with open(json_file, 'r') as f:
            data = json.load(f)

        lines = json_to_nyml(data)
        print('\n'.join(lines))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()