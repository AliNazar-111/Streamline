import asyncio
import os
import numpy as np
from moviepy import AudioArrayClip
from main_logic import generate_video

def create_dummy_audio(filename, duration=2):
    rate = 44100
    t = np.linspace(0, duration, int(duration*rate))
    data = np.sin(2*np.pi*440*t) # 440Hz sine wave
    data = np.array([data, data]).T
    audio = AudioArrayClip(data, fps=rate)
    audio.write_audiofile(filename)
    return filename

async def test_audio_features():
    print("Testing Audio Features (Offline Mode)...")
    
    # 1. Create dummy background music
    print("Generating dummy background music...")
    bg_music_path = "dummy_bg.mp3"
    create_dummy_audio(bg_music_path, duration=5)
    
    with open(bg_music_path, "rb") as f:
        bg_music_bytes = f.read()
        
    # 2. Create dummy voiceover to bypass TTS
    print("Generating dummy voiceover...")
    voiceover_path = "dummy_voice.mp3"
    create_dummy_audio(voiceover_path, duration=3)
    
    with open(voiceover_path, "rb") as f:
        voiceover_bytes = f.read()
    
    # 3. Generate video
    print("Generating video with dummy audio...")
    try:
        output = await generate_video(
            script_text="Ignored because voiceover is provided.",
            voiceover_file=voiceover_bytes,
            competitor_url="",
            base_genre="Nature",
            api_key_pexels="",
            api_key_pixabay="",
            api_key_gemini="",
            voice_name="Islamic (Male)", # Should be ignored but passed
            background_music_file=bg_music_bytes,
            bg_music_volume=0.2
        )
        print(f"Video generated successfully at: {output}")
        
        # Move to workspace
        target_path = os.path.join(os.path.dirname(__file__), "..", "test_output_audio_offline.mp4")
        import shutil
        shutil.move(output, target_path)
        print(f"Video saved to: {target_path}")
        
    except Exception as e:
        print(f"Video generation failed: {e}")
    finally:
        if os.path.exists(bg_music_path):
            os.remove(bg_music_path)
        if os.path.exists(voiceover_path):
            os.remove(voiceover_path)

if __name__ == "__main__":
    asyncio.run(test_audio_features())
