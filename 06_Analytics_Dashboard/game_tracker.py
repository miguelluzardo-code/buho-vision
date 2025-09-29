"""
BUHO VISION - Game Tracking System
Track all games, processing status, and generate reports
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
import os

class GameTracker:
    def __init__(self, db_path="buho_vision_games.db"):
        """Initialize the game tracking database"""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        """Create all necessary tables for tracking"""

        # Main games table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                league TEXT NOT NULL,
                home_team TEXT NOT NULL,
                away_team TEXT NOT NULL,
                home_score INTEGER,
                away_score INTEGER,
                game_date DATE NOT NULL,
                venue TEXT,

                -- File locations
                veo_url TEXT,
                video_file_path TEXT,
                graphics_path TEXT,
                edited_video_path TEXT,

                -- Processing status
                download_status TEXT DEFAULT 'pending',
                graphics_status TEXT DEFAULT 'pending',
                editing_status TEXT DEFAULT 'pending',
                upload_status TEXT DEFAULT 'pending',

                -- YouTube info
                youtube_url TEXT,
                youtube_views INTEGER DEFAULT 0,
                upload_date DATETIME,

                -- Timestamps
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

                -- Additional info
                duration_minutes INTEGER,
                file_size_mb REAL,
                notes TEXT
            )
        ''')

        # Leagues table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS leagues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                sport TEXT NOT NULL,
                season TEXT,
                total_teams INTEGER,
                games_per_week INTEGER,
                logo_folder TEXT,
                contact_person TEXT,
                contact_phone TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Teams table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS teams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                league TEXT,
                logo_path TEXT,
                primary_color TEXT,
                secondary_color TEXT,
                stadium TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (league) REFERENCES leagues(name)
            )
        ''')

        # Processing log table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS processing_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER,
                action TEXT,
                status TEXT,
                error_message TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (game_id) REFERENCES games(id)
            )
        ''')

        self.conn.commit()
        print("Database tables created successfully!")

    # ==================== ADD DATA ====================

    def add_game(self, league, home_team, away_team, home_score, away_score, game_date, venue=None):
        """Add a new game to track"""
        try:
            self.cursor.execute('''
                INSERT INTO games (league, home_team, away_team, home_score, away_score, game_date, venue)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (league, home_team, away_team, home_score, away_score, game_date, venue))
            self.conn.commit()
            game_id = self.cursor.lastrowid
            print(f"[OK] Game added: {home_team} vs {away_team} (ID: {game_id})")
            return game_id
        except sqlite3.Error as e:
            print(f"[ERROR] Error adding game: {e}")
            return None

    def add_league(self, name, sport, season=None, total_teams=None):
        """Add a new league"""
        try:
            self.cursor.execute('''
                INSERT INTO leagues (name, sport, season, total_teams)
                VALUES (?, ?, ?, ?)
            ''', (name, sport, season, total_teams))
            self.conn.commit()
            print(f"[OK] League added: {name}")
            return True
        except sqlite3.IntegrityError:
            print(f"[INFO] League {name} already exists")
            return False

    def add_team(self, name, league=None, logo_path=None):
        """Add a new team"""
        try:
            self.cursor.execute('''
                INSERT INTO teams (name, league, logo_path)
                VALUES (?, ?, ?)
            ''', (name, league, logo_path))
            self.conn.commit()
            print(f"[OK] Team added: {name}")
            return True
        except sqlite3.IntegrityError:
            print(f"[INFO] Team {name} already exists")
            return False

    # ==================== UPDATE STATUS ====================

    def update_game_status(self, game_id, status_type, new_status):
        """Update processing status for a game
        status_type: 'download', 'graphics', 'editing', 'upload'
        new_status: 'pending', 'processing', 'completed', 'error'
        """
        valid_types = ['download', 'graphics', 'editing', 'upload']
        valid_statuses = ['pending', 'processing', 'completed', 'error']

        if status_type not in valid_types:
            print(f"[ERROR] Invalid status type. Use one of: {valid_types}")
            return False

        if new_status not in valid_statuses:
            print(f"[ERROR] Invalid status. Use one of: {valid_statuses}")
            return False

        column = f"{status_type}_status"
        query = f"UPDATE games SET {column} = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?"

        self.cursor.execute(query, (new_status, game_id))
        self.conn.commit()

        # Log the action
        self.log_action(game_id, f"{status_type}_status_change", new_status)
        print(f"[OK] Game {game_id}: {status_type} -> {new_status}")
        return True

    def update_youtube_info(self, game_id, youtube_url, upload_date=None):
        """Update YouTube information after upload"""
        if not upload_date:
            upload_date = datetime.now()

        self.cursor.execute('''
            UPDATE games
            SET youtube_url = ?, upload_date = ?, upload_status = 'completed'
            WHERE id = ?
        ''', (youtube_url, upload_date, game_id))
        self.conn.commit()
        print(f"[OK] YouTube URL updated for game {game_id}")

    # ==================== QUERIES ====================

    def get_pending_games(self, stage='all'):
        """Get games that need processing
        stage: 'download', 'graphics', 'editing', 'upload', 'all'
        """
        if stage == 'all':
            query = '''
                SELECT * FROM games
                WHERE download_status != 'completed'
                   OR graphics_status != 'completed'
                   OR editing_status != 'completed'
                   OR upload_status != 'completed'
                ORDER BY game_date DESC
            '''
        else:
            column = f"{stage}_status"
            query = f"SELECT * FROM games WHERE {column} = 'pending' ORDER BY game_date DESC"

        self.cursor.execute(query)
        games = self.cursor.fetchall()

        return self._format_games(games)

    def get_games_by_league(self, league_name):
        """Get all games for a specific league"""
        self.cursor.execute('''
            SELECT * FROM games
            WHERE league = ?
            ORDER BY game_date DESC
        ''', (league_name,))

        games = self.cursor.fetchall()
        return self._format_games(games)

    def get_games_by_date_range(self, start_date, end_date):
        """Get games within a date range"""
        self.cursor.execute('''
            SELECT * FROM games
            WHERE game_date BETWEEN ? AND ?
            ORDER BY game_date DESC
        ''', (start_date, end_date))

        games = self.cursor.fetchall()
        return self._format_games(games)

    def get_today_games(self):
        """Get today's games"""
        today = datetime.now().date()
        return self.get_games_by_date_range(today, today)

    def get_week_games(self):
        """Get this week's games"""
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        return self.get_games_by_date_range(week_ago, today)

    # ==================== REPORTS ====================

    def generate_league_report(self, league_name):
        """Generate a complete report for a league"""

        # Get league info
        self.cursor.execute("SELECT * FROM leagues WHERE name = ?", (league_name,))
        league_info = self.cursor.fetchone()

        # Get game statistics
        self.cursor.execute('''
            SELECT
                COUNT(*) as total_games,
                SUM(CASE WHEN upload_status = 'completed' THEN 1 ELSE 0 END) as uploaded,
                SUM(CASE WHEN upload_status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(youtube_views) as total_views,
                AVG(youtube_views) as avg_views
            FROM games
            WHERE league = ?
        ''', (league_name,))

        stats = self.cursor.fetchone()

        report = {
            'league': league_name,
            'league_info': league_info,
            'statistics': {
                'total_games': stats[0],
                'uploaded': stats[1],
                'pending': stats[2],
                'total_views': stats[3] or 0,
                'average_views': round(stats[4] or 0, 2)
            },
            'recent_games': self.get_games_by_league(league_name)[:10]
        }

        return report

    def generate_daily_report(self):
        """Generate daily processing report"""
        today = datetime.now().date()

        self.cursor.execute('''
            SELECT
                COUNT(*) as games_today,
                SUM(CASE WHEN download_status = 'completed' THEN 1 ELSE 0 END) as downloaded,
                SUM(CASE WHEN graphics_status = 'completed' THEN 1 ELSE 0 END) as graphics_done,
                SUM(CASE WHEN editing_status = 'completed' THEN 1 ELSE 0 END) as edited,
                SUM(CASE WHEN upload_status = 'completed' THEN 1 ELSE 0 END) as uploaded
            FROM games
            WHERE DATE(game_date) = ?
        ''', (today,))

        stats = self.cursor.fetchone()

        return {
            'date': str(today),
            'games_today': stats[0],
            'pipeline_status': {
                'downloaded': stats[1],
                'graphics_created': stats[2],
                'edited': stats[3],
                'uploaded': stats[4]
            },
            'completion_rate': round((stats[4] / stats[0] * 100) if stats[0] > 0 else 0, 2)
        }

    # ==================== UTILITIES ====================

    def log_action(self, game_id, action, status, error_message=None):
        """Log processing actions"""
        self.cursor.execute('''
            INSERT INTO processing_log (game_id, action, status, error_message)
            VALUES (?, ?, ?, ?)
        ''', (game_id, action, status, error_message))
        self.conn.commit()

    def _format_games(self, games):
        """Format game data for better readability"""
        if not games:
            return []

        # Get column names
        self.cursor.execute("PRAGMA table_info(games)")
        columns = [col[1] for col in self.cursor.fetchall()]

        # Convert to list of dictionaries
        formatted = []
        for game in games:
            game_dict = dict(zip(columns, game))
            formatted.append(game_dict)

        return formatted

    def export_to_json(self, filepath="games_export.json"):
        """Export all data to JSON"""
        self.cursor.execute("SELECT * FROM games")
        games = self._format_games(self.cursor.fetchall())

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(games, f, indent=2, default=str, ensure_ascii=False)

        print(f"[OK] Exported {len(games)} games to {filepath}")

    def get_statistics(self):
        """Get overall statistics"""
        self.cursor.execute('''
            SELECT
                COUNT(*) as total_games,
                COUNT(DISTINCT league) as total_leagues,
                COUNT(DISTINCT home_team) + COUNT(DISTINCT away_team) as approx_teams,
                SUM(CASE WHEN upload_status = 'completed' THEN 1 ELSE 0 END) as total_uploaded,
                SUM(youtube_views) as total_views
            FROM games
        ''')

        stats = self.cursor.fetchone()

        return {
            'total_games': stats[0],
            'total_leagues': stats[1],
            'approx_teams': stats[2] // 2,  # Rough estimate
            'total_uploaded': stats[3],
            'total_views': stats[4] or 0,
            'success_rate': round((stats[3] / stats[0] * 100) if stats[0] > 0 else 0, 2)
        }

    def close(self):
        """Close database connection"""
        self.conn.close()
        print("Database connection closed")


