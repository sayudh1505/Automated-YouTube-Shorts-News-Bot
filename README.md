# Automated YouTube Shorts News Bot

An automated pipeline to generate engaging, captioned YouTube Shorts from trending news topics. The bot fetches news, filters for safety/relevance, creates a script and visual prompts using Gemini, generates voiceovers and captions, retrieves/generates matching video clips, and assembles the final video.

## Features

- **Trending News Fetching:** Query-based news scraping.
- **Safety Filtering:** Content safety auditing to ensure YouTube compliance.
- **AI-Powered Scripting:** Uses Google Gemini to generate scripts and corresponding visual prompts for each scene.
- **Voiceover Synthesis:** Synthesizes voiceovers using ElevenLabs (with gTTS fallback).
- **Word-Level Captions:** Transcribes voiceovers using Whisper to generate precise, word-level timed captions.
- **Visuals Generation:** Integrates Fal.ai (Pika/video generation) or Pexels API (with Pillow-based static rendering fallback) to produce matching scene visuals.
- **Automated Editing:** Assembles the audio, video, and overlays into a professional 1080x1920 (9:16) YouTube Short.

---

## Directory Structure

```text
Automated_News/
├── assets/             # Project assets (overlays, music, etc.)
├── audio/              # Generated audio tracks (ignored by git)
├── captions/           # Transcribed subtitles/captions (ignored by git)
├── config/             # Configuration & path management
│   └── config.py
├── logs/               # Run logs (ignored by git)
├── news/               # News fetching modules
│   └── fetch_news.py
├── output/             # Final generated YouTube Shorts (ignored by git)
├── scripts/            # Core processing scripts
│   ├── assemble_video.py
│   ├── content_filter.py
│   ├── generate_captions.py
│   ├── generate_script.py
│   ├── generate_visuals.py
│   └── generate_voiceover.py
├── video/              # Temporary video scenes (ignored by git)
├── .env.example        # Environment template
├── .gitignore          # Files to exclude from source control
├── main.py             # Orchestrator & CLI entrypoint
└── README.md           # Documentation
```

---

## Setup & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/sayudh1505/Automated-YouTube-Shorts-News-Bot.git
cd Automated-YouTube-Shorts-News-Bot
```

### 2. Configure Environment Variables
Copy the template environment file:
```bash
cp .env.example .env
```
Open `.env` and fill in your keys:
- `GEMINI_API_KEY`: Required for scripting & scene layout.
- `NEWS_API_KEY`, `ELEVENLABS_API_KEY`, `FAL_KEY`, `PEXELS_API_KEY`: Optional but recommended for full feature set.

### 3. Install Dependencies
Create a virtual environment and install the required packages:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```
*(Note: Create a `requirements.txt` listing packages like `google-generativeai`, `moviepy`, `openai-whisper`, `python-dotenv`, `requests`, etc.)*

---

## Usage

Run the main pipeline by supplying a topic:

```bash
python main.py --topic "Artificial Intelligence"
```

### Options:
- `--topic <str>`: The keyword or topic to search trending news for (default: `technology`).
- `--clean`: Clean up intermediate scene files (individual scene clips/audio files) after final assembly.
- `--limit <int>`: Max headlines to retrieve (default: `5`).

---

## License

This project is licensed under the MIT License.
