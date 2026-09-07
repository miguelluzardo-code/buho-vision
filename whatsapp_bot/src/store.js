'use strict';
/**
 * Fuente de datos: Firestore (misma base que la app) o un snapshot JSON local.
 * También persiste el estado del bot (avisos enviados, grupos, vínculos nombre→teléfono).
 */
const fs = require('fs');
const path = require('path');
const cfg = require('./config');
const log = require('./logger');

class LocalState {
  constructor(file) { this.file = file; this.data = { sent: {}, groups: {}, contacts: {} }; this.load(); }
  load() { try { this.data = { ...this.data, ...JSON.parse(fs.readFileSync(this.file, 'utf8')) }; } catch { /* primera vez */ } }
  save() { fs.mkdirSync(path.dirname(this.file), { recursive: true }); fs.writeFileSync(this.file, JSON.stringify(this.data, null, 2)); }
}

class Store {
  constructor() {
    this.db = null;
    this.local = new LocalState(path.resolve('data/bot_state.json'));
    this.sessions = [];
    this.leagues = [];
    this.listeners = [];
  }

  async init() {
    if (await this._initFirebase()) return;
    log.warn('Sin Firebase: usando snapshot local', cfg.localData);
    this._loadLocalSnapshot();
    fs.watchFile(cfg.localData, { interval: 2000 }, () => { this._loadLocalSnapshot(); this._emit(); });
  }

  async _initFirebase() {
    let admin;
    try { admin = require('firebase-admin'); } catch { return false; }
    try {
      let cred;
      if (cfg.serviceAccountJson) cred = admin.credential.cert(JSON.parse(cfg.serviceAccountJson));
      else if (process.env.GOOGLE_APPLICATION_CREDENTIALS && fs.existsSync(process.env.GOOGLE_APPLICATION_CREDENTIALS)) cred = admin.credential.applicationDefault();
      else return false;
      admin.initializeApp({ credential: cred });
      this.db = admin.firestore();
      // Estado del bot en Firestore (para sobrevivir redeploys en Railway)
      const st = await this.db.collection('bot_state').doc('main').get();
      if (st.exists) this.local.data = { ...this.local.data, ...st.data() };
      // Datos de la app: sesiones (sessions_data/main) y ligas (workspace/buhovision)
      await new Promise((resolve, reject) => {
        let first = true;
        this.db.collection('sessions_data').doc('main').onSnapshot(snap => {
          const d = snap.data() || {};
          this.sessions = Array.isArray(d[cfg.keys.sessions]) ? d[cfg.keys.sessions] : [];
          if (first) { first = false; resolve(); } else this._emit();
        }, reject);
      });
      this.db.collection('workspace').doc('buhovision').onSnapshot(snap => {
        const d = snap.data() || {};
        this.leagues = Array.isArray(d[cfg.keys.leagues]) ? d[cfg.keys.leagues] : [];
        this._emit();
      });
      log.info(`Firestore conectado · ${this.sessions.length} sesiones`);
      return true;
    } catch (e) {
      log.error('Firebase no disponible:', e.message);
      return false;
    }
  }

  _loadLocalSnapshot() {
    try {
      const d = JSON.parse(fs.readFileSync(cfg.localData, 'utf8'));
      this.sessions = d[cfg.keys.sessions] || d.sessions || [];
      this.leagues = d[cfg.keys.leagues] || d.leagues || [];
      log.info(`Snapshot local · ${this.sessions.length} sesiones · ${this.leagues.length} ligas`);
    } catch (e) { log.warn('No se pudo leer snapshot local:', e.message); }
  }

  onChange(fn) { this.listeners.push(fn); }
  _emit() { for (const fn of this.listeners) { try { fn(this); } catch (e) { log.error('listener', e); } } }

  // ── Estado del bot ──
  wasSent(key) { return !!this.local.data.sent[key]; }
  async markSent(key) { this.local.data.sent[key] = Date.now(); await this._persist(); }
  groups() { return this.local.data.groups; }                 // { general: jid, byLeague: { ligaId: jid } }
  async setGroup(kind, jid, ligaId) {
    if (kind === 'general') this.local.data.groups.general = jid;
    else { this.local.data.groups.byLeague = this.local.data.groups.byLeague || {}; this.local.data.groups.byLeague[ligaId] = jid; }
    await this._persist();
  }
  learnedContacts() { return this.local.data.contacts; }
  async learnContact(nameKey, phone) { this.local.data.contacts[nameKey] = phone; await this._persist(); }

  async _persist() {
    // Limpieza: avisos de más de 60 días
    const cutoff = Date.now() - 60 * 86400000;
    for (const [k, t] of Object.entries(this.local.data.sent)) if (t < cutoff) delete this.local.data.sent[k];
    this.local.save();
    if (this.db) { try { await this.db.collection('bot_state').doc('main').set(this.local.data, { merge: true }); } catch (e) { log.warn('bot_state', e.message); } }
  }
}

module.exports = { Store };
