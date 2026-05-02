"""
🦉 BUHO VISION - Servidor Ecosistema Integral
Servidor Flask local que sirve la app web y genera gráficos con escudos reales.

USO:
  Mac:     python3 app_server.py
  Windows: python app_server.py

ACCESO:
  Local:  http://localhost:5000
  Celular: http://[IP_que_aparece]:5000  (misma red WiFi)
"""

import json
import os
import sys
import socket
import zipfile
import io
import re
import unicodedata
import subprocess
import tempfile
from pathlib import Path
from flask import Flask, jsonify, send_file, request, send_from_directory, abort
from flask_cors import CORS

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# ─────────────────────────────────────────────
# RUTAS BASE
# ─────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "2_Graphics_Generation" / "config.json"
GRAPHICS_DIR = BASE_DIR / "2_Graphics_Generation"

def get_ligas_base():
    """Detecta el sistema operativo y devuelve la ruta base de LIGAS."""
    # Mac - Google Drive sincronizado
    mac_path = Path("/Users/miguelluzardo/Library/CloudStorage/GoogleDrive-miguelluzardo@gmail.com/Mi unidad/ProShot/LIGAS")
    if mac_path.exists():
        return mac_path

    # Windows - Google Drive como G:\ (cuenta miguelluzardo@gmail.com)
    win_paths = [
        Path("G:/Mi unidad/ProShot/LIGAS"),
        Path("G:\\Mi unidad\\ProShot\\LIGAS"),
        Path("H:/Mi unidad/ProShot/LIGAS"),
    ]
    for p in win_paths:
        if p.exists():
            return p

    # Windows - Google Drive como disco mapeado
    for letter in "GHIJKLMNOPQRSTUVWXYZ":
        candidate = Path(f"{letter}:/Mi unidad/ProShot/LIGAS")
        if candidate.exists():
            return candidate

    # Fallback: mismo directorio que el script
    return Path(__file__).parent.parent

# ── Cloud mode (Railway) ─────────────────────
CLOUD_MODE = os.environ.get("CLOUD_MODE") == "1"
HOSTING_LOGOS_URL = os.environ.get("HOSTING_LOGOS_URL", "https://buhovision-5bee4.web.app/logos")
LOGOS_STORAGE_PREFIX = os.environ.get("LOGOS_STORAGE_PREFIX", "logos")
LOGO_CACHE_DIR = Path(os.environ.get("LOGO_CACHE_DIR", "/app/logo_cache" if CLOUD_MODE else "/tmp/buho_logo_cache"))
LOGO_CACHE_DIR.mkdir(parents=True, exist_ok=True)

if CLOUD_MODE:
    print(f"☁️  Modo CLOUD activo — logos desde Firebase Hosting: {HOSTING_LOGOS_URL}")

def _download_logo_from_hosting(folder: str, filename: str) -> Path | None:
    """Descarga logo desde Firebase Hosting al cache local. Retorna Path o None."""
    import urllib.request
    cache_key = f"{folder}_{filename}".replace("/", "_")
    cache_path = LOGO_CACHE_DIR / cache_key
    if cache_path.exists():
        return cache_path
    url = f"{HOSTING_LOGOS_URL}/{folder}/01_Escudos/{filename}"
    try:
        urllib.request.urlretrieve(url, str(cache_path))
        return cache_path
    except Exception:
        if cache_path.exists():
            cache_path.unlink()
    return None

MAC_LIGAS_BASE = get_ligas_base()
print(f"📁 Base LIGAS: {MAC_LIGAS_BASE}")

# Mapa completo de todas las ligas con sus rutas reales en Mac
LEAGUES_MAP = {
    "Liga Kings": {
        "folder": "01_Liga_Kings",
        "escudos": "01_Escudos",
        "misc": "05_Miscelaneos",
        "league_logo_file": "LIGA_KINGS.png",
        "sport": "futbol",
        "emoji": "👑"
    },
    "Liga Celeste": {
        "folder": "02_Liga_Celeste",
        "escudos": "01_Escudos",
        "misc": None,
        "league_logo_file": "liga celeste.png",
        "sport": "futbol",
        "emoji": "🔵"
    },
    "Liga Lokura": {
        "folder": "04_Liga_Lokura",
        "escudos": "01_Escudos",
        "misc": "05_Miscelaneos",
        "league_logo_file": None,
        "sport": "futbol",
        "emoji": "🔥"
    },
    "Piria Seven League": {
        "folder": "05_Piria_Seven_League",
        "escudos": "01_Escudos",
        "misc": "05_Miscelaneos",
        "league_logo_file": None,
        "sport": "futbol",
        "emoji": "7️⃣"
    },
    "Lomas Baby Futbol": {
        "folder": "07_Lomas_Baby_Futbol",
        "escudos": "01_Escudos",
        "misc": None,
        "league_logo_file": None,
        "sport": "futbol",
        "emoji": "⚽"
    },
    "Liga Femenina Basketball": {
        "folder": "08_Liga_Femenina_Basketball",
        "escudos": "01_Escudos",
        "misc": "4- Miscelaneo",
        "league_logo_file": None,
        "sport": "basketball",
        "emoji": "🏀"
    },
    "Liga Solo Futbol": {
        "folder": "09_Liga_Solo_Futbol",
        "escudos": "01_Escudos",
        "misc": None,
        "league_logo_file": None,
        "sport": "futbol",
        "emoji": "⚽"
    },
    "Liga Futbol Americano": {
        "folder": "10_Liga_Futbol_Americano",
        "escudos": "01_Escudos",
        "misc": None,
        "league_logo_file": None,
        "sport": "americano",
        "emoji": "🏈"
    },
    "Liga Senior Maldonado": {
        "folder": "11_Liga_Senior_Maldonado",
        "escudos": "01_Escudos",
        "misc": None,
        "league_logo_file": None,
        "sport": "futbol",
        "emoji": "⚽"
    },
    "Liga PRO": {
        "folder": "12_Liga_PRO",
        "escudos": "1-ESCUDOS (sin fondo)",
        "escudos_alt": "1-ESCUDOS JPG",
        "misc": "MICELANEO",
        "league_logo_file": None,
        "sport": "futbol",
        "emoji": "🏆"
    },
    "Liga OFI": {
        "folder": "13_Liga_OFI",
        "escudos": "01_Escudos",
        "misc": None,
        "league_logo_file": None,
        "sport": "futbol",
        "emoji": "⚽"
    },
    "Liga LVH": {
        "folder": "14_Liga_LVH",
        "escudos": "01_Escudos",
        "misc": "Micelano",
        "league_logo_file": None,
        "sport": "futbol",
        "emoji": "⚽"
    },
    "Liga Solymar": {
        "folder": "15_Liga_Solymar_Nuevo",
        "escudos": "01_Escudos",
        "misc": None,
        "league_logo_file": None,
        "sport": "futbol",
        "emoji": "⚽"
    },
    "Liga Uruguay": {
        "folder": "16 - Liga_Uruguay",
        "escudos": "1 - Escudos",
        "misc": "3 - Miscelaneo",
        "league_logo_file": None,
        "sport": "futbol",
        "emoji": "🇺🇾"
    },
    "Liga América": {
        "folder": "17 Liga AMérica",
        "escudos": "01_Escudos",
        "misc": None,
        "league_logo_file": None,
        "sport": "futbol",
        "emoji": "🌎"
    },
    "Livosur": {
        "folder": "18_Livosur",
        "escudos": "1 - Escudos",
        "misc": "2 - Miscelaneo",
        "league_logo_file": None,
        "sport": "volleyball",
        "emoji": "🏐"
    },
    "Liga MVD": {
        "folder": "19_Liga_MVD",
        "escudos": "1 - Escudos",
        "misc": "3 - Miscelaneo",
        "league_logo_file": None,
        "sport": "futbol",
        "emoji": "🏟️"
    },
}

