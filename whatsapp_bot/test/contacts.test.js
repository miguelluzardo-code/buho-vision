'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const { Contacts, normalizePhone, splitNames, isNotAPerson } = require('../src/contacts');

test('normalizePhone: formatos uruguayos', () => {
  assert.equal(normalizePhone('099 111 222'), '59899111222');
  assert.equal(normalizePhone('+598 99 111 222'), '59899111222');
  assert.equal(normalizePhone('59899111222'), '59899111222');
  assert.equal(normalizePhone('99111222'), '59899111222');
  assert.equal(normalizePhone('abc'), null);
});

test('splitNames separa responsables múltiples y descarta frases', () => {
  assert.deepEqual(splitNames('Lucero // Mateo'), ['Lucero', 'Mateo']);
  assert.deepEqual(splitNames('Lucero y Mateo'), ['Lucero', 'Mateo']);
  assert.deepEqual(splitNames('Queda en depósito'), []);
  assert.deepEqual(splitNames('AutoGestión'), []);
  assert.deepEqual(splitNames(''), []);
  assert.ok(isNotAPerson('Queda en deposito'));
});

test('Contacts resuelve por vínculo, config y miembros de liga', () => {
  const c = new Contacts({
    manual: { 'Mateo': '099 222 333' },
    learned: { 'miguel': '59899333444' },
    leagues: [{ id: 'l1', name: 'Liga Kings', members: [{ name: 'Lucero Pérez', phone: '099 111 222' }] }],
  });
  assert.equal(c.resolve('Mateo'), '59899222333');
  assert.equal(c.resolve('MIGUEL'), '59899333444');
  assert.equal(c.resolve('Lucero'), '59899111222', 'coincidencia parcial con "Lucero Pérez"');
  assert.equal(c.resolve('Nadie'), null);
  assert.equal(c.nameFor('099 222 333'), 'mateo');
  c.learn('Nuevo', '59891234567');
  assert.equal(c.resolve('nuevo'), '59891234567');
});
