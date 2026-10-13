const assert = require('node:assert/strict');
const fs = require('node:fs');
const source = fs.readFileSync('live_demo/app.js', 'utf8');
const html = fs.readFileSync('live_demo/index.html', 'utf8');

assert(source.includes('message.type === "camera_flash"'));
assert(source.includes('avatar.status === "generating"'));
assert(source.includes('trabajando sin bloquear'));
assert(source.includes('escapeHtml(item.label)'));
assert(html.includes('Guardar como PDF'));
assert.equal((html.match(/id="checklist"/g) || []).length, 1);
console.log('client regression checks passed');