# ─────────────────────────────────────────────
# CARGA DE CONFIG.JSON (para aliases de equipos)
# ─────────────────────────────────────────────
def load_config():
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️  No se pudo cargar config.json: {e}")
        return {"leagues": {}}

CONFIG = load_config()

# ─────────────────────────────────────────────
# UTILIDADES DE RUTA
# ─────────────────────────────────────────────
def get_league_escudos_path(league_name):
    """Devuelve el Path a la carpeta de escudos de la liga."""
    info = LEAGUES_MAP.get(league_name)
    if not info:
        return None

    folder_base = MAC_LIGAS_BASE / info["folder"]

    # Intentar carpeta principal de escudos
    path = folder_base / info["escudos"]
    if path.exists():
        return path

    # Intentar carpeta alternativa (escudos_alt)
    alt = info.get("escudos_alt")
    if alt:
        path_alt = folder_base / alt
        if path_alt.exists():
            return path_alt

    # Buscar cualquier carpeta que contenga "escudo" en el nombre
    if folder_base.exists():
        for sub in folder_base.iterdir():
            if sub.is_dir() and 'escudo' in sub.name.lower():
                return sub

    return None

def get_output_path(league_name):
    """Devuelve el Path de salida usando ScoreboardGenerator (config.json)."""
    import sys
    sys.path.insert(0, str(GRAPHICS_DIR))
    try:
        from generate_graphics import ScoreboardGenerator
        gen = ScoreboardGenerator(league_name=league_name)
        gen.output_dir.mkdir(parents=True, exist_ok=True)
        return gen.output_dir
    except Exception:
        pass
    # Fallback
    info = LEAGUES_MAP.get(league_name)
    folder_num = info["folder"][:2] if info else "00"
    out_path = MAC_LIGAS_BASE / "BUHO_VISION_MAIN_CLAUDE" / "Output" / f"{folder_num}_{league_name.replace(' ', '_')}"
    out_path.mkdir(parents=True, exist_ok=True)
    return out_path

def normalize(text):
    """Normaliza texto: quita acentos, pasa a mayúsculas."""
    nfkd = unicodedata.normalize('NFD', text)
    return ''.join(c for c in nfkd if not unicodedata.combining(c)).upper()

_SUFFIX_RE = re.compile(
    r'\s*\(\s*\+?\d+\s*\)'          # (+30), (+ 40), (30)
    r'|\s*\+\s*\d+'                  # +30, +40, + 30
    r'|\s*\(\s*(?:Dom|Lun|Mar|Mié|Mie|Jue|Vie|Sáb|Sab|Vie)\b[^)]*\)'  # (Dom), (Mie. Nasazzi)
    r'|\s*F\.?[Cc]\.?\s*$'          # trailing F.C / Fc  (solo si queda suelto — ver abajo)
    , re.IGNORECASE
)

def strip_team_display(name: str) -> str:
    """Quita sufijos de día/categoría del nombre de equipo para mostrar en el gráfico.
    Ejemplos:
      'El Clan FC (+30)'   → 'El Clan FC'
      'Berges F.c +30'     → 'Berges F.c'
      'Lyon Fc (Dom)'      → 'Lyon Fc'
      'Decia el Otro (Mie)' → 'Decia el Otro'
    """
    cleaned = re.sub(
        r'\s*\(\s*\+?\d+\s*\)'
        r'|\s*\+\s*\d+'
        r'|\s*\(\s*(?:Dom|Lun|Mar|Mié|Mie|Jue|Vie|Sáb|Sab)[^)]*\)',
        '', name, flags=re.IGNORECASE
    ).strip()
    return cleaned if cleaned else name

def find_logo(league_name, team_name):
    """
    Busca el logo del equipo en la carpeta de escudos de la liga.
    Retorna Path o None.
    """
    # Resolver alias desde config.json
    league_cfg = CONFIG.get("leagues", {}).get(league_name, {})
    aliases = league_cfg.get("team_aliases", {})
    resolved = aliases.get(team_name) or aliases.get(team_name.upper()) or aliases.get(team_name.lower()) or team_name

    escudos_dir = get_league_escudos_path(league_name)
    local_exists = escudos_dir and escudos_dir.exists()

    # Cloud mode: try Firebase Hosting if local not available
    if CLOUD_MODE or not local_exists:
        league_info = LEAGUES_MAP.get(league_name, {})
        folder = league_info.get("folder", "")
        if folder:
            variants_cloud = [
                resolved,
                resolved.replace(" ", "_"),
                resolved.replace("_", " "),
                team_name,
                team_name.replace(" ", "_"),
                team_name.upper(),
                team_name.upper().replace(" ", "_"),
            ]
            for variant in variants_cloud:
                for ext in [".png", ".jpg", ".jpeg"]:
                    cached = _download_logo_from_hosting(folder, f"{variant}{ext}")
                    if cached:
                        return cached
        if CLOUD_MODE:
            return None

    if not local_exists:
        return None

    extensions = ['.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG']

    # Incluir versión con sufijos (nombre original de la API) para encontrar logos descargados
    original_name = team_name
    stripped_name = strip_team_display(team_name)

    variants = [
        resolved,
        resolved.replace(' ', '_'),
        resolved.replace('_', ' '),
        team_name,
        team_name.replace(' ', '_'),
        stripped_name,
        stripped_name.replace(' ', '_'),
        team_name.upper(),
        team_name.upper().replace(' ', '_'),
    ]

    for variant in variants:
        for ext in extensions:
            candidate = escudos_dir / f"{variant}{ext}"
            if candidate.exists():
                return candidate

    # Búsqueda insensible a mayúsculas y acentos
    try:
        files = list(escudos_dir.iterdir())
    except Exception:
        return None

    team_norm = normalize(resolved)
    stripped_norm = normalize(stripped_name)
    for f in files:
        if f.suffix.lower() in ['.png', '.jpg', '.jpeg']:
            f_norm = normalize(f.stem)
            if f_norm in (team_norm, normalize(team_name), stripped_norm):
                return f
            # Comparación parcial
            if team_norm in f_norm or f_norm in team_norm:
                return f
            if stripped_norm in f_norm or f_norm in stripped_norm:
                return f

    return None

