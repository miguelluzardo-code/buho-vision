'use strict';
/**
 * Reglas de notificación. Funciones puras: reciben datos y devuelven avisos.
 * Cada aviso tiene una `key` única → el notificador no repite avisos ya enviados.
 *
 * Aviso: { key, kind: 'task'|'alert'|'info'|'digest', ligaId, recipients: [nombre], text, toAdmin }
 */
const T = require('./time');
const M = require('./messages');
const { splitNames, isNotAPerson } = require('./contacts');

const FIELDS = [
  ['placed_by', 'colocar la cámara'],
  ['retrieved_by', 'retirar la cámara'],
  ['downloaded_by', 'descargar el material'],
];

const lgOf = (leagues, s) => leagues.find(l => l.id === s.liga) || (s.liga_name ? { id: s.liga, name: s.liga_name } : null);
const people = raw => splitNames(raw);
const isDone = s => (s.download_status || '') === 'completa';

/**
 * Reglas por tiempo. Se evalúan en cada tick; la dedupe por key evita repetir.
 * @param {object} p
 * @param {Array} p.sessions
 * @param {Array} p.leagues
 * @param {Date}  p.now
 * @param {string} p.tz
 * @param {string} p.digestTime 'HH:MM'
 */
function timeRules({ sessions, leagues, now, tz, digestTime = '08:00', maxAgeDays = 30 }) {
  const out = [];
  const today = T.localDate(now, tz);
  const nowMin = T.toMinutes(T.localTime(now, tz));
  const digestMin = T.toMinutes(digestTime) ?? 8 * 60;
  const afterDigest = nowMin >= digestMin;

  for (const s of sessions) {
    if (!s || !s.id || !s.date) continue;
    const lg = lgOf(leagues, s);
    const dd = T.diffDays(today, s.date); // >0 futuro, 0 hoy, <0 pasado
    if (dd < -maxAgeDays) continue; // sesiones viejas: no reflotar al arrancar
    const startMin = T.toMinutes(s.start_time);
    const endMin = T.toMinutes(s.end_time);

    // ── Hoy: colocar cámara ──
    if (dd === 0 && afterDigest) {
      for (const name of people(s.placed_by)) {
        out.push({ key: `colocar:${s.id}`, kind: 'task', ligaId: s.liga, recipients: [name], text: M.colocar(s, lg, name) });
      }
    }
    // ── Hoy: 90 min antes del inicio ──
    if (dd === 0 && startMin != null && nowMin >= startMin - 90 && nowMin < startMin) {
      for (const name of people(s.placed_by)) {
        out.push({ key: `colocar_pronto:${s.id}`, kind: 'task', ligaId: s.liga, recipients: [name], text: M.colocarPronto(s, lg, name) });
      }
    }
    // ── Retirar: al terminar (o al día siguiente si no hay hora fin) ──
    const retireDue = (dd === 0 && endMin != null && nowMin >= endMin) || (dd === -1 && endMin == null && afterDigest);
    if (retireDue) {
      for (const name of people(s.retrieved_by)) {
        out.push({ key: `retirar:${s.id}`, kind: 'task', ligaId: s.liga, recipients: [name], text: M.retirar(s, lg, name) });
      }
    }
    // ── Descarga pendiente: al día siguiente ──
    if (dd <= -1 && afterDigest && !isDone(s)) {
      const names = people(s.downloaded_by);
      if (dd === -1 || (dd < -1 && names.length)) {
        for (const name of names) {
          out.push({ key: `descargar:${s.id}`, kind: 'task', ligaId: s.liga, recipients: [name], text: M.descargar(s, lg, name, tz) });
        }
      }
      // Atrasada: días 3, 5, 7 y luego semanal
      const days = -dd;
      if (days >= 3 && ([3, 5, 7].includes(days) || days % 7 === 0)) {
        const name = names[0] || null;
        out.push({ key: `descarga_atrasada:${s.id}:${days}`, kind: 'alert', ligaId: s.liga, recipients: names, toAdmin: true, text: M.descargaAtrasada(s, lg, name, days, tz) });
      }
    }
    // ── SLA 48h: grabación confirmada sin entrega ──
    if ((s.confirmed_games || 0) > 0 && (s.delivered_games || 0) === 0 && s.confirmed_at) {
      const hrs = T.hoursSince(s.confirmed_at, now);
      if (hrs != null && hrs >= 48) {
        const bucket = Math.floor(hrs / 24); // 2, 3, 4… → un aviso por día
        const names = people(s.downloaded_by);
        out.push({ key: `sla48:${s.id}:${bucket}`, kind: 'alert', ligaId: s.liga, recipients: names, toAdmin: true, text: M.sla48(s, lg, names[0] || null, hrs) });
      }
    }
    // ── Próximas 48h sin responsable de colocación ──
    const deliberate = s.placed_by && isNotAPerson(s.placed_by); // p.ej. "AutoGestión"
    if (dd >= 0 && dd <= 2 && afterDigest && !people(s.placed_by).length && !deliberate) {
      out.push({ key: `sin_responsable:${s.id}`, kind: 'alert', ligaId: s.liga, recipients: [], toAdmin: true, text: M.sinResponsable(s, lg, tz) });
    }
  }

  // ── Resumen diario (uno por liga con actividad + uno general) ──
  if (afterDigest) {
    const todays = sessions.filter(s => s && s.date === today).map(s => ({ s, lg: lgOf(leagues, s) }));
    const byLiga = new Map();
    for (const it of todays) {
      const k = it.s.liga || '_';
      if (!byLiga.has(k)) byLiga.set(k, []);
      byLiga.get(k).push(it);
    }
    for (const [ligaId, items] of byLiga) {
      out.push({ key: `digest:${ligaId}:${today}`, kind: 'digest', ligaId, recipients: [], text: M.digest(today, items, tz, items[0].lg?.name || 'Búho Visión'), ligaOnly: true });
    }
    out.push({ key: `digest:_general:${today}`, kind: 'digest', ligaId: null, recipients: [], toAdmin: true, text: M.digest(today, todays, tz, 'Búho Visión · Hoy') });
  }
  return out;
}