# ==================== EXAMPLE USAGE ====================

if __name__ == "__main__":
    # Initialize tracker
    tracker = GameTracker()

    print("\n=== BUHO VISION - Game Tracking System ===")
    print("=" * 50)

    # Add sample leagues
    tracker.add_league("Liga Kings", "Football", "2024", 140)
    tracker.add_league("Basketball Pro", "Basketball", "2024", 20)

    # Add sample teams
    tracker.add_team("LA NOCHE", "Liga Kings")
    tracker.add_team("LA CREMA", "Liga Kings")
    tracker.add_team("ATLETICO MINEIRO", "Liga Kings")
    tracker.add_team("JUVENTUS", "Liga Kings")

    # Add sample games
    print("\nAdding sample games...")
    game1 = tracker.add_game("Liga Kings", "LA NOCHE", "LA CREMA", 4, 2, "2024-01-15", "Estadio Central")
    game2 = tracker.add_game("Liga Kings", "ATLETICO MINEIRO", "LA 4", 1, 6, "2024-01-15", "Estadio Norte")
    game3 = tracker.add_game("Liga Kings", "JUVENTUS", "MILAN", 2, 1, "2024-01-16", "Estadio Sur")

    # Update some statuses
    print("\nUpdating game statuses...")
    tracker.update_game_status(game1, "download", "completed")
    tracker.update_game_status(game1, "graphics", "completed")
    tracker.update_game_status(game1, "editing", "processing")

    # Get pending games
    print("\nPending games:")
    pending = tracker.get_pending_games()
    for game in pending:
        print(f"  - {game['home_team']} vs {game['away_team']} ({game['league']})")

    # Generate statistics
    print("\nOverall Statistics:")
    stats = tracker.get_statistics()
    for key, value in stats.items():
        print(f"  - {key.replace('_', ' ').title()}: {value}")

    # Generate daily report
    print("\nDaily Report:")
    daily = tracker.generate_daily_report()
    print(f"  Games Today: {daily['games_today']}")
    print(f"  Completion Rate: {daily['completion_rate']}%")

    print("\n[OK] System ready to track your games!")

    # Close connection
    tracker.close()