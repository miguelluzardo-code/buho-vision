# 📤 YOUTUBE UPLOAD AUTOMATION - MEMORY

## 🎯 PHASE GOAL
Automatically upload edited videos to YouTube with proper metadata, thumbnails, and scheduling.

## 📊 CURRENT STATUS
**Status**: 🔴 Not Started
**Priority**: HIGH
**Estimated Time**: 2 weeks

## 🔧 TECHNICAL APPROACH

### YouTube API v3
- Official Google API
- OAuth 2.0 authentication
- Resumable uploads for large files
- Full metadata control

## 📝 UPLOAD REQUIREMENTS

### Video Information Needed:
```python
video_metadata = {
    "title": "LA NOCHE vs LA CREMA | Liga Kings | Jornada 15",
    "description": """
        ⚽ Partido completo: LA NOCHE vs LA CREMA
        🏆 Liga: Liga Kings
        📅 Fecha: 15/01/2024
        🏟️ Estadio: Estadio Central
        📊 Resultado: 4-2

        🎥 Grabado con tecnología Veo.co
        📺 Producido por Buho Vision

        #LigaKings #Football #Uruguay #BuhoVision
    """,
    "tags": ["Liga Kings", "LA NOCHE", "LA CREMA", "Football", "Uruguay"],
    "category": "17",  # Sports category
    "privacy": "public",
    "thumbnail": "path/to/thumbnail.jpg"
}
```

## 🔄 AUTOMATION WORKFLOW

```
1. FILE PREPARATION
   ├── Check video file integrity
   ├── Generate thumbnail
   └── Prepare metadata

2. AUTHENTICATION
   ├── Load credentials
   ├── Refresh token if needed
   └── Initialize API client

3. UPLOAD PROCESS
   ├── Create video resource
   ├── Start resumable upload
   ├── Monitor progress
   └── Handle interruptions

4. POST-UPLOAD
   ├── Set thumbnail
   ├── Add to playlist
   ├── Share link
   └── Log success

5. NOTIFICATIONS
   ├── Send WhatsApp to team
   ├── Post on social media
   └── Update database
```

## 💻 IMPLEMENTATION CODE

### Setup Structure:
```python
youtube_uploader/
├── auth/
│   ├── client_secrets.json
│   └── oauth2_token.json
├── config/
│   ├── upload_config.yml
│   └── metadata_templates.json
├── scripts/
│   ├── uploader.py
│   ├── thumbnail_generator.py
│   └── playlist_manager.py
└── logs/
    └── upload_history.log
```

### Core Functions:
```python
# Main upload function
def upload_video(video_path, metadata):
    youtube = authenticate()
    request = youtube.videos().insert(
        part="snippet,status",
        body=metadata,
        media_body=MediaFileUpload(video_path, resumable=True)
    )
    response = resumable_upload(request)
    return response['id']

# Batch upload
def batch_upload(video_queue):
    for video in video_queue:
        try:
            video_id = upload_video(video['path'], video['metadata'])
            add_to_playlist(video_id, video['league'])
            notify_completion(video)
        except Exception as e:
            log_error(e, video)
            retry_queue.append(video)
```

## 🎨 THUMBNAIL GENERATION

### Automatic Thumbnail Creation:
1. Extract frame at 10 seconds
2. Add score overlay
3. Add team logos
4. Add "COMPLETO" badge
5. Export as 1280x720 JPG

## 📊 YOUTUBE CHANNEL STRUCTURE

### Playlist Organization:
```
Buho Vision Channel/
├── Liga Kings 2024/
│   ├── Jornada 1
│   ├── Jornada 2
│   └── ...
├── Basketball League/
├── American Football/
└── Featured Matches/
```

## 🔑 API SETUP STEPS

### 1. Google Cloud Console:
- Create new project
- Enable YouTube Data API v3
- Create OAuth 2.0 credentials
- Download client_secrets.json

### 2. Authentication:
- First-time browser authentication
- Save refresh token
- Automated token refresh

### 3. Quota Management:
- 10,000 units per day limit
- Upload costs ~1600 units
- Max ~6 videos per day (need to request increase)

## 📋 METADATA TEMPLATES

### Football Template:
```json
{
    "title": "{home} vs {away} | {league} | Jornada {round}",
    "description_template": "football_template.txt",
    "tags": ["football", "{league}", "{home}", "{away}", "Uruguay", "Buho Vision"],
    "category": "17",
    "default_language": "es",
    "privacy": "public"
}
```

## 🚨 ERROR HANDLING

### Common Issues:
1. **Quota Exceeded**: Queue for next day
2. **Network Timeout**: Resume upload
3. **Invalid Metadata**: Validation before upload
4. **File Too Large**: Compress or split

## 📈 SUCCESS METRICS
- ⏱️ Upload time per video
- ✅ Success rate
- 📊 Views within 24h
- 🔄 Retry success rate

## 🔗 INTEGRATIONS
- **Input**: From Phase 3 (Video Editing)
- **Output**: To Phase 5 (Social Media)
- **Notifications**: Phase 7 (Client Notifications)

## 💡 ADVANCED FEATURES
- Scheduled publishing
- A/B thumbnail testing
- Auto-generated subtitles
- End screen templates
- Analytics retrieval

## 📚 LEARNING RESOURCES
- [YouTube API Documentation](https://developers.google.com/youtube/v3)
- [Google API Python Client](https://github.com/googleapis/google-api-python-client)
- [OAuth 2.0 Guide](https://developers.google.com/identity/protocols/oauth2)

---

*Phase 4 Memory Document*
*Status: Planning*
*Next Step: Create Google Cloud project*