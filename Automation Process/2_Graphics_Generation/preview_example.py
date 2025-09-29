"""
Quick preview of a single scoreboard
"""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def generate_preview():
    template_path = Path(__file__).parent / "scoreboard_template.html"
    output_path = Path(__file__).parent / "preview_example.png"
    league_logo_path = r"C:\Users\mgarr\Desktop\buho\1- Liga Kings-20250925T142355Z-1-001\1- Liga Kings\5 - Miscelaneos\LIGA_KINGS.png"

    # Check for correct team logos
    logos_base = Path(r"C:\Users\mgarr\Desktop\buho\1- Liga Kings-20250925T142355Z-1-001\1- Liga Kings\1 - Escudos")

    # Try to find Bayern logo
    home_logo_path = ""
    for file in logos_base.glob("*BAYERN*"):
        home_logo_path = str(file)
        break
    if not home_logo_path:
        for file in logos_base.glob("*Bayern*"):
            home_logo_path = str(file)
            break
    if not home_logo_path:
        home_logo_path = r"C:\Users\mgarr\Desktop\buho\1- Liga Kings-20250925T142355Z-1-001\1- Liga Kings\1 - Escudos\BAYERN.png"

    # Try to find Arsenal logo
    away_logo_path = ""
    for file in logos_base.glob("*ARSENAL*"):
        away_logo_path = str(file)
        break
    if not away_logo_path:
        for file in logos_base.glob("*Arsenal*"):
            away_logo_path = str(file)
            break
    if not away_logo_path:
        away_logo_path = r"C:\Users\mgarr\Desktop\buho\1- Liga Kings-20250925T142355Z-1-001\1- Liga Kings\1 - Escudos\ARSENAL.png"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Show browser for preview
        page = await browser.new_page()
        await page.set_viewport_size({"width": 1500, "height": 350})

        # Load template
        template_url = f"file:///{template_path}".replace("\\", "/")
        await page.goto(template_url)

        # Update with sample data
        js_code = f"""
            updateScoreboard({{
                homeTeam: 'BAYERN',
                awayTeam: 'ARSENAL',
                homeScore: '3',
                awayScore: '1',
                homeLogo: 'file:///{home_logo_path.replace(chr(92), "/")}',
                awayLogo: 'file:///{away_logo_path.replace(chr(92), "/")}',
                leagueLogo: 'file:///{league_logo_path.replace(chr(92), "/")}',
                homePlaceholder: false,
                awayPlaceholder: false
            }});
        """
        await page.evaluate(js_code)

        # Wait for preview
        print("\n[PREVIEW] Browser opened with scoreboard!")
        print("[SCREENSHOT] Capturing image...")
        await page.wait_for_timeout(2000)

        # Take screenshot
        scoreboard = await page.query_selector('.scoreboard')
        if scoreboard:
            await scoreboard.screenshot(
                path=str(output_path),
                omit_background=True
            )
            print(f"[SUCCESS] Screenshot saved as: {output_path.name}")
            print(f"[PATH] Full path: {output_path}")

        print("\n[TIMER] Browser will close in 5 seconds...")
        await page.wait_for_timeout(5000)
        await browser.close()

if __name__ == "__main__":
    print("=" * 50)
    print("SCOREBOARD PREVIEW GENERATOR")
    print("=" * 50)
    asyncio.run(generate_preview())