"""
BUHO VISION - Data Parser
Parses game data from text files for graphics generation
"""

import re
from dataclasses import dataclass
from typing import List, Optional
import os

@dataclass
class GameData:
    """Represents a single game's data"""
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    league: str

    def __str__(self):
        return f"{self.home_team} {self.home_score}-{self.away_score} {self.away_team} ({self.league})"

    def get_filename(self) -> str:
        """Generate output filename for this game"""
        return f"{self.home_team} VS {self.away_team} {self.league}.png"


class DataParser:
    """Parses game data from various formats"""

    def __init__(self, data_file: str = "game_data.txt"):
        self.data_file = data_file
        self.games: List[GameData] = []

    def parse_line(self, line: str) -> Optional[GameData]:
        """
        Parse a single line of game data
        Format: Team1 vs Team2 Score1-Score2 League
        """
        # Skip comments and empty lines
        if line.startswith('#') or not line.strip():
            return None

        # Pattern to match: Team1 vs Team2 Score1-Score2 League
        pattern = r'^(.+?)\s+vs\s+(.+?)\s+(\d+)-(\d+)\s+(.+)$'
        match = re.match(pattern, line.strip())

        if match:
            home_team = match.group(1).strip()
            away_team = match.group(2).strip()
            home_score = int(match.group(3))
            away_score = int(match.group(4))
            league = match.group(5).strip()

            return GameData(
                home_team=home_team,
                away_team=away_team,
                home_score=home_score,
                away_score=away_score,
                league=league
            )
        else:
            print(f"Warning: Could not parse line: {line}")
            return None

    def load_games(self) -> List[GameData]:
        """Load and parse all games from the data file"""
        self.games = []

        if not os.path.exists(self.data_file):
            print(f"Error: Data file not found: {self.data_file}")
            return self.games

        with open(self.data_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                game = self.parse_line(line)
                if game:
                    self.games.append(game)
                    print(f"Loaded: {game}")

        print(f"\nTotal games loaded: {len(self.games)}")
        return self.games

    def get_unique_leagues(self) -> List[str]:
        """Get list of unique leagues in the data"""
        return list(set(game.league for game in self.games))

    def get_games_by_league(self, league: str) -> List[GameData]:
        """Get all games for a specific league"""
        return [game for game in self.games if game.league == league]


if __name__ == "__main__":
    # Test the parser
    parser = DataParser()
    games = parser.load_games()

    if games:
        print("\n=== Games by League ===")
        for league in parser.get_unique_leagues():
            league_games = parser.get_games_by_league(league)
            print(f"\n{league}: {len(league_games)} games")
            for game in league_games:
                print(f"  - {game.get_filename()}")