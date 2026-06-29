import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
FAL_KEY = os.getenv("FAL_KEY")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not defined in the environment variables.")

# Media Directory Structure
NEWS_DIR = BASE_DIR / "news"
SCRIPTS_DIR = BASE_DIR / "scripts"
AUDIO_DIR = BASE_DIR / "audio"
VIDEO_DIR = BASE_DIR / "video"
CAPTIONS_DIR = BASE_DIR / "captions"
OUTPUT_DIR = BASE_DIR / "output"
ASSETS_DIR = BASE_DIR / "assets"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
for directory in [NEWS_DIR, SCRIPTS_DIR, AUDIO_DIR, VIDEO_DIR, CAPTIONS_DIR, OUTPUT_DIR, ASSETS_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Voice synthesis settings
DEFAULT_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "cgSgspJ2msm6clMCxTua") # Rachel voice ID (or general expressive voice)
DEFAULT_MODEL_ID = os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")

# Video Settings
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
VIDEO_FPS = 24