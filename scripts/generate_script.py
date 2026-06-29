import os
import json
import sys
from pathlib import Path
import google.generativeai as genai

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import config

# Configure Gemini
if config.GEMINI_API_KEY:
    genai.configure(api_key=config.GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")
else:
    model = None

def generate_script(title, description, content):
    """
    Generates a structured YouTube Shorts script (JSON) from news content using Gemini.
    """
    if not model:
        raise ValueError("Gemini model is not configured. Check your GEMINI_API_KEY.")
        
    prompt = f"""
You are an expert YouTube Shorts content creator and professional script writer.
Your task is to convert the following news article into an engaging vertical video script (under 50 seconds, max 130 words total).

News Title: {title}
Description: {description}
Content: {content}

You must structure the video script into exactly 5 logical, sequential scenes.
Create a highly visual prompt for each scene that can be fed into an AI video generator (like Pika Labs). The prompt should be cinematic, descriptive, specify camera movements (e.g. slow zoom, panning), and be visually relevant to that scene's narration.

Return ONLY a valid JSON object matching the following structure:
{{
  "title": "A short catchy title for the video (with emojis)",
  "hook": "The opening line (0-3s) designed to stop scrolling",
  "scenes": [
    {{
      "scene_number": 1,
      "narration": "First sentence of voiceover (captions will overlay here). Must include the hook. Keep it very punchy and short (approx. 15-20 words).",
      "visual_prompt": "Cinematic visual description of what appears on screen. E.g. 'A close-up shot of a futuristic human-like robot thinking, neon blue backlights, slow dolly zoom, 4k, hyper-detailed.'"
    }},
    {{
      "scene_number": 2,
      "narration": "Second sentence/idea (approx. 15-20 words). Moves the story forward.",
      "visual_prompt": "Visual prompt describing a new action or setting. Include dynamic motion elements."
    }},
    {{
      "scene_number": 3,
      "narration": "Third sentence/idea (approx. 15-20 words). Presents key facts or statistics.",
      "visual_prompt": "Visual prompt describing details, digital graphics, or relevant conceptual scenes."
    }},
    {{
      "scene_number": 4,
      "narration": "Fourth sentence/idea (approx. 15-20 words). Describes the implications or why it matters.",
      "visual_prompt": "Visual prompt describing reaction, environment change, or futuristic impact."
    }},
    {{
      "scene_number": 5,
      "narration": "Fifth sentence/conclusion + Call to Action (approx. 15-20 words). E.g. 'What do you think? Leave a comment below and follow for more!'",
      "visual_prompt": "A finishing visual, engaging camera movement, or call-to-action motion graphics."
    }}
  ]
}}
"""
    try:
        print("[ScriptGenerator] Requesting structured script from Gemini...")
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        script_data = json.loads(response.text)
        
        # Save structured script to scripts/script.json
        output_path = config.SCRIPTS_DIR / "script.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(script_data, f, indent=2)
            
        print(f"[ScriptGenerator] Script generated and saved to {output_path}")
        
        # Also write narration to a text file for back-compat/reference
        full_text = []
        for scene in script_data.get("scenes", []):
            full_text.append(scene.get("narration", ""))
        
        with open(config.SCRIPTS_DIR / "script.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(full_text))
            
        return script_data
    except Exception as e:
        print(f"[ScriptGenerator] Failed to generate script: {e}")
        return None

if __name__ == "__main__":
    test_article = {
        "title": "OpenAI launches a new AI model",
        "description": "The company introduced a faster and more capable AI model.",
        "content": "OpenAI announced a new AI model that improves reasoning, coding, and automation while reducing operational costs."
    }
    
    script = generate_script(
        test_article["title"],
        test_article["description"],
        test_article["content"]
    )
    
    if script:
        print(json.dumps(script, indent=2))