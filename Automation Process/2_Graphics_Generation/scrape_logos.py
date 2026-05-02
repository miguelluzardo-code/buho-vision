"""
Descarga escudos Serie 5 (Div A/B/C Apertura 2026) desde API ligapro.uy
Endpoints: tournaments/{id}/games
"""

import asyncio
import re
import httpx
from pathlib import Path

OUTPUT_DIR = Path("/Users/miguelluzardo/Library/CloudStorage/GoogleDrive-miguelluzardo@gmail.com/Mi unidad/ProShot/LIGAS/12_Liga_PRO/1-ESCUDOS (sin fondo)")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BASE_API = "https://api.ligapro.uy/api"
HEADERS = {
    "Accept": "application/json",
    "Origin": "https://www.ligapro.uy",
    "Referer": "https://www.ligapro.uy/",
}

# Apertura 2026: todos los torneos
TOURNAMENTS = [
    484, 485, 486, 487, 488, 489, 490, 491, 492, 493, 494,
    496, 497, 498, 500, 501, 502, 503, 504, 506, 507, 508, 509,
    510, 512, 513, 514, 515, 516, 517, 518, 519, 521, 522
]

async def download_logo(client, url, name):
    if not url or 'default' in url.lower():
        return False
    try:
        resp = await client.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200 and len(resp.content) > 500:
            ext = Path(url.split('?')[0]).suffix or '.jpg'
            safe_name = re.sub(r'[<>:"/\\|?*]', '', name).strip()[:60]
            save_path = OUTPUT_DIR / f"{safe_name}{ext}"
            if save_path.exists():
                return False
            save_path.write_bytes(resp.content)
            print(f"  ✅ {safe_name}{ext}")
            return True
    except Exception as e:
        print(f"  ❌ {name}: {e}")
    return False

async def main():
    all_teams = {}  # name -> logo_url

    async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
        for tid in TOURNAMENTS:
            print(f"\n=== Torneo {tid} ===")
            resp = await client.get(f"{BASE_API}/tournaments/{tid}/games",
                                    headers=HEADERS, timeout=15)
            if resp.status_code != 200:
                print(f"  Error {resp.status_code}")
                continue

            games = resp.json()
            if isinstance(games, dict):
                games = games.get('data', [])

            print(f"  {len(games)} partidos encontrados")
            for game in games:
                local_name = game.get('local_team_name', '').strip()
                local_logo = game.get('local_team_logo', '')
                visit_name = game.get('visiting_team_name', '').strip()
                visit_logo = game.get('visiting_team_logo', '')

                if local_name and local_logo:
                    all_teams[local_name] = local_logo
                if visit_name and visit_logo:
                    all_teams[visit_name] = visit_logo

    print(f"\n=== {len(all_teams)} equipos únicos encontrados ===")
    for name in sorted(all_teams.keys()):
        print(f"  {name}")

    print(f"\n=== Descargando escudos ===")
    downloaded = 0
    async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
        for name, logo_url in all_teams.items():
            if await download_logo(client, logo_url, name):
                downloaded += 1

    print(f"\n✅ {downloaded} escudos nuevos descargados en:\n{OUTPUT_DIR}")


if __name__ == "__main__":
    asyncio.run(main())
