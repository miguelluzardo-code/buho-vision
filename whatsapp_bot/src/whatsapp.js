'use strict';
/**
 * Transporte WhatsApp con whatsapp-web.js (sesión de WhatsApp Web con un número dedicado).
 * Escaneás el QR una vez; la sesión queda en BOT_SESSION_DIR.
 */
const cfg = require('./config');
const log = require('./logger');

const toUserJid = phone => `${phone}@c.us`;

class WhatsAppTransport {
  constructor({ onMessage }) {
    this.onMessage = onMessage;
    this.client = null;
    this.ready = false;
  }

  async start() {
    const { Client, LocalAuth } = require('whatsapp-web.js');
    const qrcode = require('qrcode-terminal');
    const puppeteer = { headless: true, args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu'] };
    if (cfg.chromePath) puppeteer.executablePath = cfg.chromePath;

    this.client = new Client({ authStrategy: new LocalAuth({ dataPath: cfg.sessionDir }), puppeteer });

    this.client.on('qr', qr => { log.info('Escaneá este QR con el WhatsApp del número del bot:'); qrcode.generate(qr, { small: true }); });
    this.client.on('authenticated', () => log.info('WhatsApp autenticado'));
    this.client.on('auth_failure', m => log.error('Fallo de autenticación WhatsApp:', m));
    this.client.on('disconnected', r => { this.ready = false; log.warn('WhatsApp desconectado:', r); });
    this.client.on('ready', () => { this.ready = true; log.info('WhatsApp listo ✅'); });

    this.client.on('message', async msg => {
      try {
        if (msg.fromMe || !msg.body) return;
        const chat = await msg.getChat();
        const fromPhone = (msg.author || msg.from || '').replace(/@.*$/, '');
        const reply = await this.onMessage({ text: msg.body, fromPhone, chatJid: chat.id._serialized, isGroup: chat.isGroup, chatName: chat.name });
        if (reply) await msg.reply(reply);
      } catch (e) { log.error('message handler', e); }
    });

    await this.client.initialize();
    await new Promise(res => { if (this.ready) res(); else this.client.once('ready', res); });
  }

  async sendGroup(jid, text, mentions = []) {
    const opts = mentions.length ? { mentions: mentions.map(toUserJid) } : {};
    await this.client.sendMessage(jid, text, opts);
  }

  async sendPrivate(phone, text) {
    const id = await this.client.getNumberId(phone);
    if (!id) { log.warn(`El número ${phone} no tiene WhatsApp`); return; }
    await this.client.sendMessage(id._serialized, text);
  }

  /** Lista de grupos donde está el bot (para configurar). */
  async listGroups() {
    const chats = await this.client.getChats();
    return chats.filter(c => c.isGroup).map(c => ({ jid: c.id._serialized, name: c.name }));
  }
}

module.exports = { WhatsAppTransport };