def get_local_ip():
    """Obtiene la IP local de la red (no 127.0.0.1)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

# ─────────────────────────────────────────────
# ENDPOINTS API
# ─────────────────────────────────────────────

@app.route('/')
def index():
    """Sirve la app principal Buho Vision (accesible desde cualquier dispositivo en la red)."""
    from flask import make_response
    # Prioridad 1: buhovision_app.html en el mismo directorio que el servidor
    main_app = BASE_DIR / "buhovision_app.html"
    if main_app.exists():
        resp = make_response(send_file(main_app))
        resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        resp.headers['Pragma'] = 'no-cache'
        return resp
    # Prioridad 2: app real en Desktop de Mac
    desktop_app = Path.home() / "Desktop" / "buhovision_COMPARTIR (1).html"
    if desktop_app.exists():
        resp = make_response(send_file(desktop_app))
        resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        resp.headers['Pragma'] = 'no-cache'
        return resp
    # Fallback: ecosystem_app en templates
    template_path = BASE_DIR / "templates" / "ecosystem_app.html"
    if template_path.exists():
        resp = make_response(send_file(template_path))
        resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        resp.headers['Pragma'] = 'no-cache'
        return resp
    ip = get_local_ip()
    return f"<h1>🦉 Buho Vision Server</h1><p>Servidor online en {ip}:5000</p><p>Archivo de app no encontrado.</p>", 404

@app.route('/static/<path:filename>')
def static_files(filename):
    """Sirve archivos estáticos."""
    static_dir = BASE_DIR / "static"
    static_dir.mkdir(exist_ok=True)
    # También buscar el logo en 5_Production_Calendar
    calendar_dir = BASE_DIR / "5_Production_Calendar"
    for search_dir in [static_dir, calendar_dir, BASE_DIR]:
        candidate = search_dir / filename
        if candidate.exists():
            return send_file(candidate)
    abort(404)

@app.route('/api/status')
def api_status():
    return jsonify({
        "status": "ok",
        "version": "1.0",
        "server": "Buho Vision Ecosystem",
        "ip": get_local_ip(),
        "url": f"http://{get_local_ip()}:5000"
    })

@app.route('/api/network-ip')
def api_network_ip():
    ip = get_local_ip()
    return jsonify({
        "ip": ip,
        "port": 5000,
        "url": f"http://{ip}:5000"
    })

@app.route('/api/leagues')
def api_leagues():
    """Lista todas las ligas con información de logos."""
    result = []
    for league_name, info in LEAGUES_MAP.items():
        escudos_path = get_league_escudos_path(league_name)
        if escudos_path and escudos_path.exists():
            try:
                count = len([f for f in escudos_path.iterdir()
                             if f.suffix.lower() in ['.png', '.jpg', '.jpeg']])
            except Exception:
                count = 0
        else:
            count = 0

        result.append({
            "name": league_name,
            "sport": info.get("sport", "futbol"),
            "emoji": info.get("emoji", "⚽"),
            "logo_count": count,
            "has_logos": count > 0,
            "folder_exists": escudos_path is not None and escudos_path.exists()
        })
    return jsonify({"leagues": result})

@app.route('/api/teams/<league_name>')
def api_teams(league_name):
    """Lista los equipos de una liga con sus logos."""
    from urllib.parse import unquote
    league_name = unquote(league_name)

    escudos_path = get_league_escudos_path(league_name)
    if not escudos_path or not escudos_path.exists():
        return jsonify({"league": league_name, "teams": [], "error": "Carpeta no encontrada"})

    # Obtener aliases del config
    league_cfg = CONFIG.get("leagues", {}).get(league_name, {})
    aliases_reverse = {}  # filename_stem → display_name
    for display, filename in league_cfg.get("team_aliases", {}).items():
        if filename not in aliases_reverse:
            aliases_reverse[filename] = display.upper()

    teams = []
    try:
        for f in sorted(escudos_path.iterdir()):
            if f.suffix.lower() in ['.png', '.jpg', '.jpeg']:
                stem = f.stem
                display_name = aliases_reverse.get(stem, stem.replace('_', ' '))
                teams.append({
                    "name": display_name.upper(),
                    "filename": stem,
                    "logo_url": f"/api/logo/{league_name}/{stem}",
                    "has_logo": True
                })
    except Exception as e:
        return jsonify({"league": league_name, "teams": [], "error": str(e)})

    return jsonify({"league": league_name, "teams": teams})

@app.route('/api/logo/<league_name>/<team_name>')
def api_logo(league_name, team_name):
    """Sirve la imagen del escudo del equipo."""
    from urllib.parse import unquote
    league_name = unquote(league_name)
    team_name = unquote(team_name)

    logo_path = find_logo(league_name, team_name)
    if logo_path and logo_path.exists():
        return send_file(logo_path)

    # Devolver PNG transparente 1x1 si no se encuentra
    import base64
    transparent_png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    )
    return send_file(
        io.BytesIO(transparent_png),
        mimetype='image/png',
        as_attachment=False
    )

@app.route('/api/league-logo/<league_name>')
def api_league_logo(league_name):
    """Sirve el logo de la liga."""
    from urllib.parse import unquote
    league_name = unquote(league_name)

    info = LEAGUES_MAP.get(league_name)
    if info and info.get("misc") and info.get("league_logo_file"):
        logo_path = MAC_LIGAS_BASE / info["folder"] / info["misc"] / info["league_logo_file"]
        if logo_path.exists():
            return send_file(logo_path)

    # Buscar en config.json
    league_cfg = CONFIG.get("leagues", {}).get(league_name, {})
    for key in ["league_logo", "league_logo_mac"]:
        logo = league_cfg.get(key, "")
        if logo and not logo.startswith("G:") and Path(logo).exists():
            return send_file(Path(logo))

    # Buscar cualquier PNG en misc
    if info and info.get("misc"):
        misc_path = MAC_LIGAS_BASE / info["folder"] / info["misc"]
        if misc_path.exists():
            for f in misc_path.iterdir():
                if f.suffix.lower() in ['.png', '.jpg', '.jpeg'] and 'liga' in f.name.lower():
                    return send_file(f)

    # Transparente como fallback
    import base64
    transparent_png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
    )
    return send_file(io.BytesIO(transparent_png), mimetype='image/png')

@app.route('/api/generate-graphic', methods=['POST'])
def api_generate_graphic():
    """
    Genera UN gráfico de scoreboard.
    Body: {"league": "Liga Kings", "home_team": "LA NOCHE", "away_team": "LA CREMA",
           "home_score": "3", "away_score": "1"}
    Retorna: PNG file
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Se requiere JSON"}), 400

    league = data.get("league", "")
    home_team = data.get("home_team", "").upper()
    away_team = data.get("away_team", "").upper()
    home_score = str(data.get("home_score", "0"))
    away_score = str(data.get("away_score", "0"))

    if not all([league, home_team, away_team]):
        return jsonify({"error": "Faltan datos: league, home_team, away_team"}), 400

    png_data = generate_scoreboard_png(league, home_team, away_team, home_score, away_score)
    if png_data is None:
        return jsonify({"error": "No se pudo generar el gráfico. Verificar que Playwright esté instalado."}), 500

    filename = f"{home_team} VS {away_team} {league}.png"
    # Guardar en carpeta de salida
    try:
        out_dir = get_output_path(league)
        (out_dir / filename).write_bytes(png_data)
    except Exception:
        pass

    return send_file(
        io.BytesIO(png_data),
        mimetype='image/png',
        as_attachment=True,
        download_name=filename
    )

