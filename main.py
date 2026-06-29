import os
import sys
import argparse
import json
import shutil
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent))

from config import config
from news.fetch_news import get_trending_news
from scripts.content_filter import filter_news_articles
from scripts.generate_script import generate_script
from scripts.generate_voiceover import generate_voiceovers
from scripts.generate_captions import generate_word_captions
from scripts.generate_visuals import generate_scene_visuals
from scripts.assemble_video import assemble_youtube_short

def cleanup_temp_files():
    """
    Cleans up intermediate audio, video, and captions files.
    """
    print("[Orchestrator] Cleaning up intermediate scene files...")
    
    # Clean audio directory, keeping voiceover.mp3
    for f in config.AUDIO_DIR.glob("scene_*.mp3"):
        try:
            f.unlink()
        except Exception as e:
            print(f"Failed to delete {f}: {e}")
            
    # Clean video directory, keeping final outputs
    for f in config.VIDEO_DIR.glob("scene_*.mp4"):
        try:
            f.unlink()
        except Exception as e:
            print(f"Failed to delete {f}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Automated YouTube Shorts News Bot Pipeline")
    parser.add_argument("--topic", type=str, default="technology", help="Topic/Keyword to fetch news about")
    parser.add_argument("--clean", action="store_true", help="Delete temporary scene files after generation")
    parser.add_argument("--limit", type=int, default=5, help="Number of headlines to fetch for filtering")
    
    args = parser.parse_args()
    
    print("="*60)
    print("      STARTING AUTOMATED YOUTUBE SHORTS NEWS PIPELINE")
    print("="*60)
    
    # Step 1: Fetch News
    print(f"\n[Step 1] Fetching trending news for topic: '{args.topic}'...")
    articles = get_trending_news(query=args.topic, count=args.limit)
    if not articles:
        print("[Orchestrator] Error: No articles retrieved. Exiting.")
        return
        
    print(f"[Orchestrator] Retrieved {len(articles)} articles.")
    
    # Step 2: Content Safety Filtering
    print("\n[Step 2] Running content safety audits...")
    safe_articles = filter_news_articles(articles)
    if not safe_articles:
        print("[Orchestrator] Error: No articles passed the safety check. Exiting.")
        return
        
    # Select the first safe article
    selected_article = safe_articles[0]
    print(f"\n[Orchestrator] Selected Article: '{selected_article['title']}' from {selected_article['source']}")
    
    # Step 3: Script & Scene Prompt Generation
    print("\n[Step 3] Generating video script and visual scene prompts via Gemini...")
    script_data = generate_script(
        selected_article["title"], 
        selected_article["description"], 
        selected_article["content"]
    )
    if not script_data:
        print("[Orchestrator] Error: Script generation failed. Exiting.")
        return
        
    script_path = config.SCRIPTS_DIR / "script.json"
    
    # Step 4: Voiceover Generation (ElevenLabs / gTTS)
    print("\n[Step 4] Synthesizing scene voiceovers...")
    scene_audios = generate_voiceovers(script_path)
    if not scene_audios:
        print("[Orchestrator] Error: Voiceover synthesis failed. Exiting.")
        return
        
    # Step 5: Caption Transcription (Whisper)
    print("\n[Step 5] Transcribing audio with word-level timestamps...")
    audio_file = config.AUDIO_DIR / "voiceover.mp3"
    captions_file = config.CAPTIONS_DIR / "captions.json"
    generate_word_captions(audio_file, captions_file)
    
    # Step 6: Visuals Generation (Fal.ai Pika / Pexels / Pillow fallback)
    print("\n[Step 6] Generating matching visual scene clips...")
    generate_scene_visuals(script_path)
    
    # Step 7: Video Assembly
    print("\n[Step 7] Stitching together final YouTube Short video...")
    output_video_path = config.OUTPUT_DIR / f"news_short_{args.topic.replace(' ', '_')}.mp4"
    success = assemble_youtube_short(script_path, captions_file, output_video_path)
    
    if success:
        print("\n" + "="*60)
        print("                 SHORT GENERATION SUCCESSFUL!")
        print("="*60)
        print(f"Output File: {output_video_path}")
        print("="*60)
        
        # Step 8: Clean up if requested
        if args.clean:
            cleanup_temp_files()
    else:
        print("\n[Orchestrator] Error: Video assembly stage failed.")

if __name__ == "__main__":
    main()
