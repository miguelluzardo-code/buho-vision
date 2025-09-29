"""
BUHO VISION - Simple Interface for Game Tracking
Easy-to-use menu system for managing games
"""

from game_tracker import GameTracker
from datetime import datetime, timedelta
import os

class TrackerInterface:
    def __init__(self):
        self.tracker = GameTracker()
        self.running = True

    def clear_screen(self):
        """Clear the console screen"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def display_menu(self):
        """Display main menu"""
        print("\n" + "=" * 60)
        print("BUHO VISION - GAME TRACKING SYSTEM")
        print("=" * 60)
        print("\nMAIN MENU:\n")
        print("1. [+] Add New Game")
        print("2. [LIST] View Pending Games")
        print("3. [UPDATE] Update Game Status")
        print("4. [TODAY] Today's Games")
        print("5. [WEEK] This Week's Games")
        print("6. [REPORT] League Report")
        print("7. [STATS] Overall Statistics")
        print("8. [YOUTUBE] Add YouTube URL")
        print("9. [SEARCH] Search Games")
        print("10. [EXPORT] Export to JSON")
        print("\n0. [X] Exit")
        print("\n" + "-" * 60)

    def add_game(self):
        """Add a new game"""
        self.clear_screen()
        print("\n[+] ADD NEW GAME")
        print("-" * 40)

        # Show available leagues
        print("\nAvailable leagues: Liga Kings, Basketball Pro")
        league = input("League name: ").strip() or "Liga Kings"

        home_team = input("Home team: ").strip()
        away_team = input("Away team: ").strip()

        # Score input with validation
        while True:
            try:
                home_score = int(input("Home score: "))
                away_score = int(input("Away score: "))
                break
            except ValueError:
                print("[ERROR] Please enter valid numbers for scores")

        # Date input
        date_str = input("Game date (YYYY-MM-DD) or press Enter for today: ").strip()
        if not date_str:
            game_date = datetime.now().strftime("%Y-%m-%d")
        else:
            game_date = date_str

        venue = input("Venue (optional): ").strip() or None

        # Add the game
        game_id = self.tracker.add_game(
            league, home_team, away_team,
            home_score, away_score, game_date, venue
        )

        if game_id:
            print(f"\n[OK] Game added successfully! (ID: {game_id})")
            input("\nPress Enter to continue...")

    def view_pending_games(self):
        """View all pending games"""
        self.clear_screen()
        print("\n[LIST] PENDING GAMES")
        print("-" * 40)

        stages = ['download', 'graphics', 'editing', 'upload']

        for stage in stages:
            games = self.tracker.get_pending_games(stage)
            if games:
                print(f"\n[*] Pending {stage.upper()}:")
                for game in games:
                    print(f"  [{game['id']}] {game['home_team']} vs {game['away_team']} ({game['league']}) - {game['game_date']}")

        input("\nPress Enter to continue...")

    def update_game_status(self):
        """Update the status of a game"""
        self.clear_screen()
        print("\n[UPDATE] UPDATE GAME STATUS")
        print("-" * 40)

        # Get game ID
        try:
            game_id = int(input("\nEnter game ID: "))
        except ValueError:
            print("[ERROR] Invalid ID")
            return

        print("\nStatus types:")
        print("1. download")
        print("2. graphics")
        print("3. editing")
        print("4. upload")

        status_type_num = input("Select status type (1-4): ")
        status_types = ['download', 'graphics', 'editing', 'upload']

        try:
            status_type = status_types[int(status_type_num) - 1]
        except (ValueError, IndexError):
            print("[ERROR] Invalid selection")
            return

        print("\nNew status:")
        print("1. pending")
        print("2. processing")
        print("3. completed")
        print("4. error")

        new_status_num = input("Select new status (1-4): ")
        statuses = ['pending', 'processing', 'completed', 'error']

        try:
            new_status = statuses[int(new_status_num) - 1]
        except (ValueError, IndexError):
            print("[ERROR] Invalid selection")
            return

        # Update the status
        if self.tracker.update_game_status(game_id, status_type, new_status):
            print(f"\n[OK] Status updated successfully!")

        input("\nPress Enter to continue...")

    def view_today_games(self):
        """View today's games"""
        self.clear_screen()
        print("\n[TODAY] TODAY'S GAMES")
        print("-" * 40)

        games = self.tracker.get_today_games()

        if not games:
            print("\nNo games scheduled for today")
        else:
            for game in games:
                print(f"\n[{game['id']}] {game['home_team']} {game['home_score']} - {game['away_score']} {game['away_team']}")
                print(f"  League: {game['league']}")
                print(f"  Status: Download={game['download_status']}, Graphics={game['graphics_status']}, Edit={game['editing_status']}, Upload={game['upload_status']}")

        input("\nPress Enter to continue...")

    def view_week_games(self):
        """View this week's games"""
        self.clear_screen()
        print("\n[WEEK] THIS WEEK'S GAMES")
        print("-" * 40)

        games = self.tracker.get_week_games()

        if not games:
            print("\nNo games in the last 7 days")
        else:
            for game in games:
                print(f"\n[{game['id']}] {game['game_date']} - {game['home_team']} vs {game['away_team']}")
                print(f"  Score: {game['home_score']}-{game['away_score']}")
                print(f"  League: {game['league']}")
                if game['youtube_url']:
                    print(f"  YouTube: {game['youtube_url']}")

        input("\nPress Enter to continue...")

    def generate_league_report(self):
        """Generate report for a league"""
        self.clear_screen()
        print("\n[REPORT] LEAGUE REPORT")
        print("-" * 40)

        league_name = input("\nEnter league name (or press Enter for Liga Kings): ").strip() or "Liga Kings"

        report = self.tracker.generate_league_report(league_name)

        print(f"\n[STATS] Report for {report['league']}")
        print("-" * 40)

        stats = report['statistics']
        print(f"Total Games: {stats['total_games']}")
        print(f"Uploaded: {stats['uploaded']}")
        print(f"Pending: {stats['pending']}")
        print(f"Total Views: {stats['total_views']}")
        print(f"Average Views: {stats['average_views']}")

        if report['recent_games']:
            print("\nRecent Games:")
            for game in report['recent_games'][:5]:
                print(f"  - {game['home_team']} vs {game['away_team']} ({game['game_date']})")

        input("\nPress Enter to continue...")

    def view_statistics(self):
        """View overall statistics"""
        self.clear_screen()
        print("\n[STATS] OVERALL STATISTICS")
        print("-" * 40)

        stats = self.tracker.get_statistics()

        print(f"\nTotal Games Tracked: {stats['total_games']}")
        print(f"Total Leagues: {stats['total_leagues']}")
        print(f"Approximate Teams: {stats['approx_teams']}")
        print(f"Videos Uploaded: {stats['total_uploaded']}")
        print(f"Total YouTube Views: {stats['total_views']}")
        print(f"Success Rate: {stats['success_rate']}%")

        # Daily report
        daily = self.tracker.generate_daily_report()
        print(f"\nToday's Status:")
        print(f"  Games: {daily['games_today']}")
        print(f"  Completion Rate: {daily['completion_rate']}%")

        input("\nPress Enter to continue...")

    def add_youtube_url(self):
        """Add YouTube URL to a game"""
        self.clear_screen()
        print("\n[YOUTUBE] ADD YOUTUBE URL")
        print("-" * 40)

        try:
            game_id = int(input("\nEnter game ID: "))
        except ValueError:
            print("[ERROR] Invalid ID")
            return

        youtube_url = input("YouTube URL: ").strip()

        if youtube_url:
            self.tracker.update_youtube_info(game_id, youtube_url)
            print(f"\n[OK] YouTube URL added successfully!")

        input("\nPress Enter to continue...")

    def search_games(self):
        """Search for games"""
        self.clear_screen()
        print("\n[SEARCH] SEARCH GAMES")
        print("-" * 40)
        print("\nSearch by:")
        print("1. League")
        print("2. Date range")
        print("3. Team")

        choice = input("\nSelect option (1-3): ")

        if choice == "1":
            league = input("League name: ").strip()
            games = self.tracker.get_games_by_league(league)

        elif choice == "2":
            start_date = input("Start date (YYYY-MM-DD): ").strip()
            end_date = input("End date (YYYY-MM-DD): ").strip()
            games = self.tracker.get_games_by_date_range(start_date, end_date)

        elif choice == "3":
            team = input("Team name: ").strip()
            # Search in both home and away
            self.tracker.cursor.execute('''
                SELECT * FROM games
                WHERE home_team LIKE ? OR away_team LIKE ?
                ORDER BY game_date DESC
            ''', (f'%{team}%', f'%{team}%'))
            games = self.tracker._format_games(self.tracker.cursor.fetchall())

        else:
            print("[ERROR] Invalid option")
            return

        if games:
            print(f"\n[FOUND] {len(games)} games:")
            for game in games[:10]:  # Show max 10
                print(f"  [{game['id']}] {game['game_date']} - {game['home_team']} vs {game['away_team']} ({game['home_score']}-{game['away_score']})")
        else:
            print("\n[INFO] No games found")

        input("\nPress Enter to continue...")

    def export_json(self):
        """Export data to JSON"""
        self.clear_screen()
        print("\n[EXPORT] EXPORT TO JSON")
        print("-" * 40)

        filename = input("\nFilename (or press Enter for 'games_export.json'): ").strip()
        if not filename:
            filename = "games_export.json"

        self.tracker.export_to_json(filename)
        input("\nPress Enter to continue...")

    def run(self):
        """Main loop"""
        while self.running:
            self.clear_screen()
            self.display_menu()

            choice = input("\nSelect option: ").strip()

            if choice == "1":
                self.add_game()
            elif choice == "2":
                self.view_pending_games()
            elif choice == "3":
                self.update_game_status()
            elif choice == "4":
                self.view_today_games()
            elif choice == "5":
                self.view_week_games()
            elif choice == "6":
                self.generate_league_report()
            elif choice == "7":
                self.view_statistics()
            elif choice == "8":
                self.add_youtube_url()
            elif choice == "9":
                self.search_games()
            elif choice == "10":
                self.export_json()
            elif choice == "0":
                self.running = False
                print("\nGoodbye! Thanks for using Buho Vision Tracker!")
            else:
                print("[ERROR] Invalid option. Please try again.")
                input("\nPress Enter to continue...")

        self.tracker.close()


if __name__ == "__main__":
    # Run the interface
    interface = TrackerInterface()
    interface.run()