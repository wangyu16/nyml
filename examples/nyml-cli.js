#!/usr/bin/env node

// NYML CLI - Node.js implementation
// Usage:
//  node nyml-cli.js [--entries] [--strategy last|first|all] [-o OUTPUT] FILE

const fs = require('fs');
const path = require('path');
const parser = require(path.join(__dirname, '..', 'parsers', 'javascript', 'nyml-parser.js'));

function usage() {
  console.error('Usage: nyml-cli.js [--entries] [--strategy last|first|all] [-o OUTPUT] FILE');
  process.exit(2);
}

const argv = process.argv.slice(2);
let entries = false;
let strategy = 'last';
let output = null;
let file = null;

for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  if (a === '--entries' || a === '-e') {
    entries = true;
  } else if (a.startsWith('--strategy=')) {
    strategy = a.split('=')[1] || 'last';
  } else if (a === '--strategy' || a === '-s') {
    strategy = argv[++i];
  } else if (a === '--output' || a === '-o') {
    output = argv[++i];
  } else if (a === '--help' || a === '-h') {
    usage();
  } else if (!file) {
    file = a;
  } else {
    usage();
  }
}

if (!file) usage();

const content = fs.readFileSync(file, 'utf8');
let outObj;
if (entries) {
  outObj = parser.parseNyml(content, { asEntries: true });
} else {
  if (strategy === 'last') {
    outObj = parser.parseNyml(content, {});
  } else {
    const doc = parser.parseNyml(content, { asEntries: true });
    outObj = parser.toMapping(doc, strategy);
  }
}
const outStr = JSON.stringify(outObj, null, 2);
if (output) fs.writeFileSync(output, outStr);
else console.log(outStr);
