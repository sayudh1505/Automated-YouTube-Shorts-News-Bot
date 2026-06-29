import os
import json
import sys
from pathlib import Path
from moviepy import AudioFileClip, concatenate_audioclips

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import config

# Try to import ElevenLabs and gTTS
try:
    from elevenlabs.client import ElevenLabs
    has_eleven = True
except ImportError:
    has_eleven = False
    print("[Voiceover] ElevenLabs library not available. Will use gTTS fallback.")

try:
    from gtts import gTTS
    has_gtts = True
except ImportError:
    has_gtts = False
    print("[Voiceover] gTTS library not available.")

def generate_voiceover_scene(text, output_path, voice_id=None, model_id=None):
    """
    Generates audio voiceover for a single string of text using ElevenLabs or gTTS fallback.
    """
    eleven_key = config.ELEVENLABS_API_KEY
    
    # 1. Try ElevenLabs
    if has_eleven and eleven_key:
        try:
            print(f"[Voiceover] Using ElevenLabs to synthesize: '{text[:40]}...'")
            client = ElevenLabs(api_key=eleven_key)
            
            voice = voice_id or config.DEFAULT_VOICE_ID
            model = model_id or config.DEFAULT_MODEL_ID
            
            audio_generator = client.text_to_speech.convert(
                text=text,
                voice_id=voice,
                model_id=model
            )
            
            # Write generator bytes to output_path
            with open(output_path, "wb") as f:
                for chunk in audio_generator:
                    if chunk:
                        f.write(chunk)
            print(f"[Voiceover] ElevenLabs audio saved to {output_path}")
            return True
        except Exception as e:
            print(f"[Voiceover] ElevenLabs synthesis failed: {e}. Trying gTTS...")
            
    # 2. Fallback to gTTS
    if has_gtts:
        try:
            print(f"[Voiceover] Using gTTS fallback to synthesize: '{text[:40]}...'")
            tts = gTTS(text=text, lang='en', tld='com')
            tts.save(str(output_path))
            print(f"[Voiceover] gTTS audio saved to {output_path}")
            return True
        except Exception as e:
            print(f"[Voiceover] gTTS synthesis failed: {e}")
            
    # 3. Raise error if no options worked
    raise RuntimeError("Failed to generate voiceover. Neither ElevenLabs nor gTTS was successful.")

def generate_voiceovers(script_json_path):
    """
    Generates voiceover for all scenes in the script JSON.
    Concatenates individual scene audios into a single 'audio/voiceover.mp3' file.
    Returns lists of (scene_audio_path, duration) or combined audio path.
    """
    with open(script_json_path, "r", encoding="utf-8") as f:
        script_data = json.load(f)
        
    scenes = script_data.get("scenes", [])
    if not scenes:
        print("[Voiceover] No scenes found in script.")
        return []
        
    scene_files = []
    
    # 1. Generate audio for each scene
    for scene in scenes:
        num = scene.get("scene_number", 1)
        narration = scene.get("narration", "")
        
        output_file = config.AUDIO_DIR / f"scene_{num}.mp3"
        generate_voiceover_scene(narration, output_file)
        
        # Determine duration
        audio_clip = AudioFileClip(str(output_file))
        duration = audio_clip.duration
        audio_clip.close()
        
        scene_files.append({
            "scene_number": num,
            "audio_path": str(output_file),
            "narration": narration,
            "duration": duration
        })
        
    # 2. Concatenate all audio files into a single voiceover file
    print("[Voiceover] Concatenating scene audios...")
    clips = []
    try:
        for item in scene_files:
            clips.append(AudioFileClip(item["audio_path"]))
            
        combined_clip = concatenate_audioclips(clips)
        combined_path = config.AUDIO_DIR / "voiceover.mp3"
        combined_clip.write_audiofile(str(combined_path), logger=None)
        combined_clip.close()
        print(f"[Voiceover] Combined voiceover saved to {combined_path}")
        
        # Close all child clips
        for c in clips:
            c.close()
            
        # Update script.json with audios metadata (adding duration)
        for i, item in enumerate(scene_files):
            script_data["scenes"][i]["audio_path"] = item["audio_path"]
            script_data["scenes"][i]["duration"] = item["duration"]
            
        script_data["combined_audio_path"] = str(combined_path)
        script_data["total_duration"] = sum(x["duration"] for x in scene_files)
        
        with open(script_json_path, "w", encoding="utf-8") as f:
            json.dump(script_data, f, indent=2)
            
        return scene_files
    except Exception as e:
        print(f"[Voiceover] Failed to concatenate audios: {e}")
        # Clean up
        for c in clips:
            try:
                c.close()
            except:
                pass
        return scene_files

if __name__ == "__main__":
    print("Testing Voiceover Generator...")
    script_path = config.SCRIPTS_DIR / "script.json"
    if not script_path.exists():
        print(f"Please run generate_script.py first to create {script_path}")
    else:
        results = generate_voiceovers(script_path)
        for r in results:
            print(f"Scene {r['scene_number']}: Duration = {r['duration']:.2f}s, Path = {r['audio_path']}")
