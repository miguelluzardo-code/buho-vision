"""
BUHO VISION - Volleyball Graphics Generator
Genera gráficos de resultados de voley con sets parciales
Formato game_data: Team1 vs Team2 2-3 25/21,25/23,23/25,21/25,6/15 Liga
"""

import os
import sys
import asyncio
import json
import unicodedata
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).parent.parent / "1_Data_Input"))

try:
    from playwright.async_api import async_playwright
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
    subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
    from playwright.async_api import async_playwright


def normalize_text(text: str) -> str:
    nfd = unicodedata.normalize('NFD', text)
    return ''.join(c for c in nfd if unicodedata.category(c) != 'Mn')


def parse_volleyball_file(filepath: str) -> list:
    """
    Parse volleyball game data file.
    Format: Team1 vs Team2 HomeSets-AwaySets set1/set1,set2/set2,... League
    Example: Aires Puros B vs Bohemios J 2-3 25/21,25/23,23/25,21/25,6/15 Livosur
    """
    games = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            try:
                # Split from right to get league name (last word/phrase)
                # Format: "Team1 vs Team2 H-A sets League"
                # Find "vs" to split teams
                parts = line.split(' vs ', 1)
                if len(parts) != 2:
                    print(f"[SKIP] Invalid format: {line}")
                    continue

                home_team = parts[0].strip()
                rest = parts[1].strip()

                # rest = "Bohemios J 2-3 25/21,25/23,23/25,21/25,6/15 Livosur"
                # Split by spaces, find the score pattern (X-X), sets pattern (contains /,)
                tokens = rest.split()

                # Find score index (pattern: digit-digit)
                score_idx = None
                for i, t in enumerate(tokens):
                    if '-' in t and t.replace('-', '').replace('(', '').replace(')', '').isdigit():
                        score_idx = i
                        break

                if score_idx is None:
                    print(f"[SKIP] No score found: {line}")
                    continue

                away_team = ' '.join(tokens[:score_idx])
                score = tokens[score_idx]
                home_sets, away_sets = score.split('-')

                # Next token should be the set scores (comma-separated)
                sets_token = tokens[score_idx + 1]
                sets = sets_token.split(',')

                # Remaining tokens = league name
                league = ' '.join(tokens[score_idx + 2:])

                games.append({
                    'home_team': home_team,
                    'away_team': away_team,
                    'home_sets': int(home_sets),
                    'away_sets': int(away_sets),
                    'sets': sets,
                    'league': league
                })
                print(f"Loaded: {home_team} {home_sets}-{away_sets} {away_team} | {sets} ({league})")

            except Exception as e:
                print(f"[SKIP] Error parsing '{line}': {e}")

    return games


class VolleyballGenerator:
    def __init__(self, league_name: str):
        self.league_name = league_name
        self.template_path = Path(__file__).parent / "scoreboard_volleyball_template.html"
        self.config_path = Path(__file__).parent / "config.json"
        self.missing_logos = []
        self.load_config()

        league_cfg = self.config.get("leagues", {}).get(league_name, {})
        self.logos_base = Path(league_cfg.get("logo_folder", ""))
        self.league_logo_path = Path(league_cfg.get("league_logo", ""))

        output_folder = league_cfg.get("output_folder", league_name)
        if os.path.isabs(output_folder):
            self.output_dir = Path(output_folder)
        else:
            self.output_dir = Path(__file__).parent.parent.parent / "Output" / output_folder
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_config(self):
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

    def find_logo(self, team_name: str) -> str:
        """Returns file URL or empty string if not found."""
        league_cfg = self.config.get("leagues", {}).get(self.league_name, {})
        aliases = league_cfg.get("team_aliases", {})
        resolved = aliases.get(team_name, team_name)

        for name in [resolved, resolved.replace(" ", "_")]:
            for ext in ['.png', '.jpg', '.jpeg']:
                p = self.logos_base / f"{name}{ext}"
                if p.exists():
                    return str(p).replace("\\", "/")

        # Case-insensitive + accent-insensitive fallback
        norm = normalize_text(resolved.upper())
        for ext in ['*.png', '*.jpg', '*.jpeg']:
            for f in self.logos_base.glob(ext):
                if normalize_text(f.stem.upper()) == norm:
                    return str(f).replace("\\", "/")

        if team_name not in self.missing_logos:
            self.missing_logos.append(team_name)
            print(f"  [!] Logo no encontrado: {team_name} - usando placeholder")
        return ""

    async def generate(self, game: dict):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.set_viewport_size({"width": 1600, "height": 400})

            template_url = "file:///" + str(self.template_path).replace("\\", "/")
            await page.goto(template_url)

            def url(path):
                return ("file:///" + quote(path, safe='/: ')) if path else ""

            home_logo_url = url(self.find_logo(game['home_team']))
            away_logo_url = url(self.find_logo(game['away_team']))
            league_logo_url = url(str(self.league_logo_path).replace("\\", "/")) if self.league_logo_path.exists() else ""

            sets_js = "[" + ",".join(f"'{s}'" for s in game['sets']) + "]"

            js = f"""
                updateVolleyboard({{
                    homeTeam: '{game['home_team'].upper()}',
                    awayTeam: '{game['away_team'].upper()}',
                    homeSets: {game['home_sets']},
                    awaySets: {game['away_sets']},
                    homeLogo: '{home_logo_url}',
                    awayLogo: '{away_logo_url}',
                    leagueLogo: '{league_logo_url}',
                    leagueName: '{self.league_name.upper()}',
                    sets: {sets_js}
                }});
            """
            await page.evaluate(js)
            await page.wait_for_timeout(2000)

            safe_home = game['home_team'].replace("/", "-")
            safe_away = game['away_team'].replace("/", "-")
            filename = f"{safe_home.upper()} VS {safe_away.upper()} {self.league_name}.png"
            output_file = self.output_dir / filename

            scoreboard = await page.query_selector('.scoreboard-wrapper')
            if scoreboard:
                await scoreboard.screenshot(path=str(output_file), omit_background=True)
                print(f"[OK] Generado: {output_file.name}")
            else:
                print("[ERROR] No se encontró el elemento scoreboard")

            await browser.close()


async def main():
    print("""
    ============================================
       BUHO VISION - VOLLEYBALL GENERATOR
    ============================================
    """)

    data_file = Path(__file__).parent.parent / "1_Data_Input" / "volleyball_game_data.txt"
    if not data_file.exists():
        print(f"[ERROR] No se encontró: {data_file}")
        print("Crea el archivo con el formato:")
        print("  Team1 vs Team2 2-3 25/21,25/23,23/25,21/25,6/15 NombreLiga")
        return

    games = parse_volleyball_file(str(data_file))
    if not games:
        print("[ERROR] No se encontraron partidos")
        return

    # Group by league
    by_league = {}
    for g in games:
        by_league.setdefault(g['league'], []).append(g)

    for league, league_games in by_league.items():
        print(f"\n[INFO] Procesando {len(league_games)} partido(s) de {league}")
        gen = VolleyballGenerator(league_name=league)
        for game in league_games:
            await gen.generate(game)

    print("\n[COMPLETO]")


if __name__ == "__main__":
    asyncio.run(main())
