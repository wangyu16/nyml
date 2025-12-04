/**
 * Unit tests for NYML V2 parser.
 */

const { parseNymlV2, serializeNymlV2 } = require("../nyml-parser-v2");

describe("Basic Parsing", () => {
  test("empty input returns empty list", () => {
    expect(parseNymlV2("")).toEqual([]);
  });

  test("whitespace only returns empty list", () => {
    expect(parseNymlV2("   \n\n   \n")).toEqual([]);
  });

  test("single key-value pair", () => {
    const result = parseNymlV2("name: Alice");
    expect(result).toEqual([{ name: "Alice" }]);
  });

  test("multiple key-value pairs become list items", () => {
    const nyml = `name: Alice
age: 25`;
    const result = parseNymlV2(nyml);
    expect(result).toEqual([{ name: "Alice" }, { age: "25" }]);
  });

  test("duplicate keys are preserved as separate list items", () => {
    const nyml = `item: one
item: two
item: three`;
    const result = parseNymlV2(nyml);
    expect(result).toEqual([{ item: "one" }, { item: "two" }, { item: "three" }]);
  });

  test("values can contain colons", () => {
    const result = parseNymlV2("url: http://example.com:8080/path");
    expect(result).toEqual([{ url: "http://example.com:8080/path" }]);
  });

  test("hash symbol in value is preserved", () => {
    const result = parseNymlV2("comment: # this is not a comment");
    expect(result).toEqual([{ comment: "# this is not a comment" }]);
  });
});

describe("Quoted Keys", () => {
  test("quoted key can contain colon", () => {
    const result = parseNymlV2('"http:url": value');
    expect(result).toEqual([{ "http:url": "value" }]);
  });

  test("quoted key can contain spaces", () => {
    const result = parseNymlV2('"my key": my value');
    expect(result).toEqual([{ "my key": "my value" }]);
  });

  test("multiple quoted keys work correctly", () => {
    const nyml = `"key:one": value1
"key:two": value2`;
    const result = parseNymlV2(nyml);
    expect(result).toEqual([{ "key:one": "value1" }, { "key:two": "value2" }]);
  });
});

describe("Multi-Value Fields", () => {
  test("multi-value with plain strings", () => {
    const nyml = `items:
  value1
  value2
  value3`;
    const result = parseNymlV2(nyml);
    expect(result).toEqual([{ items: ["value1", "value2", "value3"] }]);
  });

  test("multi-value with key-value children", () => {
    const nyml = `items:
  child1: a
  child2: b`;
    const result = parseNymlV2(nyml);
    expect(result).toEqual([{ items: [{ child1: "a" }, { child2: "b" }] }]);
  });

  test("multi-value with mixed strings and key-value pairs", () => {
    const nyml = `items:
  value1
  child: a
  another plain value`;
    const result = parseNymlV2(nyml);
    expect(result).toEqual([
      { items: ["value1", { child: "a" }, "another plain value"] },
    ]);
  });

  test("duplicate keys within multi-value are preserved", () => {
    const nyml = `items:
  child: a
  child: b`;
    const result = parseNymlV2(nyml);
    expect(result).toEqual([{ items: [{ child: "a" }, { child: "b" }] }]);
  });

  test("single item in multi-value still creates a list", () => {
    const nyml = `item:
  only-one`;
    const result = parseNymlV2(nyml);
    expect(result).toEqual([{ item: ["only-one"] }]);
  });

  test("single key-value in multi-value creates list with one object", () => {
    const nyml = `item:
  only: one`;
    const result = parseNymlV2(nyml);
    expect(result).toEqual([{ item: [{ only: "one" }] }]);
  });

  test("empty lines in multi-value context are ignored", () => {
    const nyml = `items:
  value1

  value2`;
    const result = parseNymlV2(nyml);
    expect(result).toEqual([{ items: ["value1", "value2"] }]);
  });
});

describe("Nesting", () => {
  test("nested multi-value fields", () => {
    const nyml = `outer:
  inner:
    a
    b`;
    const result = parseNymlV2(nyml);
    expect(result).toEqual([{ outer: [{ inner: ["a", "b"] }] }]);
  });

  test("deeply nested structure", () => {
    const nyml = `level1:
  level2:
    level3:
      value: deep`;
    const result = parseNymlV2(nyml);
    expect(result).toEqual([
      { level1: [{ level2: [{ level3: [{ value: "deep" }] }] }] },
    ]);
  });

  test("multiple nested structures at same level", () => {
    const nyml = `first:
  a: 1
second:
  b: 2`;
    const result = parseNymlV2(nyml);
    expect(result).toEqual([{ first: [{ a: "1" }] }, { second: [{ b: "2" }] }]);
  });
});

describe("Multiline Strings", () => {
  test("basic multiline string", () => {
    const nyml = `text: |
  line1
  line2`;
    const result = parseNymlV2(nyml);
    expect(result).toEqual([{ text: "line1\nline2\n" }]);
  });

  test("multiline string preserves empty lines", () => {
    const nyml = `text: |
  line1

  line2`;
    const result = parseNymlV2(nyml);
    expect(result).toEqual([{ text: "line1\n\nline2\n" }]);
  });

  test("multiline string dedents content", () => {
    const nyml = `text: |
    indented
    content`;
    const result = parseNymlV2(nyml);
    expect(result).toEqual([{ text: "indented\ncontent\n" }]);
  });

  test("multiline string preserves relative indentation", () => {
    const nyml = `code: |
  if true:
    print("yes")
  else:
    print("no")`;
    const result = parseNymlV2(nyml);
    const expected = 'if true:\n  print("yes")\nelse:\n  print("no")\n';
    expect(result).toEqual([{ code: expected }]);
  });

  test("hash in multiline is preserved", () => {
    const nyml = `md: |
  # Heading
  Content`;
    const result = parseNymlV2(nyml);
    expect(result).toEqual([{ md: "# Heading\nContent\n" }]);
  });

  test("content after multiline block is parsed correctly", () => {
    const nyml = `text: |
  multiline
  content
next: value`;
    const result = parseNymlV2(nyml);
    expect(result).toEqual([{ text: "multiline\ncontent\n" }, { next: "value" }]);
  });
});

