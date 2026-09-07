'use strict';
/**
 * Plantillas de mensajes (español rioplatense, cortas, con emoji al inicio).
 * {@nombre} se reemplaza por una mención real de WhatsApp al enviar.
 */
const { prettyDate } = require('./time');

const m = (name) => `{@${name}}`;

function sessionLine(s, lg) {
  const parts = [];
  parts.push(`*${lg?.name || s.liga_name || 'Liga'}* · ${s.venue || 'sin cancha'}`);
  const hora = [s.start_time, s.end_time].filter(Boolean).join('–');
  if (hora) parts.push(`🕐 ${hora}`);
  if ((s.cameras || []).length) parts.push(`📷 ${s.cameras.join(', ')}`);
  if ((s.courts || []).length) parts.push(`Cancha ${s.courts.join(', ')}`);
  return parts.join(' · ');
}

function respLine(s) {
  const r = [];
  if (s.placed_by) r.push(`coloca: ${s.placed_by}`);
  if (s.retrieved_by) r.push(`retira: ${s.retrieved_by}`);
  if (s.downloaded_by) r.push(`descarga: ${s.downloaded_by}`);
  return r.length ? `👤 ${r.join(' · ')}` : '👤 _sin responsables_';
}

module.exports = {
  colocar: (s, lg, name) =>
    `📷 ${m(name)} hoy te toca *colocar la cámara*.\n${sessionLine(s, lg)}`,
  colocarPronto: (s, lg, name) =>
    `⏰ ${m(name)} en ~1h30 empieza la grabación. ¿Cámara colocada?\n${sessionLine(s, lg)}`,
  retirar: (s, lg, name) =>
    `📦 ${m(name)} terminó la jornada: *retirar la cámara*.\n${sessionLine(s, lg)}`,
  descargar: (s, lg, name, tz) =>
    `⬇️ ${m(name)} *descarga pendiente* de ${prettyDate(s.date, tz)}.\n${sessionLine(s, lg)}\nCuando esté, marcá *Completa* en la app.`,
  descargaAtrasada: (s, lg, name, days, tz) =>
    `🚨 ${name ? m(name) + ' ' : ''}descarga *atrasada ${days} días* (${prettyDate(s.date, tz)}).\n${sessionLine(s, lg)}`,
  sla48: (s, lg, name, hrs) =>
    `⚠️ ${name ? m(name) + ' ' : ''}*SLA 48h vencido*: hace ${Math.floor(hrs)}h se confirmaron ${s.confirmed_games} partido(s) y todavía no hay entrega.\n${sessionLine(s, lg)}`,
  sinResponsable: (s, lg, tz) =>
    `❓ Sesión del ${prettyDate(s.date, tz)} *sin responsable de colocación*.\n${sessionLine(s, lg)}\n¿Quién la toma?`,
  asignada: (s, lg, name, rol, tz) =>
    `📌 ${m(name)} te asignaron *${rol}* para el ${prettyDate(s.date, tz)}.\n${sessionLine(s, lg)}`,
  cambio: (s, lg, names, tz) =>
    `✏️ ${names.map(m).join(' ')} cambió la sesión del ${prettyDate(s.date, tz)}.\n${sessionLine(s, lg)}\n${respLine(s)}`,
  grab: (s, lg, n, by) =>
    `✅ ${by || 'Alguien'} confirmó *${n} partido(s) grabado(s)* · ${lg?.name || ''} · ${s.venue || ''}`,
  entrega: (s, lg, n, by) =>
    `🎬 ${by || 'Alguien'} entregó *${n} partido(s)* · ${lg?.name || ''} · ${s.venue || ''} · Cobrable 💰`,
  descargaOk: (s, lg, by) =>
    `💾 Descarga *completa* · ${lg?.name || ''} · ${s.venue || ''}${by ? ` · ${by}` : ''}`,
  material: (s, lg, tz) =>
    `📨 *Entrega de material pendiente* · ${lg?.name || ''} · ${s.venue || ''} (${prettyDate(s.date, tz)})`,
  digest: (dateIso, items, tz, title) => {
    const head = `🦉 *${title || 'Búho Visión'}* · ${prettyDate(dateIso, tz)}`;
    if (!items.length) return `${head}\nSin grabaciones programadas hoy. 😴`;
    const body = items.map(({ s, lg }) => `• ${sessionLine(s, lg)}\n  ${respLine(s)}`).join('\n');
    return `${head}\n${body}`;
  },
  ayuda: (prefix) =>
    [
      '🦉 *Comandos del bot Búho Visión*',
      `${prefix}hoy · grabaciones de hoy`,
      `${prefix}mañana · grabaciones de mañana`,
      `${prefix}semana · próximos 7 días`,
      `${prefix}pendientes · descargas y entregas atrasadas`,
      `${prefix}yo · mis tareas próximas`,
      `${prefix}soy <Nombre> · vincular mi número con mi nombre en la planilla`,
      `${prefix}liga <Nombre de liga> · usar este grupo para esa liga (admin)`,
      `${prefix}general · usar este grupo como grupo general (admin)`,
      `${prefix}ayuda · esta lista`,
    ].join('\n'),
  sessionLine,
  respLine,
};
