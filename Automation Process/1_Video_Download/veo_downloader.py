"""
Veo.co Video Download Automation
=================================
Automates downloading videos from Veo.co sports platform using Playwright
"""

import asyncio
import json
import os
from pathlib import Path
from datetime import datetime
import random
from playwright.async_api import async_playwright
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('veo_downloads.log'),
        logging.StreamHandler()
    ]
)

class VeoDownloader:
    def __init__(self, auth_file="veo_auth.json", headless=True):
        self.auth_file = auth_file
        self.headless = headless
        self.download_dir = Path("C:/Users/mgarr/Documents/claude-projects/AI-Tutoring/buho_vision/Downloads")
        self.download_dir.mkdir(exist_ok=True)
        
    async def initial_setup(self):
        """One-time setup to save authentication"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                args=['--start-maximized']
            )
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = await context.new_page()
            
            logging.info("Please login to Veo.co manually...")
            await page.goto("https://app.veo.co")
            
            # Wait for manual login
            input("Complete login and navigate to your recordings, then press Enter...")
            
            # Save authentication state
            await context.storage_state(path=self.auth_file)
            logging.info(f"Authentication saved to {self.auth_file}")
            
            await browser.close()
            
    async def human_delay(self, min_seconds=2, max_seconds=5):
        """Simulate human-like delays"""
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)
        
    async def move_mouse_randomly(self, page):
        """Simulate random mouse movements"""
        for _ in range(random.randint(2, 4)):
            x = random.randint(100, 1800)
            y = random.randint(100, 900)
            await page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.1, 0.3))
            
    async def download_videos(self, max_videos=None):
        """Download videos from Veo.co"""
        if not Path(self.auth_file).exists():
            logging.error(f"Auth file {self.auth_file} not found. Run initial_setup first.")
            return
            
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.headless,
                downloads_path=str(self.download_dir)
            )
            
            # Load saved authentication
            context = await browser.new_context(
                storage_state=self.auth_file,
                accept_downloads=True
            )
            page = await context.new_page()
            
            try:
                # Navigate to recordings
                await page.goto("https://app.veo.co/matches")
                await self.human_delay(3, 5)
                
                # Wait for page to load
                await page.wait_for_selector('[data-testid="match-card"]', timeout=30000)
                
                # Get list of available matches
                matches = await page.query_selector_all('[data-testid="match-card"]')
                logging.info(f"Found {len(matches)} matches")
                
                download_count = 0
                for match in matches:
                    if max_videos and download_count >= max_videos:
                        break
                        
                    try:
                        # Simulate human behavior
                        await self.move_mouse_randomly(page)
                        await self.human_delay()
                        
                        # Click on match
                        await match.click()
                        await self.human_delay(3, 6)
                        
                        # Look for download button
                        download_btn = await page.query_selector('[data-testid="download-button"]')
                        if download_btn:
                            # Get match title for filename
                            title_element = await page.query_selector('[data-testid="match-title"]')
                            title = await title_element.inner_text() if title_element else f"match_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                            
                            # Start download
                            async with page.expect_download() as download_info:
                                await download_btn.click()
                                logging.info(f"Downloading: {title}")
                            
                            download = await download_info.value
                            
                            # Save with organized filename
                            filename = f"{title.replace('/', '_').replace(' ', '_')}.mp4"
                            filepath = self.download_dir / filename
                            await download.save_as(str(filepath))
                            
                            logging.info(f"Saved: {filepath}")
                            download_count += 1
                            
                        # Go back to matches list
                        await page.go_back()
                        await self.human_delay(2, 4)
                        
                    except Exception as e:
                        logging.error(f"Error downloading match: {e}")
                        continue
                        
            except Exception as e:
                logging.error(f"Error in download process: {e}")
                
            finally:
                await browser.close()
                logging.info(f"Downloaded {download_count} videos")
                
    async def download_specific_match(self, match_url):
        """Download a specific match by URL"""
        if not Path(self.auth_file).exists():
            logging.error(f"Auth file {self.auth_file} not found. Run initial_setup first.")
            return
            
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.headless,
                downloads_path=str(self.download_dir)
            )
            
            context = await browser.new_context(
                storage_state=self.auth_file,
                accept_downloads=True
            )
            page = await context.new_page()
            
            try:
                await page.goto(match_url)
                await self.human_delay(3, 5)
                
                # Wait for download button
                download_btn = await page.wait_for_selector('[data-testid="download-button"]', timeout=30000)
                
                # Simulate human behavior
                await self.move_mouse_randomly(page)
                await self.human_delay()
                
                # Download
                async with page.expect_download() as download_info:
                    await download_btn.click()
                    
                download = await download_info.value
                filepath = self.download_dir / download.suggested_filename
                await download.save_as(str(filepath))
                
                logging.info(f"Downloaded: {filepath}")
                
            except Exception as e:
                logging.error(f"Error downloading specific match: {e}")
                
            finally:
                await browser.close()

# CLI Interface
async def main():
    downloader = VeoDownloader()
    
    print("Veo.co Download Automation")
    print("-" * 30)
    print("1. Initial Setup (first time only)")
    print("2. Download recent videos")
    print("3. Download specific match")
    print("4. Exit")
    
    choice = input("\nSelect option: ")
    
    if choice == "1":
        await downloader.initial_setup()
    elif choice == "2":
        num = input("How many videos to download? (blank for all): ")
        max_videos = int(num) if num else None
        await downloader.download_videos(max_videos)
    elif choice == "3":
        url = input("Enter match URL: ")
        await downloader.download_specific_match(url)
    else:
        print("Exiting...")

if __name__ == "__main__":
    asyncio.run(main())
