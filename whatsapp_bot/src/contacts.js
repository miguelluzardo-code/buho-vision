'use strict';
/**
 * Resuelve nombres de responsables ("Lucero", "Mateo") a teléfonos de WhatsApp.
 *
 * Fuentes, en orden de prioridad:
 *  1. Vínculos aprendidos (comando "!soy Nombre" en el grupo) → Firestore/local
 *  2. config/contacts.json  { "Lucero": "59899111222", ... }
 *  3. Miembros de cada liga en la app (leagues[].members[].phone)
 */

function normalizeName(s) {
  return String(s || '')
    .normalize('NFD').replace(/[̀-ͯ]/g, '')
    .toLowerCase().trim().replace(/\s+/g, ' ');
}

/** "099 123 456" (Uruguay) → "59899123456". Devuelve null si no parece un número. */
function normalizePhone(raw, defaultCountry = '598') {
  if (!raw) return null;
  let p = String(raw).replace(/[^\d+]/g, '');
  if (!p) return null;
  if (p.startsWith('+')) p = p.slice(1);
  if (p.startsWith('00')) p = p.slice(2);
  // Uruguay: celulares 09x xxx xxx → 598 9x xxx xxx
  if (p.length === 9 && p.startsWith('0')) p = defaultCountry + p.slice(1);
  if (p.length === 8 && p.startsWith('9')) p = defaultCountry + p;
  if (p.length < 10 || p.length > 15) return null;
  return p;
}

class Contacts {
  constructor({ manual = {}, learned = {}, leagues = [] } = {}) {
    this.manual = manual;
    this.learned = learned;
    this.leagues = leagues;
  }

  setLeagues(leagues) { this.leagues = leagues || []; }
  learn(name, phone) { this.learned[normalizeName(name)] = phone; }

  /** Nombre → teléfono (E.164 sin +) o null. */
  resolve(name) {
    const key = normalizeName(name);
    if (!key) return null;
    if (this.learned[key]) return this.learned[key];
    for (const [n, p] of Object.entries(this.manual)) {
      if (normalizeName(n) === key) return normalizePhone(p);
    }
    for (const lg of this.leagues) {
      for (const m of lg.members || []) {
        if (normalizeName(m.name) === key && m.phone) return normalizePhone(m.phone);
      }
    }
    // Coincidencia parcial: "Mateo" ↔ "Mateo Pérez"
    const all = this.allEntries();
    const hit = all.find(([n]) => n.split(' ').includes(key) || key.split(' ').includes(n));
    return hit ? hit[1] : null;
  }

  /** Teléfono → nombre conocido o null. */
  nameFor(phone) {
    const p = normalizePhone(phone);
    const hit = this.allEntries().find(([, ph]) => ph === p);
    return hit ? hit[0] : null;
  }

  allEntries() {
    const out = [];
    for (const [n, p] of Object.entries(this.learned)) out.push([n, p]);
    for (const [n, p] of Object.entries(this.manual)) { const ph = normalizePhone(p); if (ph) out.push([normalizeName(n), ph]); }
    for (const lg of this.leagues) for (const m of lg.members || []) { const ph = normalizePhone(m.phone); if (ph) out.push([normalizeName(m.name), ph]); }
    return out;
  }
}

/** Separa "Lucero // Mateo", "Lucero y Mateo", "Lucero, Mateo" en nombres. Ignora frases como "Queda en depósito". */
function splitNames(raw) {
  if (!raw) return [];
  return String(raw)
    .split(/\/\/|,|\by\b|&|\+|\//i)
    .map(s => s.trim())
    .filter(s => s && !isNotAPerson(s));
}

function isNotAPerson(s) {
  const n = normalizeName(s);
  return /deposito|autogestion|auto gestion|nadie|sin asignar|queda|n\/a|^-+$|^—$/.test(n);
}

module.exports = { Contacts, normalizeName, normalizePhone, splitNames, isNotAPerson };
