import os
import json
import sys
from pathlib import Path
from faster_whisper import WhisperModel

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import config

def generate_word_captions(audio_path, output_json_path, model_size="tiny"):
    """
    Transcribes an audio file using faster-whisper with word-level timestamps,
    and writes the timestamps to a JSON file.
    """
    print(f"[Captions] Initializing Whisper model '{model_size}' on CPU...")
    # Initialize on CPU with int8 quantization for speed/resource efficiency
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    
    print(f"[Captions] Transcribing audio: {audio_path}...")
    segments, info = model.transcribe(str(audio_path), word_timestamps=True)
    
    words_list = []
    
    # Iterate through segments and collect word-level timestamps
    for segment in segments:
        if segment.words:
            for w in segment.words:
                # Strip leading/trailing whitespaces and convert to uppercase for high impact captions
                word_text = w.word.strip()
                if word_text:
                    words_list.append({
                        "word": word_text.upper(),
                        "start": round(w.start, 2),
                        "end": round(w.end, 2)
                    })
        else:
            print("[Captions] Warning: No word-level timestamps found for a segment.")
            
    print(f"[Captions] Transcribed {len(words_list)} words.")
    
    # Save the timestamps to JSON
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(words_list, f, indent=2)
        
    print(f"[Captions] Word-level captions saved to {output_json_path}")
    return words_list

if __name__ == "__main__":
    print("Testing Captions Generator...")
    audio_file = config.AUDIO_DIR / "voiceover.mp3"
    output_file = config.CAPTIONS_DIR / "captions.json"
    
    if not audio_file.exists():
        print(f"Please run generate_voiceover.py first to create {audio_file}")
    else:
        words = generate_word_captions(audio_file, output_file)
        if words:
            print("First 10 words:")
            print(json.dumps(words[:10], indent=2))
