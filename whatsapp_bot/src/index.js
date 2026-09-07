'use strict';
/**
 * 🦉 Búho Visión · Bot de WhatsApp
 * Vive en los grupos, lee la misma base que la app (Firestore) y avisa a cada
 * responsable cuando tiene una tarea o cuando pasa algo importante.
 */
const fs = require('fs');
const path = require('path');
const cfg = require('./config');
const log = require('./logger');
const { Store } = require('./store');
const { Contacts } = require('./contacts');
const { Notifier } = require('./notifier');
const { timeRules, diffRules } = require('./rules');
const { handleCommand } = require('./commands');

async function main() {
  log.info('Iniciando bot Búho Visión', cfg.dryRun ? '(DRY RUN: no envía por WhatsApp)' : '');
  const store = new Store();
  await store.init();

  // Contactos: aprendidos (!soy) + config/contacts.json + miembros de ligas
  let manual = {};
  const manualPath = path.resolve('config/contacts.json');
  if (fs.existsSync(manualPath)) { try { manual = JSON.parse(fs.readFileSync(manualPath, 'utf8')); } catch (e) { log.warn('config/contacts.json inválido:', e.message); } }
  const contacts = new Contacts({ manual, learned: store.learnedContacts(), leagues: store.leagues });

  // Grupos por archivo (opcional, alternativa a !liga / !general)
  const groupsPath = path.resolve('config/groups.json');
  if (fs.existsSync(groupsPath)) {
    try {
      const g = JSON.parse(fs.readFileSync(groupsPath, 'utf8'));
      if (g.general) await store.setGroup('general', g.general);
      for (const [ligaName, jid] of Object.entries(g.byLeague || {})) {
        const lg = store.leagues.find(l => l.name === ligaName);
        if (lg) await store.setGroup('liga', jid, lg.id); else log.warn(`groups.json: liga "${ligaName}" no existe en la app`);
      }
    } catch (e) { log.warn('config/groups.json inválido:', e.message); }
  }

  const ctxBase = () => ({ store, contacts, sessions: store.sessions, leagues: store.leagues, now: new Date(), tz: cfg.tz, prefix: cfg.prefix, adminPhones: cfg.adminPhones, digestTime: cfg.digestTime });

  // Transporte: WhatsApp real o consola (dry run)
  let transport;
  if (cfg.dryRun) {
    transport = { sendGroup: async () => {}, sendPrivate: async () => {} };
  } else {
    const { WhatsAppTransport } = require('./whatsapp');
    transport = new WhatsAppTransport({ onMessage: m => handleCommand(m, ctxBase()) });
    await transport.start();
    const groups = await transport.listGroups();
    log.info(`Grupos donde está el bot (${groups.length}):`); for (const g of groups) log.info(`  ${g.name} → ${g.jid}`);
    if (!store.groups().general) log.warn(`Todavía no hay grupo general: escribí "${cfg.prefix}general" en el grupo elegido (desde un número admin).`);
  }

  const notifier = new Notifier({ store, contacts, transport, adminPhones: cfg.adminPhones, dryRun: cfg.dryRun });

  // Reglas por cambios (Firestore onSnapshot)
  let prevSessions = JSON.parse(JSON.stringify(store.sessions));
  store.onChange(async s => {
    contacts.setLeagues(s.leagues);
    const notifs = diffRules({ prev: prevSessions, next: s.sessions, leagues: s.leagues, now: new Date(), tz: cfg.tz });
    prevSessions = JSON.parse(JSON.stringify(s.sessions));
    if (notifs.length) { const n = await notifier.dispatch(notifs); log.info(`Cambios: ${notifs.length} aviso(s), ${n} enviado(s)`); }
  });

  // Reglas por tiempo (cada N minutos)
  const tick = async () => {
    try {
      const notifs = timeRules({ sessions: store.sessions, leagues: store.leagues, now: new Date(), tz: cfg.tz, digestTime: cfg.digestTime, maxAgeDays: cfg.maxAgeDays });
      const n = await notifier.dispatch(notifs);
      if (n) log.info(`Tick: ${n} aviso(s) enviado(s)`);
    } catch (e) { log.error('tick', e); }
  };
  await tick();
  setInterval(tick, Math.max(1, cfg.tickMinutes) * 60000);
  log.info(`Bot corriendo · tick cada ${cfg.tickMinutes} min · resumen ${cfg.digestTime} (${cfg.tz})`);
}

main().catch(e => { log.error('Fatal:', e); process.exit(1); });
