"""
Basketball Scoreboard Graphics Generator
Generates 4 graphics per game (one for each quarter) using HTML/CSS template
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright
import sys

# Add parent directory to path to import basketball_parser
sys.path.append(str(Path(__file__).parent.parent / "1_Data_Input"))
from basketball_parser import BasketballDataParser


class BasketballScoreboardGenerator:
    def __init__(self, league_name="Liga Femenina Basketball"):
        self.project_root = Path(__file__).parent.parent.parent
        self.template_path = Path(__file__).parent / "scoreboard_basketball_template.html"
        self.config_path = Path(__file__).parent / "config.json"
        self.league_name = league_name

        # Load configuration
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        if league_name not in config['leagues']:
            raise ValueError(f"League '{league_name}' not found in config.json")

        league_config = config['leagues'][league_name]
        self.logos_base = Path(league_config['logo_folder'])
        self.output_dir = self.project_root / "Output" / league_config['output_folder']
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.missing_logos = []

    def find_logo(self, team_name):
        """Find team logo file (case-insensitive with multiple variations)"""
        # Special mappings for known teams
        mappings = {
            'CLUB ATLETICO JUVENTUD': 'Juventud',
            'AGUADA': 'AGUADA',
            '25 DE AGOSTO': '25_de_Agosto',
            'YALE': 'YALE',
            'MALVIN': 'Malvin',
            'LAGOMAR COUNTRY CLUB': 'Lagomar',
            'DEFENSOR SPORTING CLUB': 'Defensor_Sporting',
            'URUNDAY UNIVERSITARIO': 'URUNDAY UNIV'
        }

        # Check if we have a direct mapping
        team_upper = team_name.upper()
        if team_upper in mappings:
            mapped_name = mappings[team_upper]
            logo_path = self.logos_base / f"{mapped_name}.png"
            if logo_path.exists():
                return f"file:///{logo_path.as_posix()}"

        # Try exact match variations
        variations = [
            team_name,
            team_name.upper(),
            team_name.lower(),
            team_name.replace(' ', '_'),
            team_name.replace(' ', '_').upper(),
            team_name.replace(' ', '_').lower(),
            team_name.title(),
        ]

        for variation in variations:
            logo_path = self.logos_base / f"{variation}.png"
            if logo_path.exists():
                return f"file:///{logo_path.as_posix()}"

        # Try searching for partial matches (last word usually is the key)
        team_parts = team_name.split()
        for file in self.logos_base.glob("*.png"):
            file_name = file.stem.upper()
            # Check if last significant word matches
            if team_parts and team_parts[-1].upper() in file_name:
                return f"file:///{file.as_posix()}"

        print(f"WARNING: Logo not found for {team_name} - will use placeholder")
        self.missing_logos.append(team_name)
        return "PLACEHOLDER"

    async def generate_final_graphic(self, game):
        """Generate final score graphic"""
        # Calculate total scores
        home_score = sum(game.quarters[i][0] for i in range(4))
        away_score = sum(game.quarters[i][1] for i in range(4))
        quarter_name = "FINAL"

        # Find team logos
        home_logo = self.find_logo(game.home_team)
        away_logo = self.find_logo(game.away_team)

        # Check if logos exist
        if home_logo == "PLACEHOLDER" or away_logo == "PLACEHOLDER":
            return None

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(viewport={'width': 2000, 'height': 400})

            # Load template
            await page.goto(f"file:///{self.template_path.absolute().as_posix()}")

            # Smart line breaking
            def format_team_name(name):
                if 'URUNDAY UNIVERSITARIO' in name.upper():
                    return name
                elif 'DEFENSOR SPORTING CLUB' in name.upper():
                    return name.replace('DEFENSOR ', 'DEFENSOR<br>')
                elif 'CLUB ATLETICO' in name.upper():
                    return name.replace('CLUB ', 'CLUB<br>')
                elif 'LAGOMAR COUNTRY CLUB' in name.upper():
                    return name.replace('LAGOMAR ', 'LAGOMAR<br>')
                elif len(name) > 12 and ' ' in name:
                    parts = name.split(' ', 1)
                    return f"{parts[0]}<br>{parts[1]}"
                return name

            home_display = format_team_name(game.home_team)
            away_display = format_team_name(game.away_team)

            # Update scoreboard data
            await page.evaluate(f"""
                const homeNameEl = document.getElementById('home-name');
                const awayNameEl = document.getElementById('away-name');
                homeNameEl.innerHTML = '{home_display}';
                awayNameEl.innerHTML = '{away_display}';
                document.getElementById('home-score').textContent = '{home_score}';
                document.getElementById('away-score').textContent = '{away_score}';
                document.getElementById('quarter').textContent = '{quarter_name}';
                document.getElementById('quarter').style.fontSize = '38px';

                const homeLogo = document.getElementById('home-logo');
                const awayLogo = document.getElementById('away-logo');
                if ('{home_logo}') {{
                    homeLogo.src = '{home_logo}';
                    homeLogo.style.display = 'block';
                }}
                if ('{away_logo}') {{
                    awayLogo.src = '{away_logo}';
                    awayLogo.style.display = 'block';
                }}
            """)

            # Wait for content to load
            await page.wait_for_timeout(500)

            # Generate output filename
            output_file = self.output_dir / f"{game.home_team} VS {game.away_team} {game.league}.png"

            # Take screenshot
            scoreboard = await page.query_selector('.scoreboard-wrapper')
            if scoreboard:
                await scoreboard.screenshot(
                    path=str(output_file),
                    omit_background=True
                )
                print(f"[OK] Generated FINAL: {output_file.name}")
            else:
                print(f"[ERROR] Could not find scoreboard element")

            await browser.close()
            return output_file

    async def generate_quarter_graphic(self, game, quarter_index):
        """Generate a single quarter graphic"""
        # Get cumulative scores for this quarter
        home_score, away_score = game.get_cumulative_score(quarter_index)
        quarter_name = f"{quarter_index + 1}Q"

        # Find team logos
        home_logo = self.find_logo(game.home_team)
        away_logo = self.find_logo(game.away_team)

        # Check if logos exist
        if home_logo == "PLACEHOLDER" or away_logo == "PLACEHOLDER":
            return None

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(viewport={'width': 2000, 'height': 400})

            # Load template
            await page.goto(f"file:///{self.template_path.absolute().as_posix()}")

            # Smart line breaking: split only at specific points, never break UNIVERSITARIO
            def format_team_name(name):
                # Special handling for specific teams
                if 'URUNDAY UNIVERSITARIO' in name.upper():
                    # Keep URUNDAY UNIVERSITARIO on one line
                    return name
                elif 'DEFENSOR SPORTING CLUB' in name.upper():
                    return name.replace('DEFENSOR ', 'DEFENSOR<br>')
                elif 'CLUB ATLETICO' in name.upper():
                    return name.replace('CLUB ', 'CLUB<br>')
                elif 'LAGOMAR COUNTRY CLUB' in name.upper():
                    return name.replace('LAGOMAR ', 'LAGOMAR<br>')
                elif len(name) > 12 and ' ' in name:
                    # Generic fallback: break at first space
                    parts = name.split(' ', 1)
                    return f"{parts[0]}<br>{parts[1]}"
                return name

            home_display = format_team_name(game.home_team)
            away_display = format_team_name(game.away_team)

            # Update scoreboard data
            await page.evaluate(f"""
                const homeNameEl = document.getElementById('home-name');
                const awayNameEl = document.getElementById('away-name');
                homeNameEl.innerHTML = '{home_display}';
                awayNameEl.innerHTML = '{away_display}';
                document.getElementById('home-score').textContent = '{home_score}';
                document.getElementById('away-score').textContent = '{away_score}';
                document.getElementById('quarter').textContent = '{quarter_name}';

                const homeLogo = document.getElementById('home-logo');
                const awayLogo = document.getElementById('away-logo');
                if ('{home_logo}') {{
                    homeLogo.src = '{home_logo}';
                    homeLogo.style.display = 'block';
                }}
                if ('{away_logo}') {{
                    awayLogo.src = '{away_logo}';
                    awayLogo.style.display = 'block';
                }}
            """)

            # Wait for content to load
            await page.wait_for_timeout(500)

            # Generate output filename
            output_file = self.output_dir / game.get_filename(quarter_index)

            # Take screenshot
            scoreboard = await page.query_selector('.scoreboard-wrapper')
            if scoreboard:
                await scoreboard.screenshot(
                    path=str(output_file),
                    omit_background=True
                )
                print(f"[OK] Generated: {output_file.name}")
            else:
                print(f"[ERROR] Could not find scoreboard element")

            await browser.close()
            return output_file

    async def process_all_games(self, data_file="basketball_game_data.txt"):
        """Process all games and generate 4 graphics per game"""
        parser = BasketballDataParser(str(Path(__file__).parent.parent / "1_Data_Input" / data_file))
        games = parser.load_games()

        if not games:
            print("No games found to process!")
            return

        print(f"\n{'='*50}")
        print(f"Processing {len(games)} basketball games...")
        print(f"Generating 4 graphics per game (one per quarter)")
        print(f"{'='*50}\n")

        skipped_games = []
        generated_count = 0

        for game in games:
            print(f"\nProcessing: {game.home_team} vs {game.away_team}")

            # Check if logos exist
            home_logo = self.find_logo(game.home_team)
            away_logo = self.find_logo(game.away_team)

            if home_logo == "PLACEHOLDER" or away_logo == "PLACEHOLDER":
                missing_teams = []
                if home_logo == "PLACEHOLDER":
                    missing_teams.append(game.home_team)
                if away_logo == "PLACEHOLDER":
                    missing_teams.append(game.away_team)

                print(f"[SKIPPED] Missing logos: {', '.join(missing_teams)}")
                skipped_games.append({
                    'home': game.home_team,
                    'away': game.away_team,
                    'missing': missing_teams
                })
                continue

            # Generate graphics for all 4 quarters
            for quarter_idx in range(4):
                try:
                    await self.generate_quarter_graphic(game, quarter_idx)
                    generated_count += 1
                except Exception as e:
                    print(f"[ERROR] Q{quarter_idx+1}: {e}")

        print(f"\n{'='*50}")
        print(f"[COMPLETE] Generated {generated_count} graphics")
        print(f"Skipped {len(skipped_games)} games")
        print(f"Graphics saved to: {self.output_dir}")
        print(f"{'='*50}")

        # Save skipped games report
        if skipped_games:
            report_file = self.output_dir / "skipped_games.txt"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("SKIPPED BASKETBALL GAMES - Missing Team Logos\n")
                f.write("=" * 50 + "\n\n")
                for game in skipped_games:
                    f.write(f"{game['home']} vs {game['away']}\n")
                    f.write(f"  Missing logos: {', '.join(game['missing'])}\n\n")
            print(f"\n[INFO] Skipped games report saved to: {report_file}")


async def main():
    """Main function"""
    print("""
    ============================================
       BUHO VISION - BASKETBALL GENERATOR
        HTML/CSS Solution (No Photoshop!)
    ============================================
    """)

    generator = BasketballScoreboardGenerator()

    # Check if logos directory exists
    if not generator.logos_base.exists():
        print(f"[ERROR] Logos directory not found at {generator.logos_base}")
        print("Please make sure the basketball logos folder is available.")
        return

    # Process all games
    await generator.process_all_games()


if __name__ == "__main__":
    asyncio.run(main())