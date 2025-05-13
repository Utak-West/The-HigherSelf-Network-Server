# Video Generation with MoneyPrinterTurbo

This document explains how to use the video generation capabilities in The HigherSelf Network Server, which integrates with MoneyPrinterTurbo to create high-quality short videos automatically.

## Overview

The video generation feature allows you to create professional-looking short videos by simply providing a topic or keyword. The system will:

1. Generate a script using AI
2. Find relevant high-quality, royalty-free video clips
3. Generate voice narration
4. Create subtitles
5. Add background music
6. Compile everything into a final video

All of this happens automatically while maintaining Notion as the central hub for tracking the video content lifecycle.

## Prerequisites

Before using the video generation feature, you need to:

1. Set up MoneyPrinterTurbo (see [Installation Options](#installation-options))
2. Configure your environment variables (see [Configuration](#configuration))
3. Obtain API keys for video sources (Pexels or Pixabay)
4. Ensure you have an API key for an LLM provider (OpenAI, Moonshot, etc.)

## Installation Options

### Option 1: Docker (Recommended)

```bash
# Clone the MoneyPrinterTurbo repository
git clone https://github.com/harry0703/MoneyPrinterTurbo.git
cd MoneyPrinterTurbo

# Create and configure your config.toml file
cp config.example.toml config.toml
# Edit config.toml with your API keys and preferences

# Run with Docker
docker-compose up -d
```

### Option 2: Manual Installation

```bash
# Clone the MoneyPrinterTurbo repository
git clone https://github.com/harry0703/MoneyPrinterTurbo.git
cd MoneyPrinterTurbo

# Create a virtual environment
conda create -n MoneyPrinterTurbo python=3.11
conda activate MoneyPrinterTurbo

# Install dependencies
pip install -r requirements.txt

# Install ImageMagick (platform-specific)
# For macOS: brew install imagemagick
# For Ubuntu: sudo apt-get install imagemagick

# Configure your settings
cp config.example.toml config.toml
# Edit config.toml with your API keys and preferences

# Start the API server
python main.py
```

## Configuration

Configure the video generation feature by setting the following environment variables in your `.env` file:

```
# MoneyPrinterTurbo API connection
MONEYPRINTER_API_URL=http://localhost:8080/api/v1

# Default video settings
MONEYPRINTER_DEFAULT_LANGUAGE=en
MONEYPRINTER_DEFAULT_VOICE=en-US-JennyNeural
MONEYPRINTER_DEFAULT_RESOLUTION=1080x1920
MONEYPRINTER_DEFAULT_CLIP_DURATION=5

# Subtitle settings
MONEYPRINTER_DEFAULT_SUBTITLE_POSITION=bottom
MONEYPRINTER_DEFAULT_SUBTITLE_COLOR=#FFFFFF
MONEYPRINTER_DEFAULT_SUBTITLE_SIZE=40
MONEYPRINTER_DEFAULT_SUBTITLE_STROKE_WIDTH=1.5

# Audio settings
MONEYPRINTER_DEFAULT_BACKGROUND_MUSIC_VOLUME=0.1

# API keys for video sources
PEXELS_API_KEY=your_pexels_api_key
PIXABAY_API_KEY=your_pixabay_api_key

# LLM settings
MONEYPRINTER_LLM_PROVIDER=openai
```

## API Endpoints

### Generate a Video

```http
POST /api/videos/generate
```

**Request Body:**

```json
{
  "topic": "mindfulness meditation",
  "language": "en",
  "voice_name": "en-US-JennyNeural",
  "resolution": "1080x1920",
  "clip_duration": 5,
  "subtitle_position": "bottom",
  "subtitle_color": "#FFFFFF",
  "subtitle_size": 40,
  "subtitle_stroke_width": 1.5,
  "background_music_volume": 0.1,
  "business_entity_id": "the_connection_practice"
}
```

**Response:**

```json
{
  "status": "success",
  "message": "Video generation started successfully",
  "content_id": "notion_page_id_here",
  "task_id": "mpt_task_id_here"
}
```

### Check Video Status

```http
GET /api/videos/{content_id}/status
```

**Response:**

```json
{
  "status": "success",
  "content_id": "notion_page_id_here",
  "video_status": "RENDERING",
  "video_url": null,
  "task_id": "mpt_task_id_here",
  "progress": 75.5,
  "message": null
}
```

When the video is complete, the `video_status` will be `COMPLETED` and the `video_url` will contain the URL to the generated video.

## Using in Your Code

You can also use the video generation capabilities programmatically through the Elan agent:

```python
from agents import Elan
from models.video_models import VideoGenerationConfig

# Initialize Elan agent
elan = Elan()

# Create video generation config
config = VideoGenerationConfig(
    topic="mindfulness meditation",
    language="en",
    voice_name="en-US-JennyNeural",
    resolution="1080x1920",
    clip_duration=5,
    subtitle_position="bottom",
    subtitle_color="#FFFFFF",
    subtitle_size=40,
    subtitle_stroke_width=1.5,
    background_music_volume=0.1
)

# Generate video
result = await elan.process_event(
    event_type="generate_video",
    event_data={
        "topic": config.topic,
        "language": config.language,
        "voice_name": config.voice_name,
        "resolution": config.resolution,
        "clip_duration": config.clip_duration,
        "subtitle_position": config.subtitle_position,
        "subtitle_color": config.subtitle_color,
        "subtitle_size": config.subtitle_size,
        "subtitle_stroke_width": config.subtitle_stroke_width,
        "background_music_volume": config.background_music_volume,
        "business_entity_id": "the_connection_practice"
    }
)

# Get content ID and task ID
content_id = result.get("content_id")
task_id = result.get("task_id")

# Check status later
status_result = await elan.process_event(
    event_type="get_video_status",
    event_data={"content_id": content_id}
)
```

## Video Status Lifecycle

The video generation process goes through several stages:

1. `PENDING`: Initial state when the request is received
2. `GENERATING_SCRIPT`: AI is generating the video script
3. `COLLECTING_MEDIA`: System is collecting video clips
4. `GENERATING_AUDIO`: Creating the voice narration
5. `GENERATING_SUBTITLES`: Creating subtitles
6. `RENDERING`: Compiling all elements into the final video
7. `COMPLETED`: Video generation is complete
8. `FAILED`: An error occurred during generation

## Troubleshooting

If you encounter issues with video generation:

1. Check that MoneyPrinterTurbo is running and accessible
2. Verify your API keys for Pexels/Pixabay and your LLM provider
3. Check the logs for error messages
4. Ensure ImageMagick is properly installed
5. Make sure your network can access external APIs

## Limitations

- Video generation can take several minutes depending on length and complexity
- The quality of generated videos depends on the available stock footage
- Some topics may not have suitable stock footage available
- The system works best with general topics rather than very specific ones
