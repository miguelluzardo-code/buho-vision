'use strict';
require('dotenv').config();

const env = (k, d) => (process.env[k] === undefined || process.env[k] === '' ? d : process.env[k]);

module.exports = {
  tz: env('BOT_TZ', 'America/Montevideo'),
  digestTime: env('BOT_DIGEST_TIME', '08:00'),
  tickMinutes: Number(env('BOT_TICK_MINUTES', 5)),
  prefix: env('BOT_COMMAND_PREFIX', '!'),
  dryRun: env('BOT_DRY_RUN', '0') === '1' || process.argv.includes('--dry'),
  maxAgeDays: Number(env('BOT_MAX_AGE_DAYS', 30)),
  localData: env('BOT_LOCAL_DATA', './data/snapshot.json'),
  sessionDir: env('BOT_SESSION_DIR', './.wwebjs_auth'),
  chromePath: env('PUPPETEER_EXECUTABLE_PATH', ''),
  adminPhones: env('BOT_ADMIN_PHONES', '').split(',').map(s => s.trim()).filter(Boolean),
  serviceAccountJson: env('FIREBASE_SERVICE_ACCOUNT', ''),
  // Claves de la app (ver const LS en buhovision_app.html)
  keys: { sessions: 'ps2_sessions', leagues: 'ps2_leagues' },
};
