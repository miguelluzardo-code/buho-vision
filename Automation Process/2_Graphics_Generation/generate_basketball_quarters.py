"""
BUHO VISION - Basketball Quarters Graphics Generator
Generates 4 progressive scoreboard graphics per game:
  1C  -> shows only Q1 scores
  2C  -> shows Q1 + Q2
  3C  -> shows Q1 + Q2 + Q3
  FINAL -> shows all 4 quarters + highlighted total

Input format (basketball_game_data.txt):
  Lagomar Country Club vs Cordon 35-12 16-7 20-11 22-26 Liga Femenina Basketball
"""

import os
import sys
import asyncio
import json
import base64
import unicodedata
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "1_Data_Input"))
from basketball_parser import BasketballDataParser, BasketballGame

try:
    from playwright.async_api import async_playwright
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
    subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
    from playwright.async_api import async_playwright


class BasketballQuartersGenerator:
    def __init__(self, league_name="Liga Femenina Basketball"):
        self.league_name = league_name
        self.config_path = Path(__file__).parent / "config.json"
        self.template_path = Path(__file__).parent / "scoreboard_basketball_quarters_template.html"
        self.missing_logos = []

        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        # Resolve platform-specific paths
        platform_key = "mac" if sys.platform == "darwin" else "windows"
        for league in self.config.get("leagues", {}).values():
            for field in ("logo_folder", "league_logo", "output_folder"):
                platform_field = f"{field}_{platform_key}"
                if platform_field in league:
                    league[field] = league[platform_field]

        league_config = self.config["leagues"].get(league_name, {})
        self.logos_base = Path(league_config.get("logo_folder", ""))
        self.league_logo_path = Path(league_config.get("league_logo", ""))
        self.team_aliases = league_config.get("team_aliases", {})

        output_folder = league_config.get("output_folder", "")
        if os.path.isabs(output_folder):
            self.output_dir = Path(output_folder)
        else:
            self.output_dir = Path(__file__).parent.parent.parent / "Output" / output_folder
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def normalize_text(self, text: str) -> str:
        nfd = unicodedata.normalize('NFD', text)
        return ''.join(c for c in nfd if unicodedata.category(c) != 'Mn')

    def find_logo(self, team_name: str) -> str:
        """Find logo file. Returns path string or 'PLACEHOLDER'."""
        original = team_name
        if team_name in self.team_aliases:
            team_name = self.team_aliases[team_name]

        for ext in ['.png', '.jpg', '.jpeg', '.svg']:
            f = self.logos_base / f"{team_name}{ext}"
            if f.exists():
                return str(f).replace("\\", "/")

        team_us = team_name.replace(" ", "_")
        for ext in ['.png', '.jpg', '.jpeg', '.svg']:
            f = self.logos_base / f"{team_us}{ext}"
            if f.exists():
                return str(f).replace("\\", "/")

        for ext in ['*.png', '*.jpg', '*.jpeg', '*.svg']:
            for f in self.logos_base.glob(ext):
                if f.stem.upper() == team_name.upper():
                    return str(f).replace("\\", "/")

        team_norm = self.normalize_text(team_name.upper())
        for ext in ['*.png', '*.jpg', '*.jpeg', '*.svg']:
            for f in self.logos_base.glob(ext):
                if self.normalize_text(f.stem.upper()) == team_norm:
                    return str(f).replace("\\", "/")

        def simplify(s):
            return self.normalize_text(s.upper().replace(".", "").replace("_", " ").strip())
        for ext in ['*.png', '*.jpg', '*.jpeg', '*.svg']:
            for f in self.logos_base.glob(ext):
                if simplify(f.stem) == simplify(team_name):
                    return str(f).replace("\\", "/")

        if original not in self.missing_logos:
            self.missing_logos.append(original)
            print(f"  Warning: Logo not found for {original} - using placeholder")
        return "PLACEHOLDER"

    def to_data_url(self, path: str) -> str:
        """Encode image file as base64 data URL."""
        if not path or path == "PLACEHOLDER":
            return ""
        try:
            p = Path(path)
            ext = p.suffix.lower().lstrip('.')
            mime = "image/svg+xml" if ext == "svg" else ("image/png" if ext == "png" else f"image/{ext}")
            with open(p, "rb") as f:
                data = base64.b64encode(f.read()).decode("utf-8")
            return f"data:{mime};base64,{data}"
        except Exception:
            return ""

    async def generate_graphic(self, game: BasketballGame, quarters_to_show: int):
        """
        Generate one graphic showing quarters 1..quarters_to_show.
        quarters_to_show: 1, 2, 3, or 4
        """
        home_logo_path = self.find_logo(game.home_team)
        away_logo_path = self.find_logo(game.away_team)

        home_logo_url = self.to_data_url(home_logo_path)
        away_logo_url = self.to_data_url(away_logo_path)

        league_logo_url = ""
        if self.league_logo_path.exists():
            league_logo_url = self.to_data_url(str(self.league_logo_path))

        # Build cumulative quarter arrays: each cell = running total up to that quarter
        home_quarters = []
        away_quarters = []
        h_running = 0
        a_running = 0
        for i in range(quarters_to_show):
            h_running += game.quarters[i].home
            a_running += game.quarters[i].away
            home_quarters.append(h_running)
            away_quarters.append(a_running)

        # Total column = same as last quarter value (they're already cumulative)
        home_total = home_quarters[-1] if home_quarters else None
        away_total = away_quarters[-1] if away_quarters else None

        scoreboard_data = {
            "homeTeam": game.home_team,
            "awayTeam": game.away_team,
            "homeQuarters": home_quarters,
            "awayQuarters": away_quarters,
            "homeTotal": home_total,
            "awayTotal": away_total,
            "homeLogo": home_logo_url,
            "awayLogo": away_logo_url,
            "leagueLogo": league_logo_url,
            "leagueName": game.league,
        }

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.set_viewport_size({"width": 1500, "height": 500})

            template_url = f"file:///{self.template_path}".replace("\\", "/")
            await page.goto(template_url)
            await page.evaluate("(data) => updateScoreboard(data)", scoreboard_data)
            await page.wait_for_timeout(500)

            # Filename: Q1 -> "1C", Q2 -> "2C", Q3 -> "3C", Q4 -> "FINAL"
            label = "FINAL" if quarters_to_show == 4 else f"{quarters_to_show}C"
            home_safe = game.home_team.replace("/", "-")
            away_safe = game.away_team.replace("/", "-")
            filename = f"{home_safe} VS {away_safe} {label} {game.league}.png"
            output_file = self.output_dir / filename

            scoreboard_el = await page.query_selector('.scoreboard-wrapper')
            if scoreboard_el:
                await scoreboard_el.screenshot(path=str(output_file), omit_background=True)
                print(f"  [OK] {filename}")
            else:
                print(f"  [ERROR] scoreboard element not found")

            await browser.close()

    async def process_games(self, data_file="basketball_game_data.txt"):
        """Process all games from the data file."""
        parser = BasketballDataParser(
            str(Path(__file__).parent.parent / "1_Data_Input" / data_file)
        )
        games = parser.load_games()

        if not games:
            print("No games found to process!")
            return

        print(f"\nProcessing {len(games)} basketball game(s)...")
        print(f"Generating 4 graphics per game (1C, 2C, 3C, FINAL)\n")

        generated = 0
        for game in games:
            print(f"\n{game.home_team} vs {game.away_team}")
            for q in range(1, 5):
                try:
                    await self.generate_graphic(game, q)
                    generated += 1
                except Exception as e:
                    print(f"  [ERROR] Q{q}: {e}")

        print(f"\n[COMPLETE] Generated {generated} graphics")
        print(f"Saved to: {self.output_dir}")


async def main():
    print("""
    ============================================
       BUHO VISION - BASKETBALL QUARTERS
    ============================================
    """)

    generator = BasketballQuartersGenerator()

    if not generator.logos_base.exists():
        print(f"[ERROR] Logos folder not found: {generator.logos_base}")
        return

    await generator.process_games()


if __name__ == "__main__":
    asyncio.run(main())
