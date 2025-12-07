import os
import tempfile
import requests
import random
import yake
import asyncio
import edge_tts
try:
    import torch
except ImportError:
    torch = None
except OSError:
    torch = None
from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips, ColorClip, TextClip, CompositeVideoClip, vfx, ImageClip, CompositeAudioClip, afx

import subprocess
import google.generativeai as genai
import urllib.parse

def get_smart_styling(text, genre, api_key_gemini, api_endpoint_gemini=None):
    """
    Uses Gemini to determine the best font color, position, and style.
    Returns a dict with styling options.
    """
    if not api_key_gemini:
        return {
            "color": "#FFD700", # Default Gold
            "position": "center",
            "font": "Arial"
        }
    
    try:
        config_args = {"api_key": api_key_gemini}
        if api_endpoint_gemini:
            # Sanitize endpoint
            if "googleapis.com" in api_endpoint_gemini and "/models/" in api_endpoint_gemini:
                 from urllib.parse import urlparse
                 parsed = urlparse(api_endpoint_gemini)
                 api_endpoint_gemini = f"{parsed.scheme}://{parsed.netloc}"
            config_args["client_options"] = {"api_endpoint": api_endpoint_gemini}
        
        genai.configure(**config_args)
        
        # Try models in order
        models_to_try = ['gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-pro']
        model = None
        response = None
        
        prompt = f"""
        Analyze this sentence for a video in the '{genre}' genre: "{text}"
        Determine the best subtitle styling.
        Respond ONLY with a JSON object (no markdown) with these keys:
        - "color": Hex code (e.g., #FFFFFF) that contrasts well with the mood.
        - "position": "center", "bottom", or "top".
        - "font_mood": "bold", "playful", or "elegant".
        """

        for model_name in models_to_try:
            try:
                m = genai.GenerativeModel(model_name)
                response = m.generate_content(prompt)
                if response:
                    break
            except:
                continue
        
        if not response:
             return {"color": "#FFD700", "position": "center", "font": "Arial"}

        import json
        # Clean response of markdown code blocks if present
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        styling = json.loads(clean_text)
        
        # Map font_mood to actual fonts (assuming Windows standard fonts for now)
        font_map = {
            "bold": "Arial", # Fallback to Arial which we know works
            "playful": "Comic Sans MS",
            "elegant": "Georgia"
        }
        styling["font"] = font_map.get(styling.get("font_mood", "bold"), "Arial")
        
        return styling
    except Exception as e:
        print(f"Gemini Styling Error: {e}")
        return {"color": "#FFD700", "position": "center", "font": "Arial"}

def generate_fallback_image(prompt):
    """
    Generates an image using Pollinations.ai based on the prompt.
    Returns the path to the downloaded image.
    """
    try:
        # Add random seed to ensure uniqueness even for same prompt
        seed = random.randint(0, 999999)
        encoded_prompt = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?seed={seed}"
        return download_file(url, suffix=".jpg")
    except Exception as e:
        print(f"Image Gen Error: {e}")
        return None

def get_hardware_device():
    """Detects GPU using wmic (Windows) to support NVIDIA, AMD, and Intel."""
    try:
        # Check for NVIDIA via torch first (fastest if working)
        if torch and torch.cuda.is_available():
            return "GPU (NVIDIA CUDA)"
        
        # Fallback to WMIC for broader support (AMD/Intel/NVIDIA without CUDA)
        cmd = "wmic path win32_VideoController get name"
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        output = result.stdout.lower()
        
        if "nvidia" in output:
            return "GPU (NVIDIA)"
        elif "amd" in output or "radeon" in output:
            return "GPU (AMD)"
        elif "intel" in output and ("iris" in output or "arc" in output or "uhd" in output or "hd graphics" in output):
             # Intel iGPUs or dGPUs
            return "GPU (Intel)"
            
    except Exception as e:
        print(f"GPU Detection Error: {e}")
        
    return "CPU"

# ... (rest of the file)



async def generate_audio_from_text(text, voice="en-US-AriaNeural"):
    """Generates audio from text using Edge-TTS."""
    # Map friendly names to actual Edge-TTS voices
    voice_map = {
        "Male (Default)": "en-US-ChristopherNeural",
        "Female (Default)": "en-US-AriaNeural", 
        "Islamic (Male)": "ar-SA-HamedNeural", # Arabic accent/style often used for this
        "Islamic (Female)": "ar-SA-ZariyahNeural",
        "Deep (Male)": "en-US-EricNeural"
    }
    
    # If the voice is a key in our map, use the mapped value, otherwise assume it's a direct voice ID or default
    selected_voice = voice_map.get(voice, voice)
    if not selected_voice:
        selected_voice = "en-US-AriaNeural"

    print(f"Generating audio with voice: {selected_voice}")
    communicate = edge_tts.Communicate(text, selected_voice)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        await communicate.save(tmp.name)
        return tmp.name

