# Baby Tools - Open-Source Content Creation Alternatives

This directory contains "baby versions" of expensive commercial content creation tools, built using open-source libraries and ingenuity.

## 🎯 Overview

Baby Tools provide 80% of the functionality at 0% of the cost. They are:
- **Simple**: Easy to understand and use
- **Effective**: Deliver professional results
- **Open**: Built on open-source foundations
- **Integrated**: Work seamlessly with the Content Creation Engine

## 📦 Available Tools

### 🎨 BabyCanva - Design Tool
**Alternative to:** Canva, Adobe Express

Simple design tool for creating social media graphics, thumbnails, and posts.

**Features:**
- Social media templates (Instagram, TikTok, YouTube, etc.)
- Text overlay on images
- Instagram-style filters
- Batch resizing for platforms
- Thumbnail generation

**Example:**
```python
from src.tools import BabyCanva

canva = BabyCanva(output_dir="./designs")

# Create Instagram post
post = canva.create_social_post(
    platform='instagram_post',
    text='Hello World!',
    background_color=(33, 150, 243)
)

# Create YouTube thumbnail
thumbnail = canva.create_thumbnail(
    title='Amazing Video Title',
    background_image='./background.jpg'
)

# Add text to image
result = canva.add_text_to_image(
    image_path='./photo.jpg',
    text='Check this out!',
    position='bottom'
)

# Apply filter
filtered = canva.apply_filter(
    image_path='./photo.jpg',
    filter_type='vintage'
)
```

---

### 🎬 BabyCapCut - Video Editor
**Alternative to:** CapCut, Adobe Premiere Rush

Quick video editing for social media content creation.

**Features:**
- Video trimming and cutting
- Caption/subtitle overlay
- Platform-specific resizing (TikTok, YouTube Shorts, etc.)
- Clip concatenation with transitions
- Background music overlay
- Speed control (slow-mo, time-lapse)

**Example:**
```python
from src.tools import BabyCapCut

editor = BabyCapCut(output_dir="./videos")

# Trim video
clip = editor.trim_video(
    video_path='./raw.mp4',
    start_time=10.0,
    end_time=40.0
)

# Add captions
captions = [
    {'text': 'Welcome!', 'start': 0, 'end': 2},
    {'text': 'This is cool', 'start': 2, 'end': 5}
]
captioned = editor.add_captions(
    video_path=clip,
    captions=captions
)

# Resize for TikTok
tiktok_video = editor.resize_for_platform(
    video_path=captioned,
    platform='tiktok'
)

# Add background music
final = editor.add_background_music(
    video_path=tiktok_video,
    audio_path='./music.mp3',
    audio_volume=0.3
)

# Concatenate multiple clips
compilation = editor.concatenate_videos(
    video_paths=['clip1.mp4', 'clip2.mp4', 'clip3.mp4'],
    transition_duration=0.5
)
```

---

### ✂️ BabyOpusClip - Auto-Clip Extraction
**Alternative to:** Opus Clip, Descript Clips

Automatically extract engaging clips from long videos.

**Features:**
- Scene detection
- AI-powered highlight extraction
- Sentiment analysis for engaging moments
- Auto-generate short-form content
- Compilation creation

**Example:**
```python
from src.tools import BabyOpusClip

clipper = BabyOpusClip(output_dir="./clips")

# Find engaging moments
moments = clipper.find_engaging_moments(
    video_path='./long_video.mp4',
    max_clips=5
)

# Extract highlight clips
clips = clipper.extract_highlights(
    video_path='./long_video.mp4',
    max_clips=5,
    clip_length=30.0
)

# Auto-generate a TikTok short
short = clipper.auto_generate_short(
    video_path='./podcast.mp4',
    target_length=30.0,
    platform='tiktok'
)

# Create compilation
compilation = clipper.create_compilation(
    clip_paths=clips
)

# Detect scenes
scenes = clipper.detect_scenes(
    video_path='./video.mp4',
    threshold=30.0
)
```

---

### 📊 BabyAnalytics - Self-Hosted Analytics
**Alternative to:** Google Analytics, Plausible

Privacy-friendly, self-hosted analytics system.

**Features:**
- Page view tracking
- Event tracking
- Traffic source analysis
- User session tracking
- Summary reports

**Example:**
```python
from src.tools import BabyAnalytics

analytics = BabyAnalytics(db_path="./analytics.db")

# Track page view
analytics.track_pageview(
    page_url='/video/amazing-content',
    session_id='session123',
    referrer='https://google.com'
)

# Track custom event
analytics.track_event(
    event_type='video_play',
    page_url='/video/amazing-content',
    properties={'video_id': 'abc123', 'duration': 120}
)

# Get summary statistics
summary = analytics.get_summary()
print(f"Page views: {summary['pageviews']}")
print(f"Unique sessions: {summary['unique_sessions']}")

# Get most popular pages
popular = analytics.get_popular_pages(limit=10)
for page in popular:
    print(f"{page['page_url']}: {page['views']} views")

# Analyze traffic sources
sources = analytics.get_traffic_sources(limit=20)
for source in sources:
    print(f"{source['source']}: {source['visits']} visits")
```

