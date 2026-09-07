'use strict';
/**
 * Comandos dentro de los grupos (y por privado): !hoy, !mañana, !semana, !pendientes, !yo, !soy, !liga, !general, !ayuda
 */
const T = require('./time');
const M = require('./messages');
const R = require('./rules');
const { normalizeName } = require('./contacts');

function stripAccents(s) { return s.normalize('NFD').replace(/[̀-ͯ]/g, ''); }

/**
 * @param {object} p
 * @param {string} p.text        texto del mensaje
 * @param {string} p.fromPhone   teléfono del remitente (sin @c.us)
 * @param {string|null} p.chatJid id del chat (grupo o privado)
 * @param {boolean} p.isGroup
 * @param {string} p.chatName
 * @param {object} p.ctx         { store, contacts, sessions, leagues, now, tz, prefix, adminPhones, digestTime }
 * @returns {Promise<string|null>} respuesta o null si no es un comando
 */
async function handleCommand({ text, fromPhone, chatJid, isGroup, chatName }, ctx) {
  const { prefix, tz, now, sessions, leagues, store, contacts, adminPhones = [] } = ctx;
  const t = (text || '').trim();
  if (!t.startsWith(prefix)) return null;
  const [rawCmd, ...rest] = t.slice(prefix.length).trim().split(/\s+/);
  const cmd = stripAccents(rawCmd.toLowerCase());
  const arg = rest.join(' ').trim();
  const today = T.localDate(now, tz);
  const isAdmin = adminPhones.includes(fromPhone);

  const listDay = (iso, title) => {
    const items = sessions.filter(s => s && s.date === iso).map(s => ({ s, lg: R.lgOf(leagues, s) }));
    return M.digest(iso, items, tz, title);
  };

  switch (cmd) {
    case 'ayuda': case 'help': case 'comandos':
      return M.ayuda(prefix);

    case 'hoy':
      return listDay(today, 'Hoy');

    case 'manana':
      return listDay(T.addDays(today, 1), 'Mañana');

    case 'semana': {
      const lines = [];
      for (let i = 0; i < 7; i++) {
        const iso = T.addDays(today, i);
        const ds = sessions.filter(s => s && s.date === iso);
        if (!ds.length) continue;
        lines.push(`*${T.prettyDate(iso, tz)}*`);
        for (const s of ds) lines.push(`• ${M.sessionLine(s, R.lgOf(leagues, s))}\n  ${M.respLine(s)}`);
      }
      return lines.length ? `🗓 *Próximos 7 días*\n${lines.join('\n')}` : '🗓 Sin grabaciones en los próximos 7 días.';
    }

    case 'pendientes': {
      const { descargas, entregas } = R.pending({ sessions, leagues, now, tz });
      const a = descargas.slice(0, 15).map(({ s, lg, days }) => `• ${lg?.name || ''} · ${s.venue || ''} · ${T.prettyDate(s.date, tz)} · ${days}d${s.downloaded_by ? ` · ${s.downloaded_by}` : ''}`);
      const b = entregas.slice(0, 15).map(({ s, lg, hrs }) => `• ${lg?.name || ''} · ${s.venue || ''} · ${s.confirmed_games} grabado(s)${hrs != null ? ` · ${Math.floor(hrs)}h${hrs >= 48 ? ' ⚠️' : ''}` : ''}`);
      return [
        `⬇️ *Descargas pendientes* (${descargas.length})`, ...(a.length ? a : ['— ninguna —']),
        '', `🎬 *Entregas pendientes* (${entregas.length})`, ...(b.length ? b : ['— ninguna —']),
      ].join('\n');
    }

    case 'yo': case 'mis': case 'mistareas': {
      const name = arg || contacts.nameFor(fromPhone);
      if (!name) return `No sé quién sos 🙈. Escribí *${prefix}soy TuNombre* (como figura en la planilla) y después *${prefix}yo*.`;
      const tasks = R.tasksFor(name, { sessions, leagues, now, tz });
      if (!tasks.length) return `✅ *${cap(name)}*: sin tareas en los próximos 7 días.`;
      const lines = tasks.map(({ s, lg, rol, dd }) => `• ${dd === 0 ? 'Hoy' : dd === 1 ? 'Mañana' : dd < 0 ? `Hace ${-dd}d` : T.prettyDate(s.date, tz)} · *${rol}* · ${lg?.name || ''} · ${s.venue || ''}${s.start_time ? ` · ${s.start_time}` : ''}`);
      return `📋 *Tareas de ${cap(name)}*\n${lines.join('\n')}`;
    }

    case 'soy': {
      if (!arg) return `Uso: *${prefix}soy Nombre* (tal como aparece en la planilla).`;
      await store.learnContact(normalizeName(arg), fromPhone);
      contacts.learn(arg, fromPhone);
      return `👍 Listo, *${cap(arg)}*: te aviso a este número cuando tengas una tarea.`;
    }

    case 'liga': {
      if (!isGroup) return 'Este comando se usa dentro de un grupo.';
      if (!isAdmin) return 'Solo un admin puede configurar grupos.';
      if (!arg) return `Uso: *${prefix}liga Nombre de la liga*\nLigas: ${leagues.map(l => l.name).join(', ')}`;
      const lg = leagues.find(l => normalizeName(l.name) === normalizeName(arg)) || leagues.find(l => normalizeName(l.name).includes(normalizeName(arg)));
      if (!lg) return `No encuentro la liga "${arg}". Ligas: ${leagues.map(l => l.name).join(', ')}`;
      await store.setGroup('liga', chatJid, lg.id);
      return `✅ Este grupo ("${chatName}") recibirá los avisos de *${lg.name}*.`;
    }

    case 'general': {
      if (!isGroup) return 'Este comando se usa dentro de un grupo.';
      if (!isAdmin) return 'Solo un admin puede configurar grupos.';
      await store.setGroup('general', chatJid);
      return `✅ Este grupo ("${chatName}") es ahora el *grupo general* (resumen diario, alertas y ligas sin grupo propio).`;
    }

    case 'ping':
      return 'pong 🦉';

    default:
      return null; // texto que empieza con el prefijo pero no es comando: ignorar
  }
}

const cap = s => String(s).replace(/\b\w/g, c => c.toUpperCase());

module.exports = { handleCommand };