@app.route('/api/generate-batch', methods=['POST'])
def api_generate_batch():
    """
    Genera múltiples gráficos y retorna un ZIP.
    Body: {"league": "Liga Kings", "fecha": 1,
           "games": [{"home": "LA NOCHE", "away": "LA CREMA", "home_score": "3", "away_score": "1"}]}
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Se requiere JSON"}), 400

    league = data.get("league", "")
    fecha = data.get("fecha", 1)
    games = data.get("games", [])

    if not games:
        return jsonify({"error": "No hay partidos para generar"}), 400

    zip_buffer = io.BytesIO()
    generated = 0
    errors = []

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for game in games:
            home = game.get("home", "").upper()
            away = game.get("away", "").upper()
            home_score = str(game.get("home_score", "0"))
            away_score = str(game.get("away_score", "0"))

            if not home or not away:
                continue

            png_data = generate_scoreboard_png(league, home, away, home_score, away_score)
            if png_data:
                filename = f"{home} VS {away} {league}.png"
                zf.writestr(filename, png_data)
                # Guardar también en carpeta de salida
                try:
                    out_dir = get_output_path(league)
                    (out_dir / filename).write_bytes(png_data)
                except Exception:
                    pass
                generated += 1
            else:
                errors.append(f"{home} vs {away}")

    if generated == 0:
        return jsonify({
            "error": "No se generó ningún gráfico",
            "details": errors,
            "hint": "Verificar que Playwright esté instalado: pip install playwright && playwright install chromium"
        }), 500

    zip_buffer.seek(0)
    zip_name = f"Fecha_{fecha}_{league.replace(' ', '_')}.zip"
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name=zip_name
    )

@app.route('/api/generated-graphics')
def api_generated_graphics():
    """Lista los gráficos generados recientemente."""
    league_filter = request.args.get('league', '')
    graphics = []

    for league_name in LEAGUES_MAP:
        if league_filter and league_filter != league_name:
            continue
        try:
            out_dir = get_output_path(league_name)
            if not out_dir.exists():
                continue
            for f in sorted(out_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
                if f.suffix.lower() == '.png':
                    graphics.append({
                        "filename": f.name,
                        "league": league_name,
                        "url": f"/api/graphic-file/{league_name}/{f.name}",
                        "size": f.stat().st_size,
                        "modified": f.stat().st_mtime
                    })
        except Exception:
            continue

    return jsonify({"graphics": graphics[:200]})  # Máximo 200

@app.route('/api/graphic-file/<league_name>/<filename>')
def api_graphic_file(league_name, filename):
    """Sirve un gráfico generado."""
    from urllib.parse import unquote
    league_name = unquote(league_name)
    filename = unquote(filename)

    try:
        out_dir = get_output_path(league_name)
        file_path = out_dir / filename
        if file_path.exists():
            return send_file(file_path)
    except Exception:
        pass
    abort(404)

# ─────────────────────────────────────────────
# GENERACIÓN DE GRÁFICOS CON PLAYWRIGHT
# ─────────────────────────────────────────────

def logo_to_base64(logo_path):
    """Convierte una imagen a base64 para embeber en HTML."""
    if not logo_path or not Path(logo_path).exists():
        return None
    try:
        import base64
        with open(logo_path, 'rb') as f:
            data = f.read()
        ext = Path(logo_path).suffix.lower().replace('.', '')
        if ext == 'jpg':
            ext = 'jpeg'
        return f"data:image/{ext};base64,{base64.b64encode(data).decode()}"
    except Exception:
        return None

def generate_scoreboard_html(league, home_team, away_team, home_score, away_score):
    """Genera el HTML del scoreboard con los logos embebidos en base64."""

    # Encontrar logos
    home_logo_path = find_logo(league, home_team)
    away_logo_path = find_logo(league, away_team)

    home_logo_b64 = logo_to_base64(home_logo_path)
    away_logo_b64 = logo_to_base64(away_logo_path)

    # Logo de la liga
    league_info = LEAGUES_MAP.get(league, {})
    league_logo_path = None
    if league_info.get("misc") and league_info.get("league_logo_file"):
        candidate = MAC_LIGAS_BASE / league_info["folder"] / league_info["misc"] / league_info["league_logo_file"]
        if candidate.exists():
            league_logo_path = candidate

    if not league_logo_path:
        league_cfg = CONFIG.get("leagues", {}).get(league, {})
        for key in ["league_logo", "league_logo_mac"]:
            logo = league_cfg.get(key, "")
            if logo and not logo.startswith("G:") and Path(logo).exists():
                league_logo_path = Path(logo)
                break

    league_logo_b64 = logo_to_base64(league_logo_path)

    # Iniciales para placeholder
    home_initials = ''.join(w[0] for w in home_team.split()[:2]).upper()
    away_initials = ''.join(w[0] for w in away_team.split()[:2]).upper()

    def logo_or_placeholder(b64, initials, side):
        if b64:
            return f'<img src="{b64}" alt="{initials}" style="width:70px;height:70px;object-fit:contain;">'
        return f'<div style="width:70px;height:70px;border-radius:50%;background:linear-gradient(135deg,#0066cc,#004499);display:flex;align-items:center;justify-content:center;color:white;font-size:22px;font-weight:900;">{initials}</div>'

    home_logo_html = logo_or_placeholder(home_logo_b64, home_initials, "home")
    away_logo_html = logo_or_placeholder(away_logo_b64, away_initials, "away")

    league_logo_html = ""
    if league_logo_b64:
        league_logo_html = f'<img src="{league_logo_b64}" alt="{league}" style="width:60px;height:60px;object-fit:contain;">'
    else:
        league_logo_html = f'<div style="font-size:11px;font-weight:700;color:#0066cc;text-align:center;max-width:80px;">{league.upper()}</div>'

    home_name_display = home_team[:18] + "..." if len(home_team) > 18 else home_team
    away_name_display = away_team[:18] + "..." if len(away_team) > 18 else away_team

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ width: 1400px; height: 250px; background: transparent; overflow: hidden; }}
  .scoreboard {{
    width: 1400px; height: 250px;
    display: flex; align-items: center;
    background: linear-gradient(135deg, #e8e8e8 0%, #c0c0c0 50%, #a0a0a0 100%);
    border: 3px solid #606060;
    border-radius: 15px;
    box-shadow: 0 5px 20px rgba(0,0,0,0.3), inset 0 2px 5px rgba(255,255,255,0.5);
    position: relative;
    overflow: hidden;
  }}
  .accent-bar {{
    position: absolute; top: 0; left: 0; right: 0; height: 8px;
    background: linear-gradient(90deg, #0066cc, #0099ff, #0066cc);
  }}
  .team-section {{
    display: flex; align-items: center; gap: 15px;
    padding: 20px 25px; flex: 1;
  }}
  .team-left {{ flex-direction: row; }}
  .team-right {{ flex-direction: row-reverse; text-align: right; }}
  .team-name {{
    font-family: 'Arial Black', Arial, sans-serif;
    font-size: 38px; font-weight: 900;
    color: #1a1a1a; text-transform: uppercase;
    text-shadow: 1px 1px 2px rgba(255,255,255,0.5);
    line-height: 1.1;
  }}
  .center-section {{
    display: flex; flex-direction: column; align-items: center;
    gap: 8px; padding: 0 20px; flex-shrink: 0;
  }}
  .score-display {{
    display: flex; align-items: center; gap: 15px;
    background: linear-gradient(135deg, #ffffff, #e0e0e0);
    border: 3px solid #0066cc; border-radius: 50px;
    padding: 8px 25px;
    box-shadow: 0 4px 15px rgba(0,102,204,0.3);
  }}
  .score {{
    font-family: 'Arial Black', Arial, sans-serif;
    font-size: 64px; font-weight: 900; color: #0066cc;
    min-width: 60px; text-align: center; line-height: 1;
  }}
  .score-separator {{
    font-size: 48px; color: #606060; font-weight: 900;
  }}
</style>
</head>
<body>
<div class="scoreboard">
  <div class="accent-bar"></div>
  <div class="team-section team-left">
    {home_logo_html}
    <div class="team-name">{home_name_display}</div>
  </div>
  <div class="center-section">
    {league_logo_html}
    <div class="score-display">
      <div class="score">{home_score}</div>
      <div class="score-separator">-</div>
      <div class="score">{away_score}</div>
    </div>
  </div>
  <div class="team-section team-right">
    <div class="team-name">{away_name_display}</div>
    {away_logo_html}
  </div>
</div>
</body>
</html>"""
    return html