describe("Root Level Behavior", () => {
  test("plain strings at root level are ignored", () => {
    const nyml = `this is ignored
name: Alice
also ignored
age: 25`;
    const result = parseNymlV2(nyml);
    expect(result).toEqual([{ name: "Alice" }, { age: "25" }]);
  });

  test("root strings can be used like comments", () => {
    const nyml = `This is like a comment
key: value`;
    const result = parseNymlV2(nyml);
    expect(result).toEqual([{ key: "value" }]);
  });
});

describe("Edge Cases", () => {
  test("value that is just spaces after colon creates multi-value", () => {
    const nyml = `items:   
  value1`;
    const result = parseNymlV2(nyml);
    expect(result).toEqual([{ items: ["value1"] }]);
  });

  test("key can have spaces", () => {
    const result = parseNymlV2("my key: value");
    expect(result).toEqual([{ "my key": "value" }]);
  });

  test("leading spaces in value are trimmed", () => {
    const result = parseNymlV2("key:    value with spaces   ");
    expect(result).toEqual([{ key: "value with spaces" }]);
  });

  test("inline value containing colon is plain string", () => {
    const result = parseNymlV2("item: only: one");
    expect(result).toEqual([{ item: "only: one" }]);
  });
});

describe("Spec Examples", () => {
  test("spec example 1: name and age", () => {
    const nyml = `name: Alice
age: 25`;
    const result = parseNymlV2(nyml);
    expect(result).toEqual([{ name: "Alice" }, { age: "25" }]);
  });

  test("spec example 2: items with mixed content", () => {
    const nyml = `items:
  value1
  value2
  child: a
  child: b`;
    const result = parseNymlV2(nyml);
    expect(result).toEqual([
      { items: ["value1", "value2", { child: "a" }, { child: "b" }] },
    ]);
  });

  test("spec example 3: mixed strings and key-values", () => {
    const nyml = `items:
  value1
  child: a
  another plain value`;
    const result = parseNymlV2(nyml);
    expect(result).toEqual([
      { items: ["value1", { child: "a" }, "another plain value"] },
    ]);
  });

  test("spec example: single item list", () => {
    const nyml = `item:
  only-one`;
    const result = parseNymlV2(nyml);
    expect(result).toEqual([{ item: ["only-one"] }]);
  });

  test("spec example: single key-value in list", () => {
    const nyml = `item:
  only: one`;
    const result = parseNymlV2(nyml);
    expect(result).toEqual([{ item: [{ only: "one" }] }]);
  });

  test("spec example: inline colon treated as plain value", () => {
    const nyml = "item: only: one";
    const result = parseNymlV2(nyml);
    expect(result).toEqual([{ item: "only: one" }]);
  });

  test("spec example: nested multi-value", () => {
    const nyml = `outer:
  inner:
    a
    b`;
    const result = parseNymlV2(nyml);
    expect(result).toEqual([{ outer: [{ inner: ["a", "b"] }] }]);
  });
});

describe("Serialization", () => {
  test("serialize simple key-value pairs", () => {
    const data = [{ name: "Alice" }, { age: "25" }];
    const result = serializeNymlV2(data);
    expect(result).toBe("name: Alice\nage: 25");
  });

  test("serialize multi-value list", () => {
    const data = [{ items: ["a", "b", "c"] }];
    const result = serializeNymlV2(data);
    const expected = `items:
  a
  b
  c`;
    expect(result).toBe(expected);
  });

  test("serialize mixed content list", () => {
    const data = [{ items: ["value", { key: "val" }] }];
    const result = serializeNymlV2(data);
    const expected = `items:
  value
  key: val`;
    expect(result).toBe(expected);
  });

  test("serialize multiline string", () => {
    const data = [{ text: "line1\nline2\n" }];
    const result = serializeNymlV2(data);
    const expected = `text: |
  line1
  line2`;
    expect(result).toBe(expected);
  });

  test("serialize key containing colon", () => {
    const data = [{ "http:url": "value" }];
    const result = serializeNymlV2(data);
    expect(result).toBe('"http:url": value');
  });
});

describe("Roundtrip", () => {
  test("roundtrip simple key-value", () => {
    const original = "name: Alice";
    const data = parseNymlV2(original);
    const serialized = serializeNymlV2(data);
    const reparsed = parseNymlV2(serialized);
    expect(data).toEqual(reparsed);
  });

  test("roundtrip multi-value list", () => {
    const original = `items:
  value1
  value2`;
    const data = parseNymlV2(original);
    const serialized = serializeNymlV2(data);
    const reparsed = parseNymlV2(serialized);
    expect(data).toEqual(reparsed);
  });

  test("roundtrip nested structure", () => {
    const original = `outer:
  inner:
    a
    b`;
    const data = parseNymlV2(original);
    const serialized = serializeNymlV2(data);
    const reparsed = parseNymlV2(serialized);
    expect(data).toEqual(reparsed);
  });

  test("roundtrip mixed content", () => {
    const original = `items:
  value1
  child: a
  value2`;
    const data = parseNymlV2(original);
    const serialized = serializeNymlV2(data);
    const reparsed = parseNymlV2(serialized);
    expect(data).toEqual(reparsed);
  });
});
