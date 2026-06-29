import os
import json
import sys
import time
import urllib.request
import urllib.parse
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import VideoClip

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import config

def generate_video_fal(prompt, output_path):
    """
    Generates video via Fal.ai Pika Labs Text-to-Video API.
    """
    fal_key = config.FAL_KEY
    if not fal_key:
        print("[Visuals] No FAL_KEY found. Skipping Fal.ai.")
        return None
        
    try:
        print(f"[Visuals] Triggering Pika Text-to-Video via Fal.ai for prompt: '{prompt[:50]}...'")
        # Submit task to Fal queue
        url = "https://queue.fal.run/fal-ai/pika/v2.1/text-to-video"
        headers = {
            "Authorization": f"Key {fal_key}",
            "Content-Type": "application/json"
        }
        data = {
            "prompt": prompt,
            "aspect_ratio": "9:16"
        }
        
        req = urllib.request.Request(
            url, 
            data=json.dumps(data).encode("utf-8"), 
            headers=headers,
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=15) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            
        status_url = res_data.get("status_url")
        if not status_url:
            print("[Visuals] Fal.ai submission error: No status URL received.")
            return None
            
        # Poll queue until finished
        print("[Visuals] Polling Fal.ai queue for video generation...")
        max_attempts = 60
        for _ in range(max_attempts):
            time.sleep(3)
            status_req = urllib.request.Request(status_url, headers=headers)
            with urllib.request.urlopen(status_req, timeout=10) as s_resp:
                s_data = json.loads(s_resp.read().decode("utf-8"))
                
            status = s_data.get("status")
            if status == "COMPLETED":
                video_url = s_data.get("video", {}).get("url")
                if video_url:
                    print(f"[Visuals] Downloading generated video from: {video_url}")
                    urllib.request.urlretrieve(video_url, str(output_path))
                    print(f"[Visuals] Video saved to {output_path}")
                    return True
                else:
                    print("[Visuals] Fal.ai returned COMPLETED but no video URL was found.")
                    return None
            elif status == "FAILED":
                print(f"[Visuals] Fal.ai video generation failed: {s_data.get('logs')}")
                return None
                
        print("[Visuals] Fal.ai generation timed out.")
        return None
    except Exception as e:
        print(f"[Visuals] Fal.ai generation failed: {e}")
        return None

def generate_video_pexels(prompt, output_path, duration):
    """
    Downloads a royalty-free stock video from Pexels API matching the keyword.
    """
    pexels_key = config.PEXELS_API_KEY
    if not pexels_key:
        print("[Visuals] No PEXELS_API_KEY found. Skipping Pexels.")
        return None
        
    try:
        # Extract keywords from prompt for searching
        words = [w.strip(",.?!\"") for w in prompt.split() if len(w) > 4]
        query = " ".join(words[:2]) or "technology abstract"
        print(f"[Visuals] Searching Pexels for keyword: '{query}'")
        
        search_url = f"https://api.pexels.com/videos/search?query={urllib.parse.quote_plus(query)}&per_page=5"
        req = urllib.request.Request(search_url, headers={"Authorization": pexels_key})
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            
        videos = data.get("videos", [])
        if not videos:
            print(f"[Visuals] No Pexels videos found for '{query}'.")
            return None
            
        # Select first video and find hd file
        selected_video = videos[0]
        video_files = selected_video.get("video_files", [])
        
        # Prefer vertical (9:16) videos or just get the first file
        file_url = None
        for vf in video_files:
            # Check aspect ratio
            w = vf.get("width", 0)
            h = vf.get("height", 0)
            if h > 0 and (w / h) < 0.8: # vertical-ish
                file_url = vf.get("link")
                break
                
        if not file_url and video_files:
            file_url = video_files[0].get("link")
            
        if file_url:
            print(f"[Visuals] Downloading Pexels video from: {file_url}")
            # Request with standard user agent to avoid blockage
            req_dl = urllib.request.Request(
                file_url,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            )
            with urllib.request.urlopen(req_dl) as dl_resp:
                with open(output_path, "wb") as f:
                    f.write(dl_resp.read())
            print(f"[Visuals] Pexels video saved to {output_path}")
            return True
            
        return None
    except Exception as e:
        print(f"[Visuals] Pexels video fetch failed: {e}")
        return None

