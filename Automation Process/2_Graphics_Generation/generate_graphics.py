"""
BUHO VISION - Graphics Generator using HTML/CSS + Playwright
Generates scoreboard graphics without Photoshop!
"""

import os
import sys
import asyncio
import json
import unicodedata
import base64
from pathlib import Path
from urllib.parse import quote

# Add parent directory to path to import data_parser
sys.path.append(str(Path(__file__).parent.parent / "1_Data_Input"))
from data_parser import DataParser, GameData

# Try to import playwright
try:
    from playwright.async_api import async_playwright
except ImportError:
    print("Installing playwright... Please wait...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
    subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
    from playwright.async_api import async_playwright


class ScoreboardGenerator:
    def __init__(self, league_name="Liga Kings"):
        self.config_path = Path(__file__).parent / "config.json"
        self.league_name = league_name
        self.missing_logos = []

        # Load configuration
        self.load_config()

        # Set up paths from config
        league_config = self.config.get("leagues", {}).get(league_name, {})

        # Use league-specific template if defined, otherwise default
        template_name = league_config.get("template", "scoreboard_template.html")
        self.template_path = Path(__file__).parent / template_name
        self.logos_base = Path(league_config.get("logo_folder", ""))
        self.league_logo_path = Path(league_config.get("league_logo", ""))

        # Handle output folder - use absolute path if provided, otherwise relative
        output_folder = league_config.get("output_folder", "Liga Kings")
        if os.path.isabs(output_folder):
            self.output_dir = Path(output_folder)
        else:
            self.output_dir = Path(__file__).parent.parent.parent / "Output" / output_folder
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_config(self):
        """Load configuration from JSON file"""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            # Resolve platform-specific paths for each league
            platform_key = "mac" if sys.platform == "darwin" else "windows"
            for league in self.config.get("leagues", {}).values():
                for field in ("logo_folder", "league_logo", "output_folder"):
                    platform_field = f"{field}_{platform_key}"
                    if platform_field in league:
                        league[field] = league[platform_field]
        else:
            # Default config if file doesn't exist
            self.config = {
                "scoreboard": {"dimensions": {"viewport_width": 1280, "viewport_height": 200}},
                "processing": {"wait_for_images_ms": 1000, "headless_mode": True},
                "leagues": {}
            }

    def normalize_text(self, text: str) -> str:
        """Normalize text by removing accents for comparison"""
        # Normalize to NFD (decomposed form) then remove combining characters
        nfd = unicodedata.normalize('NFD', text)
        return ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')

    def find_logo(self, team_name: str) -> tuple:
        """Find the logo file for a team. Returns (logo_path, display_name)"""
        original_name = team_name

        # Check for team aliases first
        league_config = self.config.get("leagues", {}).get(self.league_name, {})
        team_aliases = league_config.get("team_aliases", {})
        if team_name in team_aliases:
            team_name = team_aliases[team_name]

        # Try exact match first (check multiple extensions)
        for ext in ['.png', '.jpg', '.jpeg']:
            logo_file = self.logos_base / f"{team_name}{ext}"
            if logo_file.exists():
                return str(logo_file).replace("\\", "/"), original_name

        # Try with underscores instead of spaces
        team_name_underscore = team_name.replace(" ", "_")
        for ext in ['.png', '.jpg', '.jpeg']:
            logo_file = self.logos_base / f"{team_name_underscore}{ext}"
            if logo_file.exists():
                return str(logo_file).replace("\\", "/"), original_name

        # Try case-insensitive search
        for ext in ['*.png', '*.jpg', '*.jpeg']:
            for file in self.logos_base.glob(ext):
                if file.stem.upper() == team_name.upper():
                    return str(file).replace("\\", "/"), original_name

        # Try normalized search (without accents) - handles RUSTICOS vs RÚSTICOS, COLON vs COLÓN
        team_normalized = self.normalize_text(team_name.upper())
        for ext in ['*.png', '*.jpg', '*.jpeg']:
            for file in self.logos_base.glob(ext):
                file_normalized = self.normalize_text(file.stem.upper())
                if file_normalized == team_normalized:
                    return str(file).replace("\\", "/"), original_name

        # Try ignoring dots and underscores - handles TATANKA F.C → TATANKA_FC
        def simplify(s):
            return self.normalize_text(s.upper().replace(".", "").replace("_", " ").replace("  ", " ").strip())
        team_simple = simplify(team_name)
        for ext in ['*.png', '*.jpg', '*.jpeg']:
            for file in self.logos_base.glob(ext):
                if simplify(file.stem) == team_simple:
                    return str(file).replace("\\", "/"), original_name

        # Track missing logo
        if team_name not in self.missing_logos:
            self.missing_logos.append(team_name)
            print(f"Warning: Logo not found for {team_name} - will use placeholder")

        # Return placeholder indicator with original name
        return "PLACEHOLDER", original_name

    async def generate_scoreboard(self, game: GameData):
        """Generate a single scoreboard graphic"""
        async with async_playwright() as p:
            # Launch browser using config settings
            headless = self.config.get("processing", {}).get("headless_mode", True)
            browser = await p.chromium.launch(headless=headless)
            page = await browser.new_page()

            # Set viewport from config
            dimensions = self.config.get("scoreboard", {}).get("dimensions", {})
            await page.set_viewport_size({
                "width": dimensions.get("viewport_width", 1280),
                "height": dimensions.get("viewport_height", 200)
            })

            # Load the template
            template_url = f"file:///{self.template_path}".replace("\\", "/")
            await page.goto(template_url)

            # Prepare logo paths and display names
            home_logo, display_home = self.find_logo(game.home_team)
            away_logo, display_away = self.find_logo(game.away_team)

            # Use the Liga Kings logo from Miscelaneos folder
            league_logo = str(self.league_logo_path).replace("\\", "/") if self.league_logo_path.exists() else ""

            def trim_and_encode(path):
                """Trim whitespace/transparent borders and encode as base64 data URL"""
                if not path or path == "PLACEHOLDER":
                    return ""
                try:
                    from PIL import Image
                    import io
                    img = Image.open(path)
                    # Convert to RGBA to handle both transparent and white backgrounds
                    img_rgba = img.convert("RGBA")
                    datas = img_rgba.getdata()
                    # Build mask: pixel is "content" if not nearly white+opaque or transparent
                    bbox = img_rgba.getbbox()
                    # Also check for white background trimming
                    bg = Image.new("RGBA", img_rgba.size, (255, 255, 255, 255))
                    diff = Image.new("RGBA", img_rgba.size)
                    for i, (r, g, b, a) in enumerate(datas):
                        x, y = i % img_rgba.width, i // img_rgba.width
                        # Pixel is background if transparent OR nearly white
                        if a < 20 or (r > 240 and g > 240 and b > 240 and a > 200):
                            diff.putpixel((x, y), (255, 255, 255, 0))
                        else:
                            diff.putpixel((x, y), (r, g, b, a))
                    content_bbox = diff.getbbox()
                    if content_bbox:
                        # Add small padding
                        pad = 10
                        w, h = img_rgba.size
                        x0 = max(0, content_bbox[0] - pad)
                        y0 = max(0, content_bbox[1] - pad)
                        x1 = min(w, content_bbox[2] + pad)
                        y1 = min(h, content_bbox[3] + pad)
                        img = img.crop((x0, y0, x1, y1))
                    buf = io.BytesIO()
                    img.save(buf, format="PNG")
                    data = base64.b64encode(buf.getvalue()).decode("utf-8")
                    return f"data:image/png;base64,{data}"
                except Exception:
                    # Fallback: encode as-is
                    try:
                        p = Path(path)
                        ext = p.suffix.lower().lstrip('.')
                        mime = "image/png" if ext == "png" else f"image/{ext}"
                        with open(p, "rb") as f:
                            data = base64.b64encode(f.read()).decode("utf-8")
                        return f"data:{mime};base64,{data}"
                    except Exception:
                        return ""

            def to_data_url(path):
                """Convert image file to base64 data URL for reliable browser loading"""
                if not path or path == "PLACEHOLDER":
                    return ""
                # Use trimming for Nexo template (logos need to fill large areas)
                league_config = self.config.get("leagues", {}).get(self.league_name, {})
                if league_config.get("trim_logos", False):
                    return trim_and_encode(path)
                try:
                    p = Path(path)
                    ext = p.suffix.lower().lstrip('.')
                    mime = "image/png" if ext == "png" else f"image/{ext}"
                    with open(p, "rb") as f:
                        data = base64.b64encode(f.read()).decode("utf-8")
                    return f"data:{mime};base64,{data}"
                except Exception:
                    return ""

            home_logo_url = to_data_url(home_logo) if home_logo != "PLACEHOLDER" else ""
            away_logo_url = to_data_url(away_logo) if away_logo != "PLACEHOLDER" else ""
            league_logo_url = to_data_url(league_logo) if league_logo else ""

            scoreboard_data = {
                "homeTeam": display_home,
                "awayTeam": display_away,
                "homeScore": str(game.home_score),
                "awayScore": str(game.away_score),
                "homeLogo": home_logo_url,
                "awayLogo": away_logo_url,
                "leagueLogo": league_logo_url,
                "homePlaceholder": home_logo == "PLACEHOLDER",
                "awayPlaceholder": away_logo == "PLACEHOLDER",
            }

            # Update the scoreboard with game data (pass as JSON arg to avoid injection)
            await page.evaluate("(data) => updateScoreboard(data)", scoreboard_data)

            # No need to wait for images since they're embedded as base64
            await page.wait_for_timeout(500)

            # Generate output filename using display names (with correct accents)
            home_safe = display_home.replace("/", "-")
            away_safe = display_away.replace("/", "-")
            if game.divisional:
                filename = f"{home_safe} VS {away_safe} {game.league} {game.divisional}.png"
            else:
                filename = f"{home_safe} VS {away_safe} {game.league}.png"
            output_file = self.output_dir / filename

            # Take screenshot of just the scoreboard element
            scoreboard = await page.query_selector('.scoreboard-wrapper')
            if scoreboard:
                await scoreboard.screenshot(
                    path=str(output_file),
                    omit_background=True  # This enables transparency!
                )
                print(f"[OK] Generated: {output_file.name}")
            else:
                print(f"[ERROR] Could not find scoreboard element")

            await browser.close()

    async def process_games(self, games):
        """Process a list of games"""
        if not games:
            print("No games found to process!")
            return

        print(f"\nProcessing {len(games)} games...\n")

        skipped_games = []
        generated_count = 0

        for game in games:
            try:
                # Check if both team logos exist BEFORE generating
                home_logo, home_display = self.find_logo(game.home_team)
                away_logo, away_display = self.find_logo(game.away_team)

                # Generate even with missing logos (using placeholders)
                if home_logo == "PLACEHOLDER" or away_logo == "PLACEHOLDER":
                    missing_teams = []
                    if home_logo == "PLACEHOLDER":
                        missing_teams.append(game.home_team)
                    if away_logo == "PLACEHOLDER":
                        missing_teams.append(game.away_team)
                    print(f"[WARNING] Generating with placeholder for: {', '.join(missing_teams)}")

                # Always generate the graphic
                await self.generate_scoreboard(game)
                generated_count += 1

            except Exception as e:
                print(f"[ERROR] Processing {game}: {e}")

        print(f"\n[COMPLETE] Generated {generated_count} graphics, skipped {len(skipped_games)}")
        print(f"Graphics saved to: {self.output_dir}")

    async def process_all_games(self, data_file="game_data.txt"):
        """Process all games from specified data file"""
        parser = DataParser(str(Path(__file__).parent.parent / "1_Data_Input" / data_file))
        games = parser.load_games()

        if not games:
            print("No games found to process!")
            return

        await self.process_games(games)


async def main():
    """Main function to run the generator"""
    print("""
    ============================================
       BUHO VISION - SCOREBOARD GENERATOR
        HTML/CSS Solution (No Photoshop!)
    ============================================
    """)

    # Parse data file first to detect league
    data_file_path = Path(__file__).parent.parent / "1_Data_Input" / "game_data.txt"
    parser = DataParser(str(data_file_path))
    games = parser.load_games()

    if not games:
        print("[ERROR] No games found in game_data.txt")
        return

    # Group games by league
    games_by_league = {}
    for game in games:
        if game.league not in games_by_league:
            games_by_league[game.league] = []
        games_by_league[game.league].append(game)

    # Process each league separately
    for league_name, league_games in games_by_league.items():
        print(f"\n[INFO] Processing {len(league_games)} games for {league_name}")

        generator = ScoreboardGenerator(league_name=league_name)

        # Check if logos directory exists
        if not generator.logos_base.exists():
            print(f"[ERROR] Logos directory not found at {generator.logos_base}")
            print(f"Please make sure the {league_name} logos folder is available.")
            continue

        # Process games for this league
        await generator.process_games(league_games)


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())