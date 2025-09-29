"""
Test script to verify placeholder functionality for missing logos
"""
import asyncio
from generate_graphics import ScoreboardGenerator

async def main():
    print("\n" + "=" * 50)
    print("TESTING PLACEHOLDER FUNCTIONALITY")
    print("=" * 50 + "\n")

    generator = ScoreboardGenerator()

    # Process test file with missing logos
    await generator.process_all_games("test_missing_logos.txt")

    print("\n" + "=" * 50)
    print("TEST COMPLETE")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())