def generate_video_local_fallback(prompt, output_path, duration):
    """
    Creates a dynamic, animated gradient video locally using Pillow and MoviePy.
    Runs entirely offline and doesn't require any API keys.
    """
    print(f"[Visuals] Generating local motion-graphic fallback for prompt: '{prompt[:40]}...'")
    
    # Generate abstract grid/shapes that move over time
    width, height = config.VIDEO_WIDTH, config.VIDEO_HEIGHT
    
    # Color palette based on prompt content
    color_base = (20, 24, 33) # dark blue-gray default
    if "green" in prompt.lower() or "nature" in prompt.lower():
        color_base = (15, 33, 20)
    elif "red" in prompt.lower() or "fire" in prompt.lower() or "danger" in prompt.lower():
        color_base = (33, 15, 15)
    elif "yellow" in prompt.lower() or "warm" in prompt.lower() or "energy" in prompt.lower():
        color_base = (33, 28, 15)
        
    def make_frame(t):
        # Create pillow image
        img = Image.new("RGB", (width, height), color=color_base)
        draw = ImageDraw.Draw(img)
        
        # Center coordinates
        cx, cy = width // 2, height // 2
        
        # Draw some rotating/pulsing concentric circles
        for r_offset in [0, 80, 160, 240]:
            # Pulsing radius
            r = int(120 + r_offset + np.sin(t * 2 + r_offset / 100.0) * 40)
            
            # Fade colors out for larger circles
            intensity = max(50, 180 - r_offset // 2)
            outline_color = (intensity, int(intensity * 1.2), int(intensity * 1.5))
            
            draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=outline_color, width=3)
            
        # Draw floating particles
        num_particles = 15
        for i in range(num_particles):
            # Particle position changes with time t
            seed_x = (i * 73) % width
            seed_y = (i * 97) % height
            
            offset_x = int(np.sin(t * 1.5 + i) * 60)
            offset_y = int(np.cos(t * 1.2 + i) * 80)
            
            px = (seed_x + offset_x) % width
            py = (seed_y + offset_y) % height
            
            p_radius = 4 + (i % 6)
            draw.ellipse((px - p_radius, py - p_radius, px + p_radius, py + p_radius), fill=(80, 120, 220))
            
        # Subtle prompt indicator text at the bottom
        try:
            font = ImageFont.load_default()
            display_text = f"Prompt: {prompt[:80]}..."
            draw.text((40, height - 80), display_text, fill=(130, 130, 130), font=font)
        except:
            pass
            
        return np.array(img)
        
    # Generate MP4 clip using MoviePy
    clip = VideoClip(make_frame, duration=duration)
    # Write using simple libx264 codec
    clip.write_videofile(
        str(output_path), 
        fps=config.VIDEO_FPS, 
        codec="libx264", 
        audio=False, 
        logger=None
    )
    clip.close()
    print(f"[Visuals] Local fallback video saved to {output_path}")
    return True

def generate_scene_visuals(script_json_path):
    """
    Generates video clips for all scenes in the script JSON.
    """
    with open(script_json_path, "r", encoding="utf-8") as f:
        script_data = json.load(f)
        
    scenes = script_data.get("scenes", [])
    if not scenes:
        print("[Visuals] No scenes found in script.")
        return
        
    for scene in scenes:
        num = scene.get("scene_number", 1)
        prompt = scene.get("visual_prompt", "")
        # Duration generated during voiceover step (stored in script.json)
        duration = scene.get("duration", 5.0)
        
        output_file = config.VIDEO_DIR / f"scene_{num}.mp4"
        
        # Try Fal.ai
        success = generate_video_fal(prompt, output_file)
        
        # Try Pexels fallback
        if not success:
            success = generate_video_pexels(prompt, output_file, duration)
            
        # Try local motion-graphic fallback
        if not success:
            success = generate_video_local_fallback(prompt, output_file, duration)
            
        scene["video_path"] = str(output_file)
        
    # Save script.json updates
    with open(script_json_path, "w", encoding="utf-8") as f:
        json.dump(script_data, f, indent=2)
        
    print("[Visuals] Visual generation complete for all scenes.")

if __name__ == "__main__":
    print("Testing Visual Generator...")
    script_path = config.SCRIPTS_DIR / "script.json"
    if not script_path.exists():
        print(f"Please run generate_script.py and generate_voiceover.py first.")
    else:
        generate_scene_visuals(script_path)