def get_keywords(text, max_keywords=3):
    """Extract keywords from text using YAKE."""
    kw_extractor = yake.KeywordExtractor(lan="en", n=2, dedupLim=0.9, top=max_keywords, features=None)
    keywords = kw_extractor.extract_keywords(text)
    return [kw[0] for kw in keywords]

def fetch_pexels_videos(query, api_key, per_page=3):
    """Fetch video URLs from Pexels API."""
    if not api_key:
        return []
    headers = {'Authorization': api_key}
    url = f"https://api.pexels.com/videos/search?query={query}&per_page={per_page}"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        video_urls = []
        for video in data.get('videos', []):
            video_files = video.get('video_files', [])
            if video_files:
                video_files.sort(key=lambda x: x.get('width', 0), reverse=True)
                video_urls.append(video_files[0]['link'])
        return video_urls
    except Exception as e:
        print(f"Error fetching Pexels videos: {e}")
        return []

def fetch_pixabay_videos(query, api_key, per_page=3):
    """Fetch video URLs from Pixabay API."""
    if not api_key:
        return []
    url = f"https://pixabay.com/api/videos/?key={api_key}&q={query}&per_page={per_page}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        video_urls = []
        for hit in data.get('hits', []):
            videos = hit.get('videos', {})
            if 'large' in videos:
                video_urls.append(videos['large']['url'])
            elif 'medium' in videos:
                video_urls.append(videos['medium']['url'])
        return video_urls
    except Exception as e:
        print(f"Error fetching Pixabay videos: {e}")
        return []

def download_file(url, suffix=".mp4"):
    """Download a file from a URL to a temporary file."""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            for chunk in response.iter_content(chunk_size=8192):
                tmp.write(chunk)
            return tmp.name
    except Exception as e:
        print(f"Error downloading file {url}: {e}")
        return None

