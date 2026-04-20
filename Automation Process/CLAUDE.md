# BUHO VISION - AUTOMATION PROCESS MEMORY

## PROJECT OVERVIEW
Automated sports video production pipeline for Buho Vision - processing game recordings from Veo.co to YouTube-ready videos with professional graphics.

## CURRENT WORKFLOW TO AUTOMATE
1. **Download** - Get recordings from Veo.co platform
2. **Graphics** - Generate scoreboard overlays in Photoshop
3. **Edit** - Process in Premiere Pro with graphics
4. **Export** - Render final videos
5. **Upload** - Publish to YouTube with metadata

## PHASE 1: GRAPHICS AUTOMATION ✅ IMPLEMENTED!

### SOLUTION IMPLEMENTED: HTML/CSS + Playwright
**Why we switched from Photoshop:**
- FREE vs $240+/year
- No license requirements
- Faster processing (5 graphics in 10 seconds)
- Easier to maintain and modify
- Better for batch processing

### WORKING COMPONENTS:
1. **scoreboard_template.html** - Professional scoreboard design
2. **generate_graphics.py** - Automated graphics generator
3. **data_parser.py** - Game data processor
4. Successfully tested with 5 Liga Kings games

## ORIGINAL PHASE 1 REQUIREMENTS (NOW OBSOLETE)
### Requirements
- **Input Format**: Text file with "Team1 vs Team2 Score1-Score2 LeagueName"
- **PSD Template**: Layered Photoshop file with placeholders
- **Team Logos**: PNG files in `Desktop\buho\1- Liga Kings\1 - Escudos\`
- **Output**: PNG graphics with transparent background
- **Naming**: "[HomeTeam] VS [AwayTeam] [League].png"

### Technical Stack
- Photoshop MCP Server (Windows)
- Python with photoshop-python-api
- Batch processing capability

### Liga Kings Assets
- **140+ team logos** available
- Format: "TEAM NAME.png" (spaces allowed)
- Examples: LA NOCHE.png, LA_CREMA.png, ATLETICO MINEIRO.png

## PHASE 2: VIDEO PIPELINE (PLANNED)
- Veo.co API integration
- Premiere Pro automation
- Automatic overlay positioning
- Batch rendering

## PHASE 3: DISTRIBUTION (PLANNED)
- YouTube API integration
- Metadata automation
- Thumbnail generation

## FOLDER STRUCTURE
```
Automation Process/
├── 1_Data_Input/        # Game data processing
├── 2_Graphics_Generation/ # Photoshop automation
├── 3_Video_Processing/   # Premiere integration
├── 4_Export_Upload/      # Final output
└── Templates/            # PSD and presets
```

## KEY PATHS
- Team Logos: `C:\Users\mgarr\Desktop\buho\1- Liga Kings-*\1- Liga Kings\1 - Escudos\`
- Working Directory: `C:\Users\mgarr\Documents\claude-projects\AI-Tutoring\buho_vision\`

## AUTOMATION RULES
1. Always check for missing logos before processing
2. Maintain separate output folders per league
3. Log all processed games
4. Handle Spanish characters properly (ñ, á, é, etc.)
5. Case-insensitive logo matching

## PROGRESS TRACKING
- [ ] Install Photoshop MCP server
- [ ] Create data parser for game info
- [ ] Build Photoshop automation script
- [ ] Test with Liga Kings data
- [ ] Implement batch processing
- [ ] Add error handling
- [ ] Create user interface

## NOTES
- Client prefers "VS" not "versus" in filenames
- ~20 leagues total (mostly football/soccer)
- 95% football, some basketball, one American football
- Spanish language content