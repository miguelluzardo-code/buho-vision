"""
Simple Basketball Scoreboard Generator - Final Score Only
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

class SimpleBasketballGenerator:
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

    def parse_game_line(self, line):
        """Parse: Team1 vs Team2 Q1-Q1 Q2-Q2 Q3-Q3 Q4-Q4 LeagueName"""
        line = line.strip()
        if not line or line.startswith('#'):
            return None

        if ' vs ' not in line.lower():
            return None

        parts = line.split(' vs ', 1)
        home_team = parts[0].strip()

        rest = parts[1].strip().split()

        # Find all quarters (format: XX-YY)
        quarters = []
        league_start = -1
        for i, part in enumerate(rest):
            if '-' in part and all(x.isdigit() or x == '-' for x in part):
                try:
                    h, a = part.split('-')
                    quarters.append((int(h), int(a)))
                except:
                    pass
            elif quarters and part not in ['vs', 'VS']:
                league_start = i
                break

        if len(quarters) == 4:
            # Calculate total scores
            home_score = sum(q[0] for q in quarters)
            away_score = sum(q[1] for q in quarters)
            away_team = ' '.join(rest[:rest.index(f"{quarters[0][0]}-{quarters[0][1]}")]).strip()
            league = ' '.join(rest[league_start:]).strip() if league_start > 0 else "Liga Femenina Basketball"
        else:
            return None

        return {
            'home_team': home_team,
            'away_team': away_team,
            'home_score': home_score,
            'away_score': away_score,
            'league': league
        }

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
            'LAGOMAR': 'Lagomar',
            'DEFENSOR SPORTING CLUB': 'Defensor_Sporting',
            'URUNDAY UNIVERSITARIO': 'URUNDAY UNIV'
        }

        # Check if we have a direct mapping
        team_upper = team_name.upper()
        if team_upper in mappings:
            mapped_name = mappings[team_upper]
            logo_path = self.logos_base / f"{mapped_name}.png"
            if logo_path.exists():
                return logo_path

        # Try exact match variations
        variations = [
            team_name,
            team_name.upper(),
            team_name.lower(),
            team_name.replace(' ', '_'),
            team_name.replace(' ', '_').upper(),
        ]

        for variation in variations:
            for ext in ['.png', '.PNG', '.jpg', '.JPG']:
                logo_path = self.logos_base / f"{variation}{ext}"
                if logo_path.exists():
                    return logo_path

        print(f"WARNING: Logo not found for: {team_name}")
        return None

    async def generate_graphic(self, game):
        """Generate a single scoreboard graphic"""
        home_logo = self.find_logo(game['home_team'])
        away_logo = self.find_logo(game['away_team'])

        # Read template
        with open(self.template_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # Replace placeholders
        html_content = html_content.replace('{{HOME_TEAM}}', game['home_team'])
        html_content = html_content.replace('{{AWAY_TEAM}}', game['away_team'])
        html_content = html_content.replace('{{HOME_SCORE}}', str(game['home_score']))
        html_content = html_content.replace('{{AWAY_SCORE}}', str(game['away_score']))

        # Handle logos
        if home_logo:
            html_content = html_content.replace('{{HOME_LOGO}}', f'file:///{home_logo.as_posix()}')
        else:
            html_content = html_content.replace('<img src="{{HOME_LOGO}}"', '<div style="width:140px;height:140px;background:#333;border-radius:50%"')
            html_content = html_content.replace('alt="Home Team Logo">', '</div>')

        if away_logo:
            html_content = html_content.replace('{{AWAY_LOGO}}', f'file:///{away_logo.as_posix()}')
        else:
            html_content = html_content.replace('<img src="{{AWAY_LOGO}}"', '<div style="width:140px;height:140px;background:#333;border-radius:50%"')
            html_content = html_content.replace('alt="Away Team Logo">', '</div>')

        # Generate filename
        filename = f"{game['home_team']} VS {game['away_team']} {game['league']}.png"
        filename = filename.replace('/', '-').replace('\\', '-')
        output_path = self.output_dir / filename

        # Render with Playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(viewport={'width': 2000, 'height': 400})
            await page.set_content(html_content)

            # Wait for images to load
            await page.wait_for_timeout(800)

            # Take screenshot of just the scoreboard wrapper
            scoreboard = await page.query_selector('.scoreboard-wrapper')
            if scoreboard:
                await scoreboard.screenshot(
                    path=str(output_path),
                    omit_background=True
                )
            else:
                await page.screenshot(path=str(output_path), full_page=False)

            await browser.close()

        print(f"Generated: {filename}")
        return output_path

    async def process_all_games(self, data_file):
        """Process all games from data file"""
        games = []

        with open(data_file, 'r', encoding='utf-8') as f:
            for line in f:
                game = self.parse_game_line(line)
                if game:
                    games.append(game)

        print(f"\nFound {len(games)} games to process")

        for i, game in enumerate(games, 1):
            print(f"\n[{i}/{len(games)}] Processing: {game['home_team']} vs {game['away_team']}")
            await self.generate_graphic(game)

        print(f"\nAll graphics saved to: {self.output_dir}")


async def main():
    print("""
    ============================================
       BUHO VISION - BASKETBALL GENERATOR
        Simple Final Score Version
    ============================================
    """)

    data_file = Path(__file__).parent.parent / "1_Data_Input" / "basketball_game_data.txt"
    generator = SimpleBasketballGenerator("Liga Femenina Basketball")
    await generator.process_all_games(data_file)


if __name__ == "__main__":
    asyncio.run(main())