def generate_scoreboard_png(league, home_team, away_team, home_score, away_score):
    """
    Genera un PNG usando ScoreboardGenerator de 2_Graphics_Generation/generate_graphics.py
    y su scoreboard_template.html — exactamente igual a como lo hace graphics generation.
    """
    import asyncio, sys, base64 as b64mod

    sys.path.insert(0, str(GRAPHICS_DIR))
    sys.path.insert(0, str(GRAPHICS_DIR.parent / "1_Data_Input"))

    try:
        from generate_graphics import ScoreboardGenerator
        from data_parser import GameData
    except ImportError as e:
        print(f"❌ No se pudo importar ScoreboardGenerator: {e}")
        return None

    try:
        generator = ScoreboardGenerator(league_name=league)
    except Exception as e:
        print(f"❌ Error creando ScoreboardGenerator para '{league}': {e}")
        return None

    # Usar find_logo del generador (usa config.json + aliases)
    home_logo_path, _ = generator.find_logo(home_team)
    away_logo_path, _ = generator.find_logo(away_team)

    def to_data_url(path):
        if not path or path == "PLACEHOLDER":
            return ""
        import threading
        result = [""]
        def _read():
            try:
                p = Path(path)
                ext = p.suffix.lower().lstrip('.')
                mime = "image/png" if ext == "png" else f"image/{ext}"
                with open(p, "rb") as f:
                    data = b64mod.b64encode(f.read()).decode("utf-8")
                result[0] = f"data:{mime};base64,{data}"
            except Exception:
                pass
        t = threading.Thread(target=_read, daemon=True)
        t.start()
        t.join(timeout=3)  # máximo 3 segundos por logo
        return result[0]

    home_logo_b64  = to_data_url(home_logo_path)  if home_logo_path  != "PLACEHOLDER" else ""
    away_logo_b64  = to_data_url(away_logo_path)  if away_logo_path  != "PLACEHOLDER" else ""
    league_logo_b64 = to_data_url(str(generator.league_logo_path)) if generator.league_logo_path and generator.league_logo_path.exists() else ""

    scoreboard_data = {
        "homeTeam":        strip_team_display(home_team),
        "awayTeam":        strip_team_display(away_team),
        "homeScore":       str(home_score),
        "awayScore":       str(away_score),
        "homeLogo":        home_logo_b64,
        "awayLogo":        away_logo_b64,
        "leagueLogo":      league_logo_b64,
        "homePlaceholder": not bool(home_logo_b64),
        "awayPlaceholder": not bool(away_logo_b64),
    }

    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 2000, "height": 400})
            page.goto(generator.template_path.as_uri(), wait_until="domcontentloaded")
            page.evaluate("(data) => updateScoreboard(data)", scoreboard_data)
            page.wait_for_timeout(500)
            el = page.query_selector('.scoreboard-wrapper')
            png_bytes = el.screenshot(type="png", omit_background=True) if el else \
                        page.screenshot(type="png", omit_background=True)
            browser.close()
            return png_bytes
    except ImportError:
        print("❌ Playwright no instalado. Ejecutar: pip install playwright && playwright install chromium")
        return None
    except Exception as e:
        print(f"❌ Error generando gráfico: {e}")
        return None