---

## 💰 Cost Comparison

| Category | Commercial Tool | Monthly Cost | Baby Tool | Cost |
|----------|----------------|--------------|-----------|------|
| Design | Canva Pro | $12.99 | BabyCanva | $0 |
| Video Edit | CapCut Pro | $9.99 | BabyCapCut | $0 |
| Clips | Opus Clip | $29.00 | BabyOpusClip | $0 |
| Analytics | Google Analytics | Free* | BabyAnalytics | $0 |
| **TOTAL** | | **$51.98/mo** | | **$0/mo** |

*GA is free for basic use but limits data and sells your users' data

**Annual Savings: $623.76**

---

## 🚀 Installation

Baby Tools are included with the Content Creation Engine. Install dependencies:

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install system dependencies
# Ubuntu/Debian:
sudo apt install ffmpeg

# macOS:
brew install ffmpeg
```

---

## 📚 Integration Example

Combine all baby tools for a complete content pipeline:

```python
from src.tools import BabyCanva, BabyCapCut, BabyOpusClip, BabyAnalytics

# Initialize tools
canva = BabyCanva()
editor = BabyCapCut()
clipper = BabyOpusClip()
analytics = BabyAnalytics()

# 1. Extract highlight from long video
clips = clipper.extract_highlights(
    video_path='./podcast_episode.mp4',
    max_clips=3,
    clip_length=30
)

# 2. Edit and add captions
for i, clip in enumerate(clips):
    # Add captions
    captioned = editor.add_captions(
        video_path=clip,
        captions=[{'text': f'Highlight #{i+1}', 'start': 0, 'end': 2}]
    )
    
    # Resize for platform
    final = editor.resize_for_platform(
        video_path=captioned,
        platform='tiktok'
    )
    
    clips[i] = final

# 3. Create thumbnail
thumbnail = canva.create_thumbnail(
    title='Amazing Podcast Highlights',
    background_image=clips[0]
)

# 4. Track analytics
analytics.track_event(
    event_type='video_created',
    properties={
        'clips_count': len(clips),
        'platform': 'tiktok'
    }
)

print(f"Created {len(clips)} clips ready for posting!")
```

---

## 🔧 Advanced Usage

### Custom Filters

Create your own Instagram-style filters:

```python
from PIL import Image, ImageEnhance

def my_custom_filter(img):
    # Increase saturation
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(1.4)
    
    # Increase contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.2)
    
    return img
```

### Batch Processing

Process multiple videos at once:

```python
import glob

video_files = glob.glob('./raw_videos/*.mp4')

for video in video_files:
    # Extract highlights
    clips = clipper.extract_highlights(video, max_clips=3)
    
    # Edit each clip
    for clip in clips:
        edited = editor.resize_for_platform(clip, 'instagram_reel')
        print(f"Processed: {edited}")
```

### Analytics API Integration

Create a REST API for analytics:

```python
from fastapi import FastAPI
from src.tools import BabyAnalytics

app = FastAPI()
analytics = BabyAnalytics()

@app.post("/track/pageview")
def track_pageview(page_url: str, session_id: str):
    analytics.track_pageview(page_url, session_id)
    return {"status": "tracked"}

@app.get("/stats/summary")
def get_summary():
    return analytics.get_summary()
```

---

## 📖 Documentation

Each tool has comprehensive docstrings. View in Python:

```python
from src.tools import BabyCanva
help(BabyCanva)
help(BabyCanva.create_social_post)
```

---

## 🤝 Contributing

Baby Tools are designed to be simple and maintainable. To add new features:

1. Keep the API simple
2. Handle errors gracefully
3. Log important events
4. Add docstrings with examples
5. Test with real content

---

## ⚠️ Limitations

Baby Tools are simplified versions focused on core functionality:

- **BabyCanva**: No advanced graphics editing like layers or masks
- **BabyCapCut**: No complex transitions or effects
- **BabyOpusClip**: Sentiment analysis is basic, not AI-powered like Opus
- **BabyAnalytics**: No real-time dashboards or advanced segmentation

For 80% of content creation tasks, these limitations don't matter!

---

## 🎯 Future Enhancements

Potential additions:
- BabyNotion - Note-taking and knowledge base
- BabyMusicGen - Background music generation
- BabyImageGen - AI image generation wrapper
- BabyScheduler - Social media scheduling

---

## 📄 License

Same as the parent project (MIT License). These tools use open-source libraries:
- Pillow (PIL Fork) - HPND License
- FFmpeg - LGPL/GPL
- MoviePy - MIT License
- Whisper - MIT License
- PySceneDetect - BSD License

---

Built with ❤️ for content creators who want to keep their money 💰
