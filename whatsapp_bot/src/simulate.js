'use strict';
/**
 * Simulación sin WhatsApp ni Firebase: muestra qué avisos generaría el bot
 * para un snapshot y una fecha/hora dadas.
 *
 *   node src/simulate.js [ruta/snapshot.json] [2026-04-24T10:00:00-03:00]
 */
const fs = require('fs');
const cfg = require('./config');
const { timeRules } = require('./rules');
const { Contacts } = require('./contacts');

const file = process.argv[2] || cfg.localData;
const now = process.argv[3] ? new Date(process.argv[3]) : new Date();
const d = JSON.parse(fs.readFileSync(file, 'utf8'));
const sessions = d[cfg.keys.sessions] || d.sessions || [];
const leagues = d[cfg.keys.leagues] || d.leagues || [];
const contacts = new Contacts({ leagues });

const notifs = timeRules({ sessions, leagues, now, tz: cfg.tz, digestTime: cfg.digestTime });
console.log(`Snapshot: ${file} · ${sessions.length} sesiones · ahora: ${now.toISOString()} (${cfg.tz})\n`);
for (const n of notifs) {
  const to = (n.recipients || []).map(r => `${r}${contacts.resolve(r) ? '' : ' (sin tel)'}`).join(', ');
  console.log(`── [${n.kind}] ${n.key}${n.toAdmin ? ' +admin' : ''}${to ? ` → ${to}` : ''}`);
  console.log(n.text.replace(/\{@([^}]+)\}/g, '@$1'), '\n');
}
console.log(`${notifs.length} aviso(s)`);
