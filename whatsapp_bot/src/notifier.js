'use strict';
/**
 * Enruta y envía avisos:
 *  - Avisos de una liga → grupo de esa liga (si está configurado) o grupo general.
 *  - Los responsables se mencionan (@) en el grupo. Si no hay grupo, se les escribe por privado.
 *  - Avisos con toAdmin → además al grupo general y a los admins por privado.
 *  - Cada key se envía una sola vez (dedupe persistente).
 */
const log = require('./logger');
const { normalizeName } = require('./contacts');

class Notifier {
  /**
   * @param {object} p
   * @param {import('./store').Store} p.store
   * @param {import('./contacts').Contacts} p.contacts
   * @param {{sendGroup(jid,text,mentions):Promise, sendPrivate(phone,text):Promise}} p.transport
   * @param {string[]} p.adminPhones
   */
  constructor({ store, contacts, transport, adminPhones = [], dryRun = false }) {
    Object.assign(this, { store, contacts, transport, adminPhones, dryRun });
  }

  targetsFor(n) {
    const g = this.store.groups();
    const ligaGroup = n.ligaId && g.byLeague ? g.byLeague[n.ligaId] : null;
    const groups = new Set();
    if (ligaGroup) groups.add(ligaGroup);
    else if (g.general && !n.ligaOnly) groups.add(g.general);
    if (n.toAdmin && g.general) groups.add(g.general);
    if (n.kind === 'digest' && !n.ligaId && g.general) groups.add(g.general);
    return [...groups];
  }

  /** Reemplaza {@Nombre} por @teléfono y arma la lista de menciones. */
  render(text, recipients) {
    const mentions = [];
    const rendered = text.replace(/\{@([^}]+)\}/g, (_, name) => {
      const phone = this.contacts.resolve(name);
      if (phone) { mentions.push(phone); return `@${phone}`; }
      return `*${name}*`;
    });
    const unresolved = recipients.filter(r => !this.contacts.resolve(r));
    return { rendered, mentions, unresolved };
  }

  async dispatch(notifs) {
    let sent = 0;
    for (const n of notifs) {
      if (this.store.wasSent(n.key)) continue;
      const { rendered, mentions, unresolved } = this.render(n.text, n.recipients || []);
      const groups = this.targetsFor(n);
      const privates = new Set();
      if (!groups.length) for (const r of n.recipients || []) { const p = this.contacts.resolve(r); if (p) privates.add(p); }
      if (n.toAdmin) for (const p of this.adminPhones) privates.add(p);
      if (!groups.length && !privates.size) {
        log.warn(`Sin destino para ${n.key} (grupo no configurado, sin teléfono para: ${(n.recipients || []).join(', ') || '—'})`);
        continue;
      }
      if (unresolved.length) log.warn(`Sin teléfono para: ${unresolved.join(', ')} (usar "!soy Nombre" o config/contacts.json)`);
      try {
        for (const jid of groups) await this._sendGroup(jid, rendered, mentions);
        for (const phone of privates) await this._sendPrivate(phone, rendered.replace(/@(\d{10,15})/g, (m, p) => this.contacts.nameFor(p) ? `*${cap(this.contacts.nameFor(p))}*` : m));
        await this.store.markSent(n.key);
        sent++;
      } catch (e) {
        log.error(`Fallo enviando ${n.key}:`, e.message);
      }
    }
    return sent;
  }

  async _sendGroup(jid, text, mentions) {
    if (this.dryRun) { log.info(`[DRY] → grupo ${jid}\n${text}\n  menciones: ${mentions.join(', ') || '—'}`); return; }
    await this.transport.sendGroup(jid, text, mentions);
  }
  async _sendPrivate(phone, text) {
    if (this.dryRun) { log.info(`[DRY] → privado ${phone}\n${text}`); return; }
    await this.transport.sendPrivate(phone, text);
  }
}

const cap = s => s.replace(/\b\w/g, c => c.toUpperCase());

module.exports = { Notifier, normalizeName };
