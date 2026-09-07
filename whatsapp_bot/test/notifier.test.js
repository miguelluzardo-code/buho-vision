'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const { Notifier } = require('../src/notifier');
const { Contacts } = require('../src/contacts');

function fakeStore(groups = {}) {
  const sent = {};
  return { sent, wasSent: k => !!sent[k], markSent: async k => { sent[k] = 1; }, groups: () => groups };
}
function fakeTransport() {
  const calls = [];
  return { calls, sendGroup: async (jid, text, mentions) => calls.push({ jid, text, mentions }), sendPrivate: async (phone, text) => calls.push({ phone, text }) };
}

test('menciona en el grupo de la liga, cae al general y no repite', async () => {
  const store = fakeStore({ general: 'G@g.us', byLeague: { lg1: 'L1@g.us' } });
  const tr = fakeTransport();
  const contacts = new Contacts({ manual: { Lucero: '59899111222' } });
  const n = new Notifier({ store, contacts, transport: tr, adminPhones: ['59899000000'] });
  const notifs = [
    { key: 'a', kind: 'task', ligaId: 'lg1', recipients: ['Lucero'], text: 'Hola {@Lucero}' },
    { key: 'b', kind: 'task', ligaId: 'lg2', recipients: ['Lucero'], text: 'Hola {@Lucero}' },
    { key: 'c', kind: 'alert', ligaId: 'lg1', recipients: [], toAdmin: true, text: 'Alerta' },
  ];
  assert.equal(await n.dispatch(notifs), 3);
  assert.deepEqual(tr.calls[0], { jid: 'L1@g.us', text: 'Hola @59899111222', mentions: ['59899111222'] });
  assert.equal(tr.calls[1].jid, 'G@g.us');
  const alertGroups = tr.calls.filter(c => c.text === 'Alerta' && c.jid).map(c => c.jid).sort();
  assert.deepEqual(alertGroups, ['G@g.us', 'L1@g.us']);
  assert.ok(tr.calls.some(c => c.phone === '59899000000' && c.text === 'Alerta'), 'admin por privado');
  assert.equal(await n.dispatch(notifs), 0, 'dedupe');
});

test('sin grupo configurado escribe por privado; sin teléfono no envía', async () => {
  const store = fakeStore({});
  const tr = fakeTransport();
  const contacts = new Contacts({ manual: { Lucero: '59899111222' } });
  const n = new Notifier({ store, contacts, transport: tr });
  await n.dispatch([
    { key: 'x', kind: 'task', ligaId: 'lg1', recipients: ['Lucero'], text: 'Hola {@Lucero}' },
    { key: 'y', kind: 'task', ligaId: 'lg1', recipients: ['Desconocido'], text: 'Hola {@Desconocido}' },
  ]);
  assert.equal(tr.calls.length, 1);
  assert.equal(tr.calls[0].phone, '59899111222');
  assert.equal(tr.calls[0].text, 'Hola *Lucero*', 'en privado la mención se vuelve nombre');
  assert.ok(store.wasSent('x') && !store.wasSent('y'));
});
