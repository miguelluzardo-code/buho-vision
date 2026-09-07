'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const { timeRules, diffRules, tasksFor, pending } = require('../src/rules');
const { snap, TZ, at } = require('./helpers');

const run = (now, extra = {}) => { const d = snap(); return timeRules({ sessions: d.ps2_sessions, leagues: d.ps2_leagues, now, tz: TZ, digestTime: '08:00', ...extra }); };
const keys = ns => ns.map(n => n.key);

test('mañana temprano (antes del resumen) no manda tareas del día', () => {
  const ns = run(at('2026-04-24T07:00:00-03:00'));
  assert.ok(!keys(ns).some(k => k.startsWith('colocar:')));
  assert.ok(!keys(ns).some(k => k.startsWith('digest:')));
});

test('a la hora del resumen: colocar para hoy, resumen por liga y general', () => {
  const ns = run(at('2026-04-24T08:00:00-03:00'));
  const k = keys(ns);
  assert.ok(k.includes('colocar:s1'));
  assert.ok(k.includes('colocar:s2'));
  assert.ok(k.includes('digest:lg_solymar:2026-04-24'));
  assert.ok(k.includes('digest:lg_fubb:2026-04-24'));
  assert.ok(k.includes('digest:_general:2026-04-24'));
  const c = ns.find(n => n.key === 'colocar:s1');
  assert.deepEqual(c.recipients, ['Lucero']);
  assert.match(c.text, /\{@Lucero\}/);
  assert.match(c.text, /Solymar/);
});

test('recordatorio 90 min antes del inicio', () => {
  const ns = run(at('2026-04-24T18:45:00-03:00'));
  assert.ok(keys(ns).includes('colocar_pronto:s1'));   // 20:00 - 90min = 18:30
  assert.ok(!keys(ns).includes('colocar_pronto:s2'));  // 21:00 - 90min = 19:30 todavía no
});

test('retirar: al terminar; "Queda en depósito" no es una persona', () => {
  const ns = run(at('2026-04-24T22:05:00-03:00'));
  assert.ok(!keys(ns).includes('retirar:s1'), 'Queda en depósito → sin aviso');
  // s2 no tiene hora fin → se avisa al día siguiente
  assert.ok(!keys(ns).includes('retirar:s2'));
  const next = run(at('2026-04-25T08:30:00-03:00'));
  assert.ok(keys(next).includes('retirar:s2'));
  assert.deepEqual(next.find(n => n.key === 'retirar:s2').recipients, ['Mateo']);
});

test('descarga pendiente al día siguiente y atrasada a los 3 días (+admin)', () => {
  const next = run(at('2026-04-25T09:00:00-03:00'));
  assert.ok(keys(next).includes('descargar:s1'));
  assert.ok(keys(next).includes('descargar:s2'));
  assert.ok(!keys(next).includes('descargar:s5'), 'completa → nada');
  const late = run(at('2026-04-27T09:00:00-03:00'));
  const a = late.find(n => n.key === 'descarga_atrasada:s1:3');
  assert.ok(a && a.toAdmin && a.kind === 'alert');
  assert.match(a.text, /atrasada 3 días/);
});

test('SLA 48h: confirmado sin entrega → alerta diaria con bucket', () => {
  const early = run(at('2026-04-23T20:00:00-03:00')); // 44h
  assert.ok(!keys(early).some(k => k.startsWith('sla48:s3')));
  const late = run(at('2026-04-24T10:00:00-03:00'));  // ~58h → bucket 2
  const a = late.find(n => n.key === 'sla48:s3:2');
  assert.ok(a && a.toAdmin);
  assert.deepEqual(a.recipients, ['Lucero']);
  const later = run(at('2026-04-25T10:00:00-03:00'));  // ~82h → bucket 3
  assert.ok(keys(later).includes('sla48:s3:3'));
  assert.ok(!keys(run(at('2026-04-30T10:00:00-03:00'))).some(k => k.startsWith('sla48:s5')), 'entregado → nada');
});

test('sesión próxima sin responsable → alerta admin', () => {
  const ns = run(at('2026-04-24T09:00:00-03:00'));
  const a = ns.find(n => n.key === 'sin_responsable:s4');
  assert.ok(a && a.toAdmin);
  assert.match(a.text, /sin responsable/);
});

