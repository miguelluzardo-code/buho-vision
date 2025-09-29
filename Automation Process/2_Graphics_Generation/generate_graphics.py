"""
BUHO VISION - Graphics Generator using HTML/CSS + Playwright
Generates scoreboard graphics without Photoshop!
"""

import os
import sys
import asyncio
import json
from pathlib import Path

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
        self.template_path = Path(__file__).parent / "scoreboard_template.html"
        self.config_path = Path(__file__).parent / "config.json"
        self.league_name = league_name
        self.missing_logos = []

        # Load configuration
        self.load_config()

        # Set up paths from config
        league_config = self.config.get("leagues", {}).get(league_name, {})
        self.logos_base = Path(league_config.get("logo_folder", r"C:\Users\mgarr\Desktop\buho\1- Liga Kings-20250925T142355Z-1-001\1- Liga Kings\1 - Escudos"))
        self.league_logo_path = Path(league_config.get("league_logo", r"C:\Users\mgarr\Desktop\buho\1- Liga Kings-20250925T142355Z-1-001\1- Liga Kings\5 - Miscelaneos\LIGA_KINGS.png"))
        self.output_dir = Path(__file__).parent.parent.parent / "Output" / league_config.get("output_folder", "Liga Kings")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_config(self):
        """Load configuration from JSON file"""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            # Default config if file doesn't exist
            self.config = {
                "scoreboard": {"dimensions": {"viewport_width": 1280, "viewport_height": 200}},
                "processing": {"wait_for_images_ms": 1000, "headless_mode": True},
                "leagues": {}
            }

    def find_logo(self, team_name: str) -> str:
        """Find the logo file for a team"""
        # Try exact match first
        logo_file = self.logos_base / f"{team_name}.png"
        if logo_file.exists():
            return str(logo_file).replace("\\", "/")

        # Try with underscores instead of spaces
        team_name_underscore = team_name.replace(" ", "_")
        logo_file = self.logos_base / f"{team_name_underscore}.png"
        if logo_file.exists():
            return str(logo_file).replace("\\", "/")

        # Try case-insensitive search
        for file in self.logos_base.glob("*.png"):
            if file.stem.upper() == team_name.upper():
                return str(file).replace("\\", "/")

        # Track missing logo
        if team_name not in self.missing_logos:
            self.missing_logos.append(team_name)
            print(f"Warning: Logo not found for {team_name} - will use placeholder")

        # Return placeholder indicator
        return "PLACEHOLDER"

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

            # Prepare logo paths
            home_logo = self.find_logo(game.home_team)
            away_logo = self.find_logo(game.away_team)

            # Use the Liga Kings logo from Miscelaneos folder
            league_logo = str(self.league_logo_path).replace("\\", "/") if self.league_logo_path.exists() else ""

            # Create JavaScript object with proper handling for placeholders
            js_code = f"""
                updateScoreboard({{
                    homeTeam: '{game.home_team}',
                    awayTeam: '{game.away_team}',
                    homeScore: '{game.home_score}',
                    awayScore: '{game.away_score}',
                    homeLogo: '{("file:///" + home_logo) if home_logo != "PLACEHOLDER" else ""}',
                    awayLogo: '{("file:///" + away_logo) if away_logo != "PLACEHOLDER" else ""}',
                    leagueLogo: 'file:///{league_logo}',
                    homePlaceholder: {str(home_logo == "PLACEHOLDER").lower()},
                    awayPlaceholder: {str(away_logo == "PLACEHOLDER").lower()}
                }});
            """

            # Update the scoreboard with game data
            await page.evaluate(js_code)

            # Wait for images to load (time from config)
            wait_time = self.config.get("processing", {}).get("wait_for_images_ms", 1000)
            await page.wait_for_timeout(wait_time)

            # Generate output filename
            output_file = self.output_dir / game.get_filename()

            # Take screenshot of just the scoreboard element
            scoreboard = await page.query_selector('.scoreboard')
            if scoreboard:
                await scoreboard.screenshot(
                    path=str(output_file),
                    omit_background=True  # This enables transparency!
                )
                print(f"[OK] Generated: {output_file.name}")
            else:
                print(f"[ERROR] Could not find scoreboard element")

            await browser.close()

    async def process_all_games(self, data_file="game_data.txt"):
        """Process all games from specified data file"""
        parser = DataParser(str(Path(__file__).parent.parent / "1_Data_Input" / data_file))
        games = parser.load_games()

        if not games:
            print("No games found to process!")
            return

        print(f"\nProcessing {len(games)} games...\n")

        for game in games:
            try:
                await self.generate_scoreboard(game)
            except Exception as e:
                print(f"[ERROR] Processing {game}: {e}")

        print(f"\n[COMPLETE] Graphics saved to: {self.output_dir}")

        # Save missing logos report if any
        if self.missing_logos:
            report_file = self.output_dir / "missing_logos.txt"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("Missing Team Logos Report\n")
                f.write("=" * 40 + "\n")
                f.write(f"Date: {Path(__file__).parent}\n\n")
                for team in sorted(set(self.missing_logos)):
                    f.write(f"- {team}\n")
            print(f"\n[INFO] Missing logos report saved to: {report_file}")


async def main():
    """Main function to run the generator"""
    print("""
    ============================================
       BUHO VISION - SCOREBOARD GENERATOR
        HTML/CSS Solution (No Photoshop!)
    ============================================
    """)

    generator = ScoreboardGenerator()

    # Check if logos directory exists
    if not generator.logos_base.exists():
        print(f"[ERROR] Logos directory not found at {generator.logos_base}")
        print("Please make sure the Liga Kings logos folder is available.")
        return

    # Process all games
    await generator.process_all_games()


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())