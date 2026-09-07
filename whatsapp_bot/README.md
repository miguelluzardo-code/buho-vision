# 🦉 Búho Visión · Bot de WhatsApp

Bot que **vive dentro de los grupos de WhatsApp de Búho Visión**, lee la misma base de datos que la app
(`sessions_data/main` y `workspace/buhovision` en Firestore) y **avisa a cada responsable** cuando tiene una
tarea o cuando pasa algo importante. No hay que cargar nada dos veces: todo sale de la planilla de la app.

## ¿Qué avisa?

| Cuándo | A quién | Mensaje |
|---|---|---|
| Hora del resumen (08:00) | `placed_by` | 📷 Hoy te toca colocar la cámara en … |
| 90 min antes de `start_time` | `placed_by` | ⏰ En ~1h30 empieza la grabación. ¿Cámara colocada? |
| Al pasar `end_time` (o al día siguiente si no hay hora) | `retrieved_by` | 📦 Retirar la cámara |
| Día siguiente, si `download_status` ≠ completa | `downloaded_by` | ⬇️ Descarga pendiente |
| 3, 5, 7 días y luego semanal sin descargar | `downloaded_by` + admins | 🚨 Descarga atrasada N días |
| 48 h después de confirmar partidos sin entrega (y cada 24 h) | `downloaded_by` + admins | ⚠️ SLA 48h vencido |
| Sesión en las próximas 48 h sin `placed_by` | admins | ❓ Sesión sin responsable, ¿quién la toma? |
| Se crea una sesión / cambia un responsable | el asignado | 📌 Te asignaron colocar/retirar/descargar |
| Cambia fecha, cancha, horario o cámaras | todos los responsables | ✏️ Cambió la sesión |
| Alguien confirma partidos grabados (GRAB) | grupo | ✅ X confirmó N partidos grabados |
| Alguien entrega (ENTRE / cobrable) | grupo | 🎬 X entregó N partidos · Cobrable |
| Descarga marcada completa | grupo | 💾 Descarga completa |
| Entrega de material marcada pendiente | admins | 📨 Entrega de material pendiente |
| Todos los días a las 08:00 | cada grupo de liga + grupo general | 🦉 Resumen del día con responsables |

Cada aviso se envía **una sola vez** (se guarda en `bot_state/main` en Firestore, o en `data/bot_state.json`).
"Queda en depósito" y "AutoGestión" no se tratan como personas.

## Comandos dentro del grupo

```
!hoy          grabaciones de hoy
!mañana       grabaciones de mañana
!semana       próximos 7 días
!pendientes   descargas y entregas atrasadas
!yo           mis tareas próximas
!soy Lucero   vincular mi número con mi nombre en la planilla
!liga Kings   usar este grupo para esa liga (solo admin)
!general      usar este grupo como grupo general (solo admin)
!ayuda
```

## ¿A dónde va cada aviso?

1. Si la liga tiene grupo (`!liga …` o `config/groups.json`) → a ese grupo, **mencionando** (@) al responsable.
2. Si no → al grupo general.
3. Si no hay ningún grupo configurado → por privado al responsable (si conocemos su número).
4. Las alertas (`toAdmin`) van además al grupo general y por privado a `BOT_ADMIN_PHONES`.

Para mencionar a alguien el bot necesita su teléfono. Lo busca en: vínculos `!soy` → `config/contacts.json`
→ personas de la liga en la app (`Ligas → Personas → Teléfono`). Si no lo encuentra, escribe el nombre en negrita.

## Cómo funciona por dentro

- **whatsapp-web.js**: el bot es un *número dedicado* que abre una sesión de WhatsApp Web (como "Dispositivos
  vinculados"). Hay que agregarlo a los grupos como a cualquier persona. Es la única forma de que un bot lea y
  escriba en grupos comunes: la API oficial de Meta (Cloud API) no participa de grupos de usuarios y solo
  escribe a personas que abrieron conversación en las últimas 24 h (o con plantillas aprobadas y pagas).
- Es una integración **no oficial**: usar un número exclusivo para el bot, no spamear, y mantener volumen
  razonable. Si Meta bloquea el número, se repite el QR con otro. El transporte está aislado en
  `src/whatsapp.js`, así que cambiar a la Cloud API para los avisos privados es un módulo más.
- Las reglas (`src/rules.js`) son funciones puras y están testeadas (`npm test`).

```
src/
  index.js      arranque: Firestore → reglas → notificador → WhatsApp
  rules.js      reglas por tiempo (cada 5 min) y por cambios (onSnapshot)
  messages.js   textos en español
  notifier.js   enrutamiento a grupos/privados, menciones y dedupe
  commands.js   !hoy !semana !pendientes !yo !soy !liga !general
  contacts.js   nombre → teléfono
  store.js      Firestore o snapshot local + estado del bot
  whatsapp.js   transporte whatsapp-web.js
  simulate.js   "¿qué avisaría el bot tal día a tal hora?" sin WhatsApp ni Firebase
```

## Puesta en marcha

Necesitás: un **chip/número para el bot**, la **cuenta de servicio** de Firebase del proyecto `buhovision-5bee4`
(Firebase Console → Configuración → Cuentas de servicio → Generar clave), y Node 20+.

```bash
cd whatsapp_bot
npm install
cp .env.example .env          # completar BOT_ADMIN_PHONES y credenciales
cp config/contacts.example.json config/contacts.json   # nombre → teléfono
npm start                     # escaneás el QR con el WhatsApp del bot (una sola vez)
```

Al arrancar lista los grupos donde está el bot con su ID. Después, desde un número admin, en el grupo elegido:
`!general`, y en cada grupo de liga: `!liga Liga Kings`.

### Probar sin WhatsApp

```bash
npm test                                                     # tests de reglas, contactos, comandos
node src/simulate.js data/snapshot.example.json "2026-04-24T08:00:00-03:00"   # ver avisos de un día
npm run dev                                                  # corre todo pero imprime en consola en vez de enviar
```

### Railway / Docker

El `Dockerfile` instala Chromium. Montar un **volumen persistente en `/data`** (sesión de WhatsApp) y definir
`FIREBASE_SERVICE_ACCOUNT` con el JSON de la cuenta de servicio en una línea, más `BOT_ADMIN_PHONES`.
El QR sale en los logs del deploy la primera vez.

## Variables

| Variable | Default | Para qué |
|---|---|---|
| `BOT_TZ` | `America/Montevideo` | zona horaria de "hoy" y horarios |
| `BOT_DIGEST_TIME` | `08:00` | hora del resumen y de las tareas del día |
| `BOT_TICK_MINUTES` | `5` | frecuencia de evaluación de reglas por tiempo |
| `BOT_MAX_AGE_DAYS` | `30` | ignorar sesiones más viejas (no reflotar al arrancar) |
| `BOT_COMMAND_PREFIX` | `!` | prefijo de comandos |
| `BOT_ADMIN_PHONES` | | admins (E.164 sin +, separados por coma) |
| `BOT_DRY_RUN` | `0` | `1` = solo consola |
| `GOOGLE_APPLICATION_CREDENTIALS` / `FIREBASE_SERVICE_ACCOUNT` | | credenciales Firebase |
| `BOT_LOCAL_DATA` | `./data/snapshot.json` | snapshot si no hay Firebase |
| `PUPPETEER_EXECUTABLE_PATH` | | Chromium del sistema (Docker) |
| `BOT_SESSION_DIR` | `./.wwebjs_auth` | dónde guardar la sesión de WhatsApp |