/**
 * Reglas por cambios: comparan el snapshot anterior con el nuevo.
 */
function diffRules({ prev, next, leagues, now, tz }) {
  const out = [];
  if (!prev) return out;
  const today = T.localDate(now, tz);
  const prevById = new Map(prev.filter(s => s && s.id).map(s => [s.id, s]));

  for (const s of next) {
    if (!s || !s.id) continue;
    const lg = lgOf(leagues, s);
    const p = prevById.get(s.id);
    const future = s.date && T.diffDays(today, s.date) >= 0;

    // ── Nueva sesión o cambio de responsable → avisar al asignado ──
    for (const [field, rol] of FIELDS) {
      const before = new Set(p ? people(p[field]) : []);
      for (const name of people(s[field])) {
        if (!before.has(name) && future) {
          out.push({ key: `asignada:${s.id}:${field}:${name}`, kind: 'task', ligaId: s.liga, recipients: [name], text: M.asignada(s, lg, name, rol, tz) });
        }
      }
    }
    if (!p) continue;

    // ── Cambió fecha / cancha / horario de una sesión futura → avisar a todos los responsables ──
    const sig = x => [x.date, x.venue, x.start_time, x.end_time, (x.cameras || []).join('|')].join('#');
    if (future && sig(p) !== sig(s)) {
      const names = [...new Set(FIELDS.flatMap(([f]) => people(s[f])))];
      if (names.length) {
        const h = Buffer.from(sig(s)).toString('base64url').slice(0, 12);
        out.push({ key: `cambio:${s.id}:${h}`, kind: 'task', ligaId: s.liga, recipients: names, text: M.cambio(s, lg, names, tz) });
      }
    }
    // ── Grabación confirmada (GRAB) ──
    const c0 = p.confirmed_games || 0, c1 = s.confirmed_games || 0;
    if (c1 > c0) out.push({ key: `grab:${s.id}:${c1}`, kind: 'info', ligaId: s.liga, recipients: [], text: M.grab(s, lg, c1, s.confirmed_by) });
    // ── Entrega (ENTRE / cobrable) ──
    const d0 = p.delivered_games || 0, d1 = s.delivered_games || 0;
    if (d1 > d0) out.push({ key: `entrega:${s.id}:${d1}`, kind: 'info', ligaId: s.liga, recipients: [], text: M.entrega(s, lg, d1, s.delivered_by) });
    // ── Descarga completa ──
    if (!isDone(p) && isDone(s)) out.push({ key: `descarga_ok:${s.id}`, kind: 'info', ligaId: s.liga, recipients: [], text: M.descargaOk(s, lg, s.status_changed_by) });
    // ── Material pendiente ──
    if ((p.material_delivery_status || '') !== 'pendiente' && (s.material_delivery_status || '') === 'pendiente') {
      out.push({ key: `material:${s.id}`, kind: 'alert', ligaId: s.liga, recipients: [], toAdmin: true, text: M.material(s, lg, tz) });
    }
  }
  return out;
}

/** Tareas próximas de una persona (para el comando !yo). */
function tasksFor(name, { sessions, leagues, now, tz, days = 7 }) {
  const today = T.localDate(now, tz);
  const key = require('./contacts').normalizeName(name);
  const out = [];
  for (const s of sessions) {
    if (!s || !s.date) continue;
    const dd = T.diffDays(today, s.date);
    const lg = lgOf(leagues, s);
    for (const [field, rol] of FIELDS) {
      const mine = people(s[field]).some(n => require('./contacts').normalizeName(n) === key);
      if (!mine) continue;
      if (field === 'downloaded_by' ? (dd <= days && !isDone(s)) : (dd >= 0 && dd <= days)) {
        out.push({ s, lg, rol, dd });
      }
    }
  }
  return out.sort((a, b) => a.dd - b.dd);
}

/** Descargas y entregas atrasadas (para el comando !pendientes). */
function pending({ sessions, leagues, now, tz }) {
  const today = T.localDate(now, tz);
  const descargas = [], entregas = [];
  for (const s of sessions) {
    if (!s || !s.date) continue;
    const lg = lgOf(leagues, s);
    const dd = T.diffDays(today, s.date);
    if (dd < 0 && !isDone(s)) descargas.push({ s, lg, days: -dd });
    if ((s.confirmed_games || 0) > 0 && (s.delivered_games || 0) === 0) {
      const hrs = s.confirmed_at ? T.hoursSince(s.confirmed_at, now) : null;
      entregas.push({ s, lg, hrs });
    }
  }
  return { descargas: descargas.sort((a, b) => b.days - a.days), entregas: entregas.sort((a, b) => (b.hrs || 0) - (a.hrs || 0)) };
}

module.exports = { timeRules, diffRules, tasksFor, pending, lgOf, FIELDS };
