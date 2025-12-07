import asyncio
import os
import numpy as np
from moviepy import AudioArrayClip
from main_logic import generate_video

# Test with TTS (no voiceover file)
print("Calling generate_video with TTS...")
try:
    output = asyncio.run(generate_video(
        script_text="In a small café, Nora sketches dreams on napkins. One gust of wind steals her latest drawing... up, up it dances! She chases—laughing!—as strangers join in. When the napkin lands, it’s in a child’s hands, smiling like a sunrise. Nora decides—yes, the world is her gallery.",
        voiceover_file=None,
        competitor_url="",
        base_genre="Cartoon",
        api_key_pexels="",
        api_key_pixabay="",
        api_key_gemini="",
        aspect_ratio="16:9"
    ))
    print(f"Video generated successfully at: {output}")
    
    # Move to workspace for easy access
    target_path = os.path.join(os.path.dirname(__file__), "..", "test_output_tts.mp4")
    import shutil
    shutil.move(output, target_path)
    print(f"Video saved to: {target_path}")
except Exception as e:
    print(f"Video generation failed: {e}")
finally:
    if os.path.exists("test_voiceover.mp3"):
        os.remove("test_voiceover.mp3")
