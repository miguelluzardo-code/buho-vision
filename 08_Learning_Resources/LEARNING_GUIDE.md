# 📚 BUHO VISION - LEARNING GUIDE
## Master Each Technology Step by Step

---

## 🎯 LEARNING PHILOSOPHY
**"Learn by doing, understand by building, master by teaching"**

Each technology you'll learn has immediate practical application in your business. No theory without practice!

---

## 🐍 PYTHON AUTOMATION (Weeks 1-2)

### What You'll Learn:
- Reading/writing files
- Web scraping with Selenium/Playwright
- Working with APIs
- Automating repetitive tasks

### Your First Project:
```python
# Day 1: Hello Buho Vision
print("Starting automation journey!")

# Day 3: Read game data
with open('game_data.txt', 'r') as file:
    games = file.readlines()
    for game in games:
        print(f"Processing: {game}")

# Day 5: Your first automation
from datetime import datetime
import os

def organize_files_by_date():
    # This could organize your video files!
    pass

# Week 2: Web scraping Veo.co
from playwright.sync_api import sync_playwright

def download_veo_games():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        # Your automation here!
```

### Resources:
- **Interactive**: [Python.org Tutorial](https://docs.python.org/3/tutorial/)
- **Video Course**: "Automate the Boring Stuff with Python"
- **Practice**: Start with organizing your existing video files

### Hands-On Exercises:
1. ✏️ Create a script to rename video files
2. ✏️ Build a game data parser
3. ✏️ Automate folder creation by date
4. ✏️ Scrape scores from a website

---

## 🌐 WEB SCRAPING (Weeks 1-3)

### Playwright vs Selenium:
```python
# We'll use Playwright (it's better!)
# Why? Faster, more reliable, better for modern websites

# Example: Login to Veo.co
async def veo_login(page):
    await page.goto('https://veo.co/login')
    await page.fill('input[name="email"]', 'your_email')
    await page.fill('input[name="password"]', 'your_password')
    await page.click('button[type="submit"]')
```

### Key Concepts:
1. **Finding Elements**: CSS selectors, XPath
2. **Waiting**: For pages to load, elements to appear
3. **Navigation**: Clicking, scrolling, downloading
4. **Sessions**: Keeping logged in, cookies

### Practice Project:
Build a Veo.co game lister that:
- Logs into your account
- Lists all available games
- Saves game info to a file
- Downloads one test video

---

## 🔑 API INTEGRATION (Weeks 3-4)

### YouTube API Basics:
```python
# What you'll build:
from googleapiclient.discovery import build

def upload_to_youtube(video_file, title, description):
    youtube = build('youtube', 'v3', credentials=creds)

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": description,
                "tags": ["Liga Kings", "Football"],
                "categoryId": "17"  # Sports
            },
            "status": {
                "privacyStatus": "public"
            }
        },
        media_body=MediaFileUpload(video_file)
    )
    response = request.execute()
    return response['id']
```

### What You'll Learn:
- OAuth 2.0 authentication
- Making API requests
- Handling responses
- Error management
- Rate limiting

### Mini Projects:
1. Upload a test video
2. Create a playlist
3. Update video metadata
4. Generate upload reports

---

## 🎬 VIDEO PROCESSING (Weeks 5-6)

### FFmpeg Fundamentals:
```bash
# You'll master these commands:

# Add watermark
ffmpeg -i game.mp4 -i logo.png \
  -filter_complex "overlay=10:10" output.mp4

# Cut video (remove first 30 seconds)
ffmpeg -i game.mp4 -ss 00:00:30 -c copy output.mp4

# Add intro
ffmpeg -i intro.mp4 -i game.mp4 \
  -filter_complex "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1" output.mp4

# Compress for faster upload
ffmpeg -i game.mp4 -c:v libx264 -crf 23 -c:a aac output.mp4
```

### Python + FFmpeg:
```python
import subprocess

def add_scoreboard_overlay(video_path, scoreboard_path):
    cmd = [
        'ffmpeg',
        '-i', video_path,
        '-i', scoreboard_path,
        '-filter_complex', '[1:v]scale=400:-1[ovr];[0:v][ovr]overlay=10:10:enable=between(t,0,10)',
        '-c:a', 'copy',
        'output.mp4'
    ]
    subprocess.run(cmd)
```

### Projects:
1. Add graphics to video
2. Create highlight clips
3. Batch process videos
4. Generate thumbnails

---

## 💾 DATABASE & TRACKING (Weeks 7-8)

### Simple Database for Games:
```python
import sqlite3
from datetime import datetime

# Create database
conn = sqlite3.connect('buho_vision.db')
cursor = conn.cursor()

# Track your games
cursor.execute('''
    CREATE TABLE IF NOT EXISTS games (
        id INTEGER PRIMARY KEY,
        league TEXT,
        home_team TEXT,
        away_team TEXT,
        score TEXT,
        date TEXT,
        veo_url TEXT,
        youtube_url TEXT,
        status TEXT
    )
''')

# Add a game
def add_game(league, home, away, score):
    cursor.execute('''
        INSERT INTO games (league, home_team, away_team, score, date, status)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (league, home, away, score, datetime.now(), 'pending'))
    conn.commit()

# Check pending games
def get_pending_games():
    cursor.execute("SELECT * FROM games WHERE status = 'pending'")
    return cursor.fetchall()
```

### What You'll Track:
- Game processing status
- Upload success/failures
- Processing times
- Error logs
- Performance metrics

---

## 🚀 DEPLOYMENT & SCHEDULING (Weeks 9-10)

### Automation Scheduling:
```python
# Using schedule library
import schedule
import time

def download_new_games():
    print("Checking for new games...")
    # Your download code here

def process_videos():
    print("Processing videos...")
    # Your processing code here

# Schedule tasks
schedule.every().day.at("02:00").do(download_new_games)
schedule.every(30).minutes.do(process_videos)

# Keep running
while True:
    schedule.run_pending()
    time.sleep(60)
```

### Windows Task Scheduler:
```xml
<!-- Create a task that runs your Python script -->
<Task>
    <Triggers>
        <CalendarTrigger>
            <StartBoundary>2024-01-15T02:00:00</StartBoundary>
            <Repetition>
                <Interval>PT24H</Interval>
            </Repetition>
        </CalendarTrigger>
    </Triggers>
    <Actions>
        <Exec>
            <Command>python</Command>
            <Arguments>C:\buho_vision\main_automation.py</Arguments>
        </Exec>
    </Actions>
</Task>
```

---

## 📱 SOCIAL MEDIA AUTOMATION (Weeks 11-12)

### Creating Clips for Social:
```python
def create_social_clip(video_path, start_time, duration=30):
    """Create a 30-second clip for Instagram/TikTok"""

    # Extract clip
    clip = extract_clip(video_path, start_time, duration)

    # Add captions
    add_captions(clip, "GOAL! ⚽")

    # Resize for platform
    resize_for_instagram(clip)  # 1080x1920
    resize_for_tiktok(clip)     # 9:16 ratio

    # Add music
    add_background_music(clip)

    return clip
```

---

## 🎓 LEARNING SCHEDULE

### Daily Practice (30 min/day):
- **Week 1-2**: Python basics
- **Week 3-4**: Web scraping
- **Week 5-6**: APIs
- **Week 7-8**: Video processing
- **Week 9-10**: Databases
- **Week 11-12**: Deployment

### Weekly Projects:
1. **Week 1**: Automate file organization
2. **Week 2**: Scrape game data
3. **Week 3**: Upload to YouTube
4. **Week 4**: Process a video
5. **Week 5**: Build tracking database
6. **Week 6**: Create dashboard
7. **Week 7**: Schedule automation
8. **Week 8**: Full pipeline test

---

## 💡 TIPS FOR SUCCESS

### 1. Start Small
Don't try to automate everything at once. Pick ONE task and automate it completely.

### 2. Test Everything
Always test with one game before processing 100.

### 3. Log Everything
Keep detailed logs of what works and what doesn't.

### 4. Ask for Help
The community is huge. Stack Overflow, Reddit, and GitHub are your friends.

### 5. Celebrate Wins
Every automated task is a victory. Celebrate it!

---

## 🆘 WHEN STUCK

### Debugging Checklist:
1. ✅ Is Python installed correctly?
2. ✅ Are all libraries installed?
3. ✅ Are file paths correct?
4. ✅ Do you have internet connection?
5. ✅ Are credentials valid?
6. ✅ Check the error message carefully

### Common Fixes:
```python
# Problem: "Module not found"
pip install missing_module

# Problem: "Permission denied"
# Run as administrator or check file permissions

# Problem: "Connection timeout"
# Add retry logic with delays

# Problem: "API rate limit"
# Add delays between requests
```

---

## 📈 MEASURING PROGRESS

### Week 1-2 Goals:
- [ ] Run your first Python script
- [ ] Automate one manual task
- [ ] Successfully scrape a website

### Week 3-4 Goals:
- [ ] Upload video to YouTube via API
- [ ] Download from Veo.co automatically

### Week 5-6 Goals:
- [ ] Process video with FFmpeg
- [ ] Create social media clips

### Week 7-8 Goals:
- [ ] Track games in database
- [ ] Generate reports

### Week 9-12 Goals:
- [ ] Full automation running
- [ ] 90% time reduction achieved

---

## 🎉 YOUR GRADUATION PROJECT

### The Final Test:
Build a system that:
1. Downloads 5 games from Veo.co
2. Adds graphics automatically
3. Processes videos
4. Uploads to YouTube
5. Posts highlights to social media
6. Sends completion notification

**All with ONE button click!**

---

*Remember: Every expert was once a beginner.*
*You're not just learning to code - you're building your business's future!*

**Start today. Automate tomorrow. Scale forever! 🚀**