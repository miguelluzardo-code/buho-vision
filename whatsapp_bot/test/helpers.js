'use strict';
const fs = require('fs');
const path = require('path');
const snap = () => JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'data', 'snapshot.example.json'), 'utf8'));
const TZ = 'America/Montevideo';
const at = iso => new Date(iso); // '2026-04-24T10:00:00-03:00'
module.exports = { snap, TZ, at };
