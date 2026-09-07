'use strict';
/**
 * Utilidades de fecha/hora con zona horaria (sin dependencias).
 */

/** Devuelve 'YYYY-MM-DD' de `date` en la zona `tz`. */
function localDate(date, tz) {
  return new Intl.DateTimeFormat('en-CA', { timeZone: tz, year: 'numeric', month: '2-digit', day: '2-digit' }).format(date);
}

/** Devuelve 'HH:MM' de `date` en la zona `tz`. */
function localTime(date, tz) {
  return new Intl.DateTimeFormat('en-GB', { timeZone: tz, hour: '2-digit', minute: '2-digit', hour12: false }).format(date);
}

/** Suma `days` a una fecha 'YYYY-MM-DD'. */
function addDays(iso, days) {
  const [y, m, d] = iso.split('-').map(Number);
  const dt = new Date(Date.UTC(y, m - 1, d + days));
  return dt.toISOString().slice(0, 10);
}

/** Diferencia en días entre dos 'YYYY-MM-DD' (b - a). */
function diffDays(a, b) {
  const p = s => { const [y, m, d] = s.split('-').map(Number); return Date.UTC(y, m - 1, d); };
  return Math.round((p(b) - p(a)) / 86400000);
}

/** 'HH:MM' → minutos desde medianoche. null si inválido. */
function toMinutes(hhmm) {
  if (!hhmm || !/^\d{1,2}:\d{2}$/.test(hhmm)) return null;
  const [h, m] = hhmm.split(':').map(Number);
  return h * 60 + m;
}

/** Horas transcurridas desde un ISO timestamp. */
function hoursSince(isoTs, now) {
  const t = Date.parse(isoTs);
  if (Number.isNaN(t)) return null;
  return (now.getTime() - t) / 3600000;
}

/** 'YYYY-MM-DD' → 'lun 24/04' en español. */
function prettyDate(iso, tz) {
  const [y, m, d] = iso.split('-').map(Number);
  const dt = new Date(Date.UTC(y, m - 1, d, 12));
  const wd = new Intl.DateTimeFormat('es-UY', { timeZone: 'UTC', weekday: 'short' }).format(dt);
  return `${wd} ${String(d).padStart(2, '0')}/${String(m).padStart(2, '0')}`;
}

module.exports = { localDate, localTime, addDays, diffDays, toMinutes, hoursSince, prettyDate };
