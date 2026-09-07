'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const { handleCommand } = require('../src/commands');
const { Contacts } = require('../src/contacts');
const { snap, TZ, at } = require('./helpers');

function ctx(extra = {}) {
  const d = snap();
  const learned = {};
  const groups = {};
  const store = { learnContact: async (k, p) => { learned[k] = p; }, setGroup: async (kind, jid, lg) => { groups[kind] = { jid, lg }; }, groups: () => groups };
  const contacts = new Contacts({ manual: { Mateo: '59899222333' }, leagues: d.ps2_leagues });
  return { store, contacts, learned, groups, sessions: d.ps2_sessions, leagues: d.ps2_leagues, now: at('2026-04-24T12:00:00-03:00'), tz: TZ, prefix: '!', adminPhones: ['59899000000'], ...extra };
}
const msg = (text, o = {}) => ({ text, fromPhone: '59899222333', chatJid: 'G@g.us', isGroup: true, chatName: 'Búho Staff', ...o });

test('ignora texto que no es comando', async () => {
  assert.equal(await handleCommand(msg('hola a todos'), ctx()), null);
  assert.equal(await handleCommand(msg('!loquesea'), ctx()), null);
});

test('!hoy, !mañana, !semana, !pendientes', async () => {
  const c = ctx();
  assert.match(await handleCommand(msg('!hoy'), c), /Invictus[\s\S]*Malvin/);
  assert.match(await handleCommand(msg('!mañana'), c), /Zona Lab/);
  assert.match(await handleCommand(msg('!manana'), c), /Zona Lab/);
  assert.match(await handleCommand(msg('!semana'), c), /Próximos 7 días/);
  const p = await handleCommand(msg('!pendientes'), c);
  assert.match(p, /Descargas pendientes\*? \(1\)/);
  assert.match(p, /Entregas pendientes\*? \(1\)/);
  assert.match(p, /⚠️/);
});

test('!yo usa el nombre vinculado; !soy vincula', async () => {
  const c = ctx();
  assert.match(await handleCommand(msg('!yo'), c), /Tareas de Mateo/);
  assert.match(await handleCommand(msg('!yo', { fromPhone: '59891111111' }), c), /No sé quién sos/);
  assert.match(await handleCommand(msg('!soy Lucero', { fromPhone: '59891111111' }), c), /Listo, \*Lucero\*/);
  assert.equal(c.learned['lucero'], '59891111111');
  assert.match(await handleCommand(msg('!yo', { fromPhone: '59891111111' }), c), /Tareas de Lucero[\s\S]*colocar la cámara/);
});

test('!liga y !general solo admin y en grupo', async () => {
  const c = ctx();
  assert.match(await handleCommand(msg('!general'), c), /Solo un admin/);
  assert.match(await handleCommand(msg('!general', { fromPhone: '59899000000', isGroup: false }), c), /dentro de un grupo/);
  assert.match(await handleCommand(msg('!general', { fromPhone: '59899000000' }), c), /grupo general/);
  assert.equal(c.groups.general.jid, 'G@g.us');
  assert.match(await handleCommand(msg('!liga kings', { fromPhone: '59899000000' }), c), /Liga Kings/);
  assert.equal(c.groups.liga.lg, 'lg_kings');
  assert.match(await handleCommand(msg('!liga Inexistente', { fromPhone: '59899000000' }), c), /No encuentro/);
});