async def generate_video(script_text, voiceover_file, competitor_url, base_genre, api_key_pexels, api_key_pixabay, api_key_gemini, api_endpoint_gemini=None, aspect_ratio="16:9", voice_name="Female (Default)", background_music_file=None, bg_music_volume=0.1):
    """
    Generates a video based on the script and voiceover.
    """
    device = get_hardware_device()
    print(f"Starting video generation on {device} for genre: {base_genre}")
    
    # Determine dimensions
    if aspect_ratio == "9:16":
        target_width, target_height = 1080, 1920
    else:
        target_width, target_height = 1920, 1080
    
    audio_path = None
    
    try:
        # 1. Handle Audio (Upload vs TTS)
        if voiceover_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_audio:
                tmp_audio.write(voiceover_file)
                audio_path = tmp_audio.name
        else:
            print("No voiceover file provided. Generating TTS...")
            audio_path = await generate_audio_from_text(script_text, voice=voice_name)
        
        # Load audio to get duration
        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration
        print(f"Audio duration: {duration} seconds")

        # 2. Scene-Based Generation (Simple Split)
        # Split script into sentences for better relevance
        import re
        sentences = re.split(r'(?<=[.!?]) +', script_text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Calculate duration per sentence (approximate for now)
        # In a real app, we'd generate audio per sentence to get exact timing.
        # Here we'll just distribute total duration by char count ratio.
        total_chars = sum(len(s) for s in sentences)
        
        clips = []
        current_time = 0
        
        for sentence in sentences:
            sentence_duration = (len(sentence) / total_chars) * duration
            print(f"Processing scene: '{sentence[:30]}...' ({sentence_duration:.2f}s)")
            
            keywords = get_keywords(sentence)
            video_urls = []
            
            # Search for clips
            search_query = f"{base_genre} {' '.join(keywords)}"
            if api_key_pexels:
                video_urls.extend(fetch_pexels_videos(search_query, api_key_pexels))
            if api_key_pixabay:
                video_urls.extend(fetch_pixabay_videos(search_query, api_key_pixabay))
            
            random.shuffle(video_urls)
            
            scene_clip = None
            
            # Try to find a valid video clip
            for url in video_urls:
                video_path = download_file(url)
                if video_path:
                    try:
                        clip = VideoFileClip(video_path)
                        
                        # Resize logic for aspect ratio
                        if aspect_ratio == "9:16":
                            # Vertical crop
                            clip = clip.with_effects([vfx.Resize(height=target_height)])
                            if clip.w < target_width:
                                clip = clip.with_effects([vfx.Resize(width=target_width)])
                            clip = clip.cropped(x1=clip.w/2 - target_width/2, width=target_width, height=target_height)
                        else:
                            # Landscape
                            clip = clip.with_effects([vfx.Resize(height=target_height)])
                            if clip.w < target_width:
                                clip = clip.with_effects([vfx.Resize(width=target_width)])
                            clip = clip.cropped(x1=clip.w/2 - target_width/2, width=target_width, height=target_height)
                        
                        # Loop if too short
                        if clip.duration < sentence_duration:
                            clip = clip.loop(duration=sentence_duration)
                        else:
                            clip = clip.subclipped(0, sentence_duration)
                            
                        scene_clip = clip
                        break
                    except Exception as e:
                        print(f"Error processing clip: {e}")
            
            # Fallback if no video found
            if not scene_clip:
                # 1. Try AI Image Generation if Gemini Key is present
                if api_key_gemini:
                    try:
                        # Get prompt from Gemini
                        config_args = {"api_key": api_key_gemini}
                        if api_endpoint_gemini:
                            # Sanitize endpoint
                            if "googleapis.com" in api_endpoint_gemini and "/models/" in api_endpoint_gemini:
                                 from urllib.parse import urlparse
                                 parsed = urlparse(api_endpoint_gemini)
                                 api_endpoint_gemini = f"{parsed.scheme}://{parsed.netloc}"
                            config_args["client_options"] = {"api_endpoint": api_endpoint_gemini}
                        genai.configure(**config_args)
                        
                        # Try models in order
                        models_to_try = ['gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-pro']
                        prompt_resp = None
                        
                        prompt_req = f"Create a vivid, cinematic image prompt for this scene: '{sentence}'. Genre: {base_genre}. Keep it under 20 words."
                        
                        for model_name in models_to_try:
                            try:
                                m = genai.GenerativeModel(model_name)
                                prompt_resp = m.generate_content(prompt_req)
                                if prompt_resp:
                                    break
                            except:
                                continue
                        
                        if prompt_resp:
                            img_prompt = prompt_resp.text.strip()
                            print(f"Generated Image Prompt: {img_prompt}")
                            
                            img_path = generate_fallback_image(img_prompt)
                            if img_path:
                                img_clip = ImageClip(img_path).with_duration(sentence_duration)
                                # Resize image to target
                                img_clip = img_clip.with_effects([vfx.Resize(height=target_height)])
                                if img_clip.w < target_width:
                                    img_clip = img_clip.with_effects([vfx.Resize(width=target_width)])
                                img_clip = img_clip.cropped(x1=img_clip.w/2 - target_width/2, width=target_width, height=target_height)
                                scene_clip = img_clip
                    except Exception as e:
                        print(f"AI Image Fallback Failed: {e}")

                # 2. Modern Fallback (Color) if still no clip
                if not scene_clip:
                    bg_color = (20, 20, 30) # Dark Blue-Grey
                    scene_clip = ColorClip(size=(target_width, target_height), color=bg_color, duration=sentence_duration)

            # Add Subtitles (Modern Style)
            try:
                # Wrap text
                wrapped_text = "\n".join([sentence[i:i+40] for i in range(0, len(sentence), 40)])
                
                # Smart Styling
                style = get_smart_styling(sentence, base_genre, api_key_gemini, api_endpoint_gemini)
                print(f"Smart Style: {style}")
                
                # Map position to TextClip arguments or CompositeVideoClip positioning
                # TextClip in MoviePy v2 is a bit different, we'll generate it centered then position it in Composite
                
                txt_clip = TextClip(
                    text=wrapped_text, 
                    font_size=80 if aspect_ratio == "16:9" else 60, 
                    color=style.get("color", "#FFD700"), 
                    stroke_color='black', 
                    stroke_width=3, 
                    font=r'C:\Windows\Fonts\arial.ttf', # Keep safe font for now, or map style['font'] if we verify paths
                    size=(target_width - 200, None), # Width constraint, auto height
                    method='caption',
                    text_align='center'
                )
                txt_clip = txt_clip.with_duration(sentence_duration)
                
                # Positioning
                pos = style.get("position", "center")
                if pos == "bottom":
                    txt_pos = ('center', 'bottom')
                elif pos == "top":
                    txt_pos = ('center', 'top')
                else:
                    txt_pos = ('center', 'center')
                
                # Composite
                scene_clip = CompositeVideoClip([scene_clip, txt_clip.with_position(txt_pos)])
            except Exception as e:
                print(f"Subtitle failed: {e}")

            clips.append(scene_clip)
            current_time += sentence_duration

        final_clip = concatenate_videoclips(clips, method="compose")
        
        # Trim/Extend to exact audio duration
        final_clip = final_clip.with_duration(duration)
        
        # 4. Background Music Mixing
        final_audio = audio_clip
        bg_music_path = None
        
        if background_music_file:
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_bg:
                    tmp_bg.write(background_music_file)
                    bg_music_path = tmp_bg.name
                
                bg_music = AudioFileClip(bg_music_path)
                
                # Loop background music to match video duration
                if bg_music.duration < duration:
                    bg_music = afx.audio_loop(bg_music, duration=duration)
                else:
                    bg_music = bg_music.subclipped(0, duration)
                
                # Apply volume (ducking)
                bg_music = bg_music.with_volume_scaled(bg_music_volume)
                
                # Mix
                final_audio = CompositeAudioClip([audio_clip, bg_music])
                print("Background music added and mixed.")
                
            except Exception as e:
                print(f"Error adding background music: {e}")

        final_clip = final_clip.with_audio(final_audio)
        
        # Output file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp_out:
            output_path = tmp_out.name
        
        # Write video file
        # Check for GPU and try to use hardware encoders
        device_name = get_hardware_device()
        print(f"DEBUG: Detected device for encoding: {device_name}")
        
        # Helper to check encoder availability
        def check_encoder(enc_name):
            try:
                res = subprocess.run(["ffmpeg", "-encoders"], capture_output=True, text=True)
                return enc_name in res.stdout
            except:
                return False

        # Define codec priority based on device
        ffmpeg_params = ["-pix_fmt", "yuv420p"] # Standard pixel format
        codec = 'libx264' # Default CPU
        preset = 'ultrafast' # Default to fast for CPU
        
        if "NVIDIA" in device_name and check_encoder("h264_nvenc"):
            print("Attempting to render with GPU (NVIDIA) using h264_nvenc...")
            codec = 'h264_nvenc'
            # Use p1 (fastest) to ensure it works and is fast
            ffmpeg_params.extend(["-preset", "p1", "-rc", "constqp", "-qp", "28"])
            preset = None # Params handle it
        elif "AMD" in device_name and check_encoder("h264_amf"):
            print("Attempting to render with GPU (AMD) using h264_amf...")
            codec = 'h264_amf'
            ffmpeg_params.extend(["-usage", "transcoding", "-rc", "cqp", "-qp_i", "28"])
            preset = None
        elif "Intel" in device_name and check_encoder("h264_qsv"):
            print("Attempting to render with GPU (Intel) using h264_qsv...")
            codec = 'h264_qsv'
            ffmpeg_params.extend(["-global_quality", "28", "-preset", "veryfast"])
            preset = None
            
        # Write Video
        try:
            # Run blocking write_videofile in a separate thread to keep event loop alive for status updates
            print(f"Starting background rendering with {codec}...")
            
            # Prepare kwargs
            write_kwargs = {
                "filename": output_path,
                "fps": 24,
                "codec": codec,
                "audio_codec": "aac",
                "ffmpeg_params": ffmpeg_params,
                "threads": 12
            }
            if preset:
                write_kwargs["preset"] = preset
            
            await asyncio.to_thread(final_clip.write_videofile, **write_kwargs)
            
        except Exception as e:
            print(f"Hardware encoding failed ({e}). Falling back to CPU (Ultrafast)...")
            # Fallback to CPU with ultrafast preset to avoid 20 min waits
            await asyncio.to_thread(
                final_clip.write_videofile,
                output_path, 
                fps=24, 
                codec='libx264',
                audio_codec="aac",
                preset='ultrafast',
                threads=12
            )
            
        # Write Video
        try:
            # Run blocking write_videofile in a separate thread to keep event loop alive for status updates
            print(f"Starting background rendering with {codec}...")
            await asyncio.to_thread(
                final_clip.write_videofile,
                output_path, 
                fps=24, 
                codec=codec, 
                audio_codec="aac",
                ffmpeg_params=ffmpeg_params,
                threads=12
            )
        except Exception as e:
            print(f"Hardware encoding failed ({e}). Falling back to CPU (Ultrafast)...")
            # Fallback to CPU with ultrafast preset to avoid 20 min waits
            await asyncio.to_thread(
                final_clip.write_videofile,
                output_path, 
                fps=24, 
                codec='libx264',
                audio_codec="aac",
                preset='ultrafast',
                threads=12
            )
        
        return output_path
        


    except Exception as e:
        print(f"Error in generate_video: {e}")
        raise e
    finally:
        # Cleanup audio file
        if audio_path and os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except:
                pass
        if bg_music_path and os.path.exists(bg_music_path):
            try:
                os.remove(bg_music_path)
            except:
                pass
