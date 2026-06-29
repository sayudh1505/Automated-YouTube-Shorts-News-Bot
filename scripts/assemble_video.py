import os
import json
import sys
from pathlib import Path
from moviepy import (
    VideoFileClip, 
    AudioFileClip, 
    TextClip, 
    CompositeVideoClip, 
    CompositeAudioClip,
    concatenate_videoclips
)

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import config

def make_vertical(clip, target_w=1080, target_h=1920):
    """
    Resizes and center-crops a video clip to 9:16 vertical ratio (1080x1920).
    Uses MoviePy 2.x 'resized' and 'cropped' methods.
    """
    clip_w, clip_h = clip.size
    aspect_ratio = clip_w / clip_h
    target_ratio = target_w / target_h
    
    # Check if clip is already vertical
    if abs(aspect_ratio - target_ratio) < 0.05:
        return clip.resized(width=target_w, height=target_h)
        
    if aspect_ratio > target_ratio:
        # Landscape: scale height to 1920, then crop width
        scaled = clip.resized(height=target_h)
        w, h = scaled.size
        cropped = scaled.cropped(
            width=target_w,
            height=target_h,
            x_center=w // 2,
            y_center=h // 2
        )
    else:
        # Portrait/Narrow: scale width to 1080, then crop height
        scaled = clip.resized(width=target_w)
        w, h = scaled.size
        cropped = scaled.cropped(
            width=target_w,
            height=target_h,
            x_center=w // 2,
            y_center=h // 2
        )
    return cropped

def assemble_youtube_short(script_json_path, captions_json_path, output_mp4_path):
    """
    Stitches video clips, voiceover, background music, and word-by-word captions
    into a finished 9:16 MP4 YouTube Short.
    """
    print(f"[Assembler] Reading script from {script_json_path}...")
    with open(script_json_path, "r", encoding="utf-8") as f:
        script_data = json.load(f)
        
    scenes = script_data.get("scenes", [])
    if not scenes:
        print("[Assembler] Error: No scenes found in script.")
        return False
        
    # 1. Load and format video clips
    print("[Assembler] Loading and formatting scene video clips...")
    clips = []
    for scene in scenes:
        video_path = scene.get("video_path")
        duration = scene.get("duration", 5.0)
        
        if not video_path or not Path(video_path).exists():
            print(f"[Assembler] Error: Video file for scene {scene['scene_number']} not found at {video_path}")
            return False
            
        print(f"[Assembler] Loading clip: {video_path} (Duration: {duration:.2f}s)")
        clip = VideoFileClip(video_path).with_duration(duration)
        vertical_clip = make_vertical(clip)
        clips.append(vertical_clip)
        
    # Stitch video clips together
    print("[Assembler] Concatenating video clips...")
    base_video = concatenate_videoclips(clips, method="compose")
    video_duration = base_video.duration
    print(f"[Assembler] Base video assembled. Total duration: {video_duration:.2f}s")
    
    # 2. Add Audio (Voiceover + Background Music)
    combined_audio_path = script_data.get("combined_audio_path")
    if not combined_audio_path or not Path(combined_audio_path).exists():
        combined_audio_path = str(config.AUDIO_DIR / "voiceover.mp3")
        
    if not Path(combined_audio_path).exists():
        print(f"[Assembler] Error: Voiceover audio not found at {combined_audio_path}")
        return False
        
    print(f"[Assembler] Loading voiceover audio: {combined_audio_path}")
    voiceover = AudioFileClip(combined_audio_path)
    
    audio_clips = [voiceover]
    
    # Check for background music fallback
    bg_music_path = config.ASSETS_DIR / "background_music.mp3"
    if bg_music_path.exists():
        print(f"[Assembler] Loading background music: {bg_music_path}")
        try:
            bg_music = AudioFileClip(str(bg_music_path))
            # Scale volume to a soft level (e.g. 8%) and loop to cover full video length
            bg_music = bg_music.with_volume_scaled(0.08).loop(duration=video_duration)
            audio_clips.append(bg_music)
        except Exception as e:
            print(f"[Assembler] Failed to load background music: {e}. Proceeding with voiceover only.")
    else:
        print("[Assembler] No background music found in assets/background_music.mp3. Using voiceover only.")
        
    final_audio = CompositeAudioClip(audio_clips)
    base_video = base_video.with_audio(final_audio)
    
    # 3. Add Subtitles / Captions (Word-by-word)
    print(f"[Assembler] Reading captions from {captions_json_path}...")
    if not Path(captions_json_path).exists():
        print(f"[Assembler] Warning: Captions file not found at {captions_json_path}. Assembling without captions.")
        final_video = base_video
    else:
        with open(captions_json_path, "r", encoding="utf-8") as f:
            word_captions = json.load(f)
            
        # Determine best available font
        selected_font = "impact.ttf"
        try:
            from PIL import ImageFont
            ImageFont.truetype(selected_font, 20)
        except Exception:
            try:
                selected_font = "arial.ttf"
                ImageFont.truetype(selected_font, 20)
            except Exception:
                selected_font = None # Default Pillow font

        print(f"[Assembler] Rendering {len(word_captions)} word captions using font: {selected_font}...")
        text_clips = []
        
        for idx, item in enumerate(word_captions):
            word = item.get("word", "")
            start = item.get("start", 0.0)
            end = item.get("end", 0.0)
            
            # Avoid divide-by-zero durations
            duration = max(0.1, end - start)
            
            # Render a high-impact caption
            txt_clip = TextClip(
                text=word,
                font=selected_font,
                font_size=80,
                color="yellow", # Vibrant yellow active text
                stroke_color="black",
                stroke_width=5,
                bg_color=None,
                transparent=True
            ).with_start(start).with_duration(duration).with_position(("center", "center"))
            
            text_clips.append(txt_clip)
            
        # Composite text clips on top of the base video
        final_video = CompositeVideoClip([base_video] + text_clips)
        
    # 4. Write Final Video file
    print(f"[Assembler] Exporting final YouTube Short to {output_mp4_path}...")
    final_video.write_videofile(
        str(output_mp4_path),
        fps=config.VIDEO_FPS,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile=str(config.OUTPUT_DIR / "temp_audio.m4a"),
        remove_temp=True,
        logger="bar" # standard progress bar
    )
    
    # Close resources
    final_video.close()
    base_video.close()
    voiceover.close()
    
    print(f"[Assembler] Successfully generated vertical Short! File location: {output_mp4_path}")
    return True

if __name__ == "__main__":
    print("Testing Video Assembler...")
    script_path = config.SCRIPTS_DIR / "script.json"
    captions_path = config.CAPTIONS_DIR / "captions.json"
    output_path = config.OUTPUT_DIR / "final_short.mp4"
    
    if not script_path.exists() or not captions_path.exists():
        print("Please ensure you have generated script, voiceover, and captions first.")
    else:
        assemble_youtube_short(script_path, captions_path, output_path)