test('"AutoGestión" como responsable no dispara alerta de sin responsable', () => {
  const d = snap();
  d.ps2_sessions[3].placed_by = 'AutoGestión';
  const ns = timeRules({ sessions: d.ps2_sessions, leagues: d.ps2_leagues, now: at('2026-04-24T09:00:00-03:00'), tz: TZ });
  assert.ok(!keys(ns).includes('sin_responsable:s4'));
  assert.ok(!keys(ns).some(k => k.startsWith('colocar:s4')));
});

test('diff: nueva sesión asigna tareas; cambios de estado informan', () => {
  const d = snap();
  const prev = JSON.parse(JSON.stringify(d.ps2_sessions));
  const next = JSON.parse(JSON.stringify(d.ps2_sessions));
  next.push({ id: 's9', date: '2026-04-28', liga: 'lg_kings', venue: 'Zona Lab', placed_by: 'Lucero // Mateo', retrieved_by: 'Mateo', downloaded_by: 'Lucero', start_time: '19:00' });
  next[0].confirmed_games = 4; next[0].confirmed_by = 'Lucero';
  next[2].delivered_games = 6; next[2].delivered_by = 'Miguel';
  next[1].download_status = 'completa'; next[1].status_changed_by = 'Mateo';
  next[3].material_delivery_status = 'pendiente';
  next[3].placed_by = 'Mateo';
  const ns = diffRules({ prev, next, leagues: d.ps2_leagues, now: at('2026-04-24T12:00:00-03:00'), tz: TZ });
  const k = keys(ns);
  assert.ok(k.includes('asignada:s9:placed_by:Lucero'));
  assert.ok(k.includes('asignada:s9:placed_by:Mateo'));
  assert.ok(k.includes('asignada:s9:retrieved_by:Mateo'));
  assert.ok(k.includes('asignada:s9:downloaded_by:Lucero'));
  assert.ok(k.includes('asignada:s4:placed_by:Mateo'), 'cambio de responsable');
  assert.ok(k.includes('grab:s1:4'));
  assert.ok(k.includes('entrega:s3:6'));
  assert.ok(k.includes('descarga_ok:s2'));
  assert.ok(k.includes('material:s4'));
  assert.match(ns.find(n => n.key === 'entrega:s3:6').text, /Miguel.*6 partido/);
});

test('diff: cambio de fecha/cancha avisa a responsables; sin snapshot previo no avisa', () => {
  const d = snap();
  const prev = JSON.parse(JSON.stringify(d.ps2_sessions));
  const next = JSON.parse(JSON.stringify(d.ps2_sessions));
  next[0].venue = 'Otra cancha';
  const ns = diffRules({ prev, next, leagues: d.ps2_leagues, now: at('2026-04-23T12:00:00-03:00'), tz: TZ });
  const c = ns.find(n => n.key.startsWith('cambio:s1:'));
  assert.ok(c);
  assert.deepEqual(c.recipients, ['Lucero']);
  assert.equal(diffRules({ prev: null, next, leagues: d.ps2_leagues, now: at('2026-04-23T12:00:00-03:00'), tz: TZ }).length, 0);
});

test('tasksFor y pending', () => {
  const d = snap();
  const t = tasksFor('lucero', { sessions: d.ps2_sessions, leagues: d.ps2_leagues, now: at('2026-04-24T12:00:00-03:00'), tz: TZ });
  assert.ok(t.some(x => x.s.id === 's1' && x.rol === 'colocar la cámara'));
  assert.ok(t.some(x => x.s.id === 's3' && x.rol === 'descargar el material'), 'descarga atrasada aparece');
  const p = pending({ sessions: d.ps2_sessions, leagues: d.ps2_leagues, now: at('2026-04-24T12:00:00-03:00'), tz: TZ });
  assert.deepEqual(p.descargas.map(x => x.s.id), ['s3']);
  assert.deepEqual(p.entregas.map(x => x.s.id), ['s3']);
});

test('sesiones más viejas que maxAgeDays se ignoran en las reglas por tiempo', () => {
  const d = snap();
  const ns = timeRules({ sessions: d.ps2_sessions, leagues: d.ps2_leagues, now: at('2026-06-30T09:00:00-03:00'), tz: TZ, maxAgeDays: 30 });
  assert.equal(ns.filter(n => n.kind !== 'digest').length, 0);
});