@app.route('/api/scrape-fixture', methods=['POST'])
def api_scrape_fixture():
    """Abre una URL con Playwright y extrae el texto del fixture (Liga MVD, Liga PRO, etc.)"""
    data = request.get_json()
    url = (data or {}).get('url', '').strip()
    if not url:
        return jsonify({'error': 'URL requerida'}), 400

    try:
        import requests as req_lib
        from html.parser import HTMLParser

        # ── Liga MVD: usa Playwright para mantener sesión y llamar fixtures_show.php ──
        if 'ligamvd.com' in url:
            if not url.startswith('http'):
                url = 'https://www.ligamvd.com' + url

            etapa = str((data or {}).get('etapa', '1')).strip() or '1'

            # Detectar torneo_id y etapa desde la URL
            # Formato /fixtures/{slug}/{torneo_id}/{etapa}/
            m_fix = re.search(r'/fixtures/[^/]+/(\d+)/(\d+)/?', url)
            # Formato /home/{liga_id}/{serie_id}/ — no usamos fixtures en este caso
            m_home = re.search(r'/home/(\d+)/(\d+)/?', url)

            torneo_id = None
            if m_fix:
                torneo_id = m_fix.group(1)
                if (data or {}).get('etapa') in (None, '', '1', 1):
                    etapa = m_fix.group(2)
            elif m_home:
                # Para URLs /home/, buscamos el torneo activo en la página
                pass
            else:
                # Fallback: tomar el número grande de la URL
                url_nums = re.findall(r'/(\d+)', url)
                big = [n for n in url_nums if int(n) > 100]
                if big:
                    torneo_id = big[0]
                    small = [n for n in url_nums[url_nums.index(torneo_id)+1:] if int(n) <= 30]
                    if small and (data or {}).get('etapa') in (None, '', '1', 1):
                        etapa = small[0]

            try:
                from playwright.sync_api import sync_playwright
                from bs4 import BeautifulSoup as _BS
            except ImportError as ie:
                return jsonify({'error': f'Dependencia faltante: {ie}'}), 500

            games = []
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                page = browser.new_page()
                # Cargar la home para inicializar sesión/cookies
                init_url = 'https://www.ligamvd.com/home/9/3/' if not m_home else url
                page.goto(init_url, timeout=25000, wait_until='networkidle')

                if torneo_id:
                    # Llamar fixtures_show.php desde el contexto del browser (con cookies)
                    html = page.evaluate(f'''async () => {{
                        const r = await fetch('/fixtures_show.php', {{
                            method: 'POST',
                            headers: {{'Content-Type':'application/x-www-form-urlencoded','X-Requested-With':'XMLHttpRequest'}},
                            body: 'torneo_id={torneo_id}&fixture_etapa={etapa}'
                        }});
                        return await r.text();
                    }}''')
                    soup = _BS(html, 'html.parser')
                    rows = soup.find_all('tr')
                    for row in rows[1:]:
                        cells = [td.get_text(strip=True) for td in row.find_all('td')]
                        # Formato: [fecha, hora, cancha, local, gol_local, gol_visit, visitante, extra?]
                        if len(cells) >= 7 and cells[3] and cells[6] and cells[4].isdigit() and cells[5].isdigit():
                            games.append({
                                'home':  cells[3].upper(),
                                'away':  cells[6].upper(),
                                'score': f"{cells[4]}-{cells[5]}",
                                'date':  cells[0],
                                'raw':   f"{cells[3]} {cells[4]}-{cells[5]} {cells[6]}"
                            })
                else:
                    # Para /home/ URLs: extraer resultados del texto de la página renderizada
                    import time as _t
                    _t.sleep(3)
                    body_text = page.inner_text('body')
                    # Buscar patrones "EQUIPO1 N - EQUIPO2 M" en el texto
                    pat = re.compile(r'([A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÜÑa-záéíóúüñ0-9\s.\-\']+?)\s+(\d{1,2})\s*-\s*(\d{1,2})\s+([A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÜÑa-záéíóúüñ0-9\s.\-\']+)')
                    seen = set()
                    for m in pat.finditer(body_text):
                        h = m.group(1).strip().upper()
                        a = m.group(4).strip().split('\n')[0].upper()
                        hs, as_ = m.group(2), m.group(3)
                        key = f"{h}|{a}"
                        if key not in seen and len(h) >= 3 and len(a) >= 3:
                            seen.add(key)
                            games.append({'home': h, 'away': a, 'score': f"{hs}-{as_}", 'raw': f"{h} {hs}-{as_} {a}"})

                browser.close()

            if not games:
                return jsonify({'error': f'Sin partidos con resultado para la fecha {etapa}. Verificá el número de jornada.'}), 400

            return jsonify({'games': games, 'source': 'ligamvd'})

        # ── Liga PRO: REST API directa ──
        if 'ligapro.uy' in url:
            m = re.search(r'/campeonatos/(\d+)', url)
            if not m:
                return jsonify({'error': 'URL inválida — debe ser ligapro.uy/campeonatos/{id}'}), 400
            tournament_id = m.group(1)
            groupweek_id = (data or {}).get('groupweek_id')

            api = 'https://api.ligapro.uy/api'
            hdrs = {'Accept': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}

            # Datos del torneo
            r_t = req_lib.get(f'{api}/tournaments/{tournament_id}', headers=hdrs, timeout=10)
            r_t.raise_for_status()
            t_json = r_t.json()
            tournament = t_json.get('data', t_json)
            tournament_name = tournament.get('name', '')
            if not groupweek_id:
                groupweek_id = tournament.get('current_groupweek_id')

            # Jornadas
            r_gw = req_lib.get(f'{api}/tournaments/{tournament_id}/groupweeks', headers=hdrs, timeout=10)
            r_gw.raise_for_status()
            gw_json = r_gw.json()
            groupweeks_raw = gw_json.get('data', gw_json) if isinstance(gw_json, dict) else gw_json
            groupweeks = [{'id': g.get('id'), 'name': g.get('name', f"Fecha {g.get('order','?')}")}
                          for g in (groupweeks_raw if isinstance(groupweeks_raw, list) else [])]

            # Partidos de la jornada seleccionada
            games = []
            if groupweek_id:
                r_g = req_lib.get(f'{api}/tournaments/{tournament_id}/games',
                                  params={'filter[groupweek_id]': groupweek_id},
                                  headers=hdrs, timeout=10)
                r_g.raise_for_status()
                g_json = r_g.json()
                games_list = g_json.get('data', g_json) if isinstance(g_json, dict) else g_json
                for g in (games_list if isinstance(games_list, list) else []):
                    home = (g.get('local_team_name') or '').upper().strip()
                    away = (g.get('visiting_team_name') or '').upper().strip()
                    hs = str(g.get('local_team_result', '') or '')
                    as_ = str(g.get('visiting_team_result', '') or '')
                    if home and away:
                        score = f"{hs}-{as_}" if hs != '' and as_ != '' else ''
                        games.append({'home': home, 'away': away, 'score': score,
                                      'raw': f"{home} {hs}-{as_} {away}"})

            return jsonify({'source': 'ligapro', 'games': games, 'groupweeks': groupweeks,
                            'current_groupweek_id': groupweek_id, 'tournament_name': tournament_name})

        # ── Otros: Playwright headless ──
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={'width': 1280, 'height': 900})
            page.goto(url, wait_until='networkidle', timeout=35000)
            text = ''

            if 'ligapro.uy' in url:
                try:
                    for sel in ['a:has-text("Fixture")', 'button:has-text("Fixture")',
                                '[role="tab"]:has-text("Fixture")', 'li:has-text("Fixture")']:
                        try:
                            page.locator(sel).first.click(timeout=3000); break
                        except Exception:
                            pass
                    page.wait_for_load_state('networkidle', timeout=10000)
                    text = page.evaluate("""() => {
                        const lines = [];
                        document.querySelectorAll('tr, [class*="match"], [class*="partido"], [class*="fixture"], [class*="game"], [class*="row"]').forEach(el => {
                            const t = el.innerText.replace(/[\\n\\t]+/g,' ').replace(/\\s+/g,' ').trim();
                            if (t.length > 6 && /\\d/.test(t)) lines.push(t);
                        });
                        if (!lines.length) {
                            document.querySelectorAll('main, #__next').forEach(el => {
                                el.innerText.split('\\n').forEach(l => { const t=l.trim(); if(t.length>4) lines.push(t); });
                            });
                        }
                        return [...new Set(lines)].join('\\n');
                    }""")
                except Exception as e:
                    print(f"ligapro scrape error: {e}")

            if not text:
                text = page.locator('body').inner_text()
            browser.close()
            return jsonify({'text': text})

    except ImportError:
        return jsonify({'error': 'Playwright no instalado. Ejecutar: pip install playwright && playwright install chromium'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


_LP_HDR = {'Accept': 'application/json',
           'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
_LP_API = 'https://api.ligapro.uy/api'

@app.route('/api/ligapro/series')
def ligapro_series():
    """Devuelve todas las series activas con sus divisionales."""
    import requests as req_lib
    r = req_lib.get(f'{_LP_API}/tournaments/series',
                    params={'filter[status][0]': 141, 'sort[]': '-createdAt'},
                    headers=_LP_HDR, timeout=10)
    r.raise_for_status()
    return jsonify(r.json())

@app.route('/api/ligapro/torneos')
def ligapro_torneos():
    """Devuelve torneos para una serie+divisional (y opcionalmente categoría)."""
    import requests as req_lib
    params = {'filter[status][0]': 141}
    for k in ('serie', 'divisional', 'category'):
        v = request.args.get(k)
        if v:
            params[f'filter[{k}]'] = v
    r = req_lib.get(f'{_LP_API}/tournaments', params=params, headers=_LP_HDR, timeout=10)
    r.raise_for_status()
    return jsonify(r.json())

@app.route('/api/ligapro/jornadas')
def ligapro_jornadas():
    """Devuelve las jornadas de un torneo."""
    import requests as req_lib
    torneo_id = request.args.get('torneo_id', '')
    if not torneo_id:
        return jsonify({'error': 'torneo_id requerido'}), 400
    r = req_lib.get(f'{_LP_API}/tournaments/{torneo_id}/groupweeks',
                    headers=_LP_HDR, timeout=10)
    r.raise_for_status()
    return jsonify(r.json())

@app.route('/api/ligapro/resultados')
def ligapro_resultados():
    """Devuelve todos los partidos con resultado de un torneo y descarga logos faltantes."""
    import requests as req_lib, re as _re
    torneo_id = request.args.get('torneo_id', '')
    if not torneo_id:
        return jsonify({'error': 'torneo_id requerido'}), 400

    r = req_lib.get(f'{_LP_API}/tournaments/{torneo_id}/games', headers=_LP_HDR, timeout=10)
    r.raise_for_status()
    raw = r.json()
    games_raw = raw.get('data', raw) if isinstance(raw, dict) else raw

    # Carpeta de escudos Liga PRO
    escudos_dir = Path(MAC_LIGAS_BASE) / '12_Liga_PRO' / '1-ESCUDOS (sin fondo)'
    escudos_dir.mkdir(parents=True, exist_ok=True)

    def _safe_name(n):
        return _re.sub(r'[<>:"/\\|?*]', '', n).strip()[:60]

    def _download_logo(url, name):
        if not url or 'default' in url.lower() or 'arch/2.png' in url:
            return False
        ext = Path(url.split('?')[0]).suffix or '.jpg'
        dest = escudos_dir / f"{_safe_name(name)}{ext}"
        if dest.exists():
            return False
        try:
            resp = req_lib.get(url, headers=_LP_HDR, timeout=10)
            if resp.status_code == 200 and len(resp.content) > 500:
                dest.write_bytes(resp.content)
                return True
        except Exception:
            pass
        return False

    games = []
    logos_downloaded = 0
    for g in (games_raw if isinstance(games_raw, list) else []):
        home = (g.get('local_team_name') or '').strip()
        away = (g.get('visiting_team_name') or '').strip()
        hs = g.get('local_team_result')
        as_ = g.get('visiting_team_result')
        home_logo_url = g.get('local_team_logo', '')
        away_logo_url = g.get('visiting_team_logo', '')
        date = g.get('date', '')

        if not home or not away:
            continue

        # Download missing logos
        if _download_logo(home_logo_url, home):
            logos_downloaded += 1
        if _download_logo(away_logo_url, away):
            logos_downloaded += 1

        has_result = hs is not None and as_ is not None
        games.append({
            'home': home,
            'away': away,
            'home_display': strip_team_display(home),
            'away_display': strip_team_display(away),
            'home_score': str(hs) if hs is not None else '',
            'away_score': str(as_) if as_ is not None else '',
            'score': f"{hs}-{as_}" if has_result else '',
            'has_result': has_result,
            'home_logo': home_logo_url,
            'away_logo': away_logo_url,
            'date': date,
        })

    return jsonify({
        'games': games,
        'total': len(games),
        'with_result': sum(1 for g in games if g['has_result']),
        'logos_downloaded': logos_downloaded,
    })


@app.route('/api/preview-html', methods=['POST'])
def api_preview_html():
    """Retorna el HTML del scoreboard para preview en el browser."""
    data = request.get_json()
    if not data:
        return "Error", 400

    league = data.get("league", "")
    home_team = data.get("home_team", "EQUIPO LOCAL").upper()
    away_team = data.get("away_team", "EQUIPO VISITANTE").upper()
    home_score = str(data.get("home_score", "0"))
    away_score = str(data.get("away_score", "0"))

    html = generate_scoreboard_html(league, home_team, away_team, home_score, away_score)
    return html, 200, {'Content-Type': 'text/html; charset=utf-8'}

@app.route('/api/veo-cameras')
def api_veo_cameras():
    """Devuelve el inventario de cámaras escaneado desde Veo.co."""
    json_path = BASE_DIR / "1_Video_Download" / "veo_cameras.json"
    if not json_path.exists():
        return jsonify({"error": "veo_cameras.json no encontrado. Ejecutar veo_camera_scan.py"}), 404
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
        return jsonify({"cameras": data, "total": len(data), "source": str(json_path)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/parse-image', methods=['POST'])
def api_parse_image():
    """
    Recibe una imagen (base64 o multipart) y extrae resultados de partidos usando Claude vision.
    Retorna: {"games": [{"home": "...", "away": "...", "home_score": "N", "away_score": "N"}]}
    """
    import base64 as b64mod

    # Aceptar multipart/form-data (upload) o JSON con base64
    if request.content_type and 'multipart' in request.content_type:
        f = request.files.get('image')
        if not f:
            return jsonify({'error': 'No se recibió imagen'}), 400
        img_bytes = f.read()
        mime = f.content_type or 'image/jpeg'
    else:
        data = request.get_json() or {}
        img_b64 = data.get('image', '')
        if not img_b64:
            return jsonify({'error': 'Se requiere campo image (base64)'}), 400
        if ',' in img_b64:
            header, img_b64 = img_b64.split(',', 1)
            mime = header.split(':')[1].split(';')[0] if ':' in header else 'image/jpeg'
        else:
            mime = 'image/jpeg'
        img_bytes = b64mod.b64decode(img_b64)

    img_b64_str = b64mod.b64encode(img_bytes).decode('utf-8')

    try:
        import anthropic
        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": mime, "data": img_b64_str}
                    },
                    {
                        "type": "text",
                        "text": (
                            "Extraé todos los resultados de partidos que aparecen en esta imagen de fixture/resultados deportivos. "
                            "Devolvé SOLO un JSON válido con este formato exacto, sin markdown ni texto adicional:\n"
                            "[{\"home\": \"NOMBRE EQUIPO LOCAL\", \"away\": \"NOMBRE EQUIPO VISITANTE\", "
                            "\"home_score\": \"N\", \"away_score\": \"N\"}]\n"
                            "Solo incluí partidos con resultado numérico. "
                            "Los nombres de los equipos exactamente como aparecen en la imagen. "
                            "Si no hay resultados o la imagen no es un fixture deportivo, devolvé []."
                        )
                    }
                ]
            }]
        )
        raw = response.content[0].text.strip()
        # Limpiar posible markdown
        if raw.startswith('```'):
            raw = raw.split('\n', 1)[1] if '\n' in raw else raw
            raw = raw.rsplit('```', 1)[0].strip()
        games = json.loads(raw)
        return jsonify({'games': games, 'source': 'vision'})
    except ImportError:
        return jsonify({'error': 'anthropic no instalado. Ejecutar: pip install anthropic'}), 500
    except json.JSONDecodeError as e:
        return jsonify({'error': f'No se pudo parsear respuesta: {e}', 'raw': raw}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/logo-files/<path:league_name>')
def api_logo_files(league_name):
    """Devuelve lista de archivos de logos disponibles para una liga."""
    escudos_dir = get_league_escudos_path(league_name)
    if not escudos_dir or not escudos_dir.exists():
        return jsonify({'files': []})
    files = sorted([f.stem for f in escudos_dir.iterdir()
                    if f.is_file() and f.suffix.lower() in ('.png','.jpg','.jpeg','.svg')])
    return jsonify({'files': files})


@app.route('/api/save-alias', methods=['POST'])
def api_save_alias():
    """
    Guarda un alias de equipo en config.json.
    Body: {"league": "Liga Kings", "team_name": "Bayern Leverkusen", "alias": "BAYER_LEVERKUSEN"}
    """
    data = request.get_json() or {}
    league     = data.get('league', '').strip()
    team_name  = data.get('team_name', '').strip()
    alias      = data.get('alias', '').strip()

    if not league or not team_name or not alias:
        return jsonify({'error': 'Faltan campos: league, team_name, alias'}), 400

    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            cfg = json.load(f)

        leagues = cfg.setdefault('leagues', {})
        if league not in leagues:
            leagues[league] = {}
        aliases = leagues[league].setdefault('team_aliases', {})

        # Guardar el alias en todas las variantes de capitalización comunes
        aliases[team_name]            = alias
        aliases[team_name.upper()]    = alias
        aliases[team_name.lower()]    = alias
        aliases[team_name.title()]    = alias

        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)

        # Recargar config global
        global CONFIG
        CONFIG = cfg

        return jsonify({'ok': True, 'saved': f'{team_name} → {alias}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/check-logos', methods=['POST'])
def api_check_logos():
    """
    Verifica si los equipos tienen logo disponible.
    Body: {"league": "Liga Kings", "teams": ["Bayern Leverkusen", "El Ombligo"]}
    Retorna: {"results": [{"team": "...", "found": true/false, "file": "..."}]}
    """
    data = request.get_json() or {}
    league = data.get('league', '')
    teams  = data.get('teams', [])

    sys.path.insert(0, str(GRAPHICS_DIR))
    try:
        from generate_graphics import ScoreboardGenerator
        gen = ScoreboardGenerator(league_name=league)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    results = []
    for team in teams:
        logo_path, _ = gen.find_logo(team)
        results.append({
            'team': team,
            'found': logo_path != 'PLACEHOLDER',
            'file': logo_path if logo_path != 'PLACEHOLDER' else None
        })
    return jsonify({'results': results})


@app.route('/marcadores')
def marcadores_page():
    """Sirve la app de generación de marcadores."""
    page = BASE_DIR / "templates" / "marcadores.html"
    if page.exists():
        from flask import make_response
        resp = make_response(send_file(page))
        resp.headers['Cache-Control'] = 'no-store'
        return resp
    return "<h1>marcadores.html no encontrado</h1>", 404

@app.route('/api/generate-basketball-quarters', methods=['POST'])
def api_generate_basketball_quarters():
    """
    Genera 4 gráficos de básquetbol (1C, 2C, 3C, FINAL) y retorna un ZIP.
    Body: {
      "league": "Liga Femenina Basketball",
      "home_team": "Lagomar Country Club",
      "away_team": "Cordon",
      "home_quarters": [35, 16, 20, 22],
      "away_quarters": [12, 7, 11, 26]
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Se requiere JSON"}), 400

    league      = data.get("league", "Liga Femenina Basketball")
    home_team   = data.get("home_team", "")
    away_team   = data.get("away_team", "")
    home_q      = data.get("home_quarters", [])
    away_q      = data.get("away_quarters", [])

    if not home_team or not away_team or len(home_q) != 4 or len(away_q) != 4:
        return jsonify({"error": "Faltan datos: home_team, away_team, home_quarters[4], away_quarters[4]"}), 400

    sys.path.insert(0, str(GRAPHICS_DIR))
    sys.path.insert(0, str(GRAPHICS_DIR.parent / "1_Data_Input"))

    try:
        from generate_basketball_quarters import BasketballQuartersGenerator
        from basketball_parser import BasketballGame, QuarterScore
    except ImportError as e:
        return jsonify({"error": f"No se pudo importar el generador: {e}"}), 500

    try:
        gen = BasketballQuartersGenerator(league_name=league)
    except Exception as e:
        return jsonify({"error": f"Error creando generador: {e}"}), 500

    # Construir objeto de juego
    quarters = [QuarterScore(home=int(home_q[i]), away=int(away_q[i])) for i in range(4)]
    game = BasketballGame(home_team=home_team, away_team=away_team, quarters=quarters, league=league)

    import asyncio, tempfile

    zip_buffer = io.BytesIO()
    labels = ["1C", "2C", "3C", "FINAL"]

    try:
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for q_count in range(1, 5):
                label = "FINAL" if q_count == 4 else f"{q_count}C"
                filename = f"{home_team} VS {away_team} {label} {league}.png"

                # Generar a archivo temporal
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                    tmp_path = tmp.name

                async def _gen(g, q, path):
                    # Patch output to temp file
                    gen.output_dir = Path(path).parent
                    orig_filename = f"{g.home_team.replace('/', '-')} VS {g.away_team.replace('/', '-')} {'FINAL' if q == 4 else str(q)+'C'} {g.league}.png"
                    await gen.generate_graphic(g, q)
                    return gen.output_dir / orig_filename

                out_file = asyncio.run(_gen(game, q_count, tmp_path))

                # Save to output folder too
                dest = gen.output_dir / filename
                if dest.exists():
                    zf.write(str(dest), filename)
                    # also use the real output path
                else:
                    # Try the actual generated file
                    actual = gen.output_dir / f"{home_team} VS {away_team} {label} {league}.png"
                    if actual.exists():
                        zf.write(str(actual), filename)

    except Exception as e:
        return jsonify({"error": f"Error generando gráficos: {e}"}), 500

    zip_buffer.seek(0)
    if zip_buffer.getbuffer().nbytes < 100:
        return jsonify({"error": "No se generaron gráficos"}), 500

    zip_name = f"{home_team} VS {away_team} {league}.zip"
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name=zip_name
    )

# ─────────────────────────────────────────────
# INICIO DEL SERVIDOR
# ─────────────────────────────────────────────
def print_banner():
    ip = get_local_ip()
    print("\n" + "="*60)
    print("  🦉  BUHO VISION - ECOSISTEMA INTEGRAL  🦉")
    print("="*60)
    print(f"  📍 Local:   http://localhost:5000")
    print(f"  📱 Red:     http://{ip}:5000")
    print(f"")
    print(f"  👉 Abre esa URL desde tu celular o compu")
    print(f"     (conectados a la misma red WiFi)")
    print(f"")
    print(f"  Ligas disponibles:")
    for name, info in LEAGUES_MAP.items():
        escudos = get_league_escudos_path(name)
        if escudos and escudos.exists():
            try:
                count = len([f for f in escudos.iterdir() if f.suffix.lower() in ['.png','.jpg','.jpeg']])
            except Exception:
                count = 0
            print(f"    {info['emoji']}  {name}: {count} escudos")
    print("="*60 + "\n")

if __name__ == '__main__':
    print_banner()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
