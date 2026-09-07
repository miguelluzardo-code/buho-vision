'use strict';
const ts = () => new Date().toISOString().replace('T', ' ').slice(0, 19);
module.exports = {
  info: (...a) => console.log(`[${ts()}] INFO `, ...a),
  warn: (...a) => console.warn(`[${ts()}] WARN `, ...a),
  error: (...a) => console.error(`[${ts()}] ERROR`, ...a),
};
