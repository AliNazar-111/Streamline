from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import tempfile, os, asyncio
from main_logic import generate_video, get_hardware_device

app = FastAPI()

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import psutil
try:
    import GPUtil
except ImportError:
    GPUtil = None

@app.get("/system-status")
def get_system_status():
    device = get_hardware_device()
    gpu_available = "GPU" in device and "Intel" not in device # Assume Intel is weak for now, or just check generic
    
    # Get Real-time stats
    cpu_usage = psutil.cpu_percent(interval=None)
    memory_usage = psutil.virtual_memory().percent
    
    gpu_stats = {"name": "None", "load": 0, "memory": 0}
    if GPUtil:
        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                gpu_stats = {
                    "name": gpu.name,
                    "load": round(gpu.load * 100, 1),
                    "memory": round(gpu.memoryUtil * 100, 1)
                }
        except:
            pass

    return {
        "device": device,
        "gpu_available": gpu_available,
        "cpu_usage": cpu_usage,
        "memory_usage": memory_usage,
        "gpu_stats": gpu_stats
    }

@app.post("/validate-keys")
async def validate_keys(
    api_key_gemini: str = Form(""),
    api_endpoint_gemini: str = Form(""),
    api_key_pexels: str = Form(""),
    api_key_pixabay: str = Form("")
):
    status = {"gemini": False, "pexels": False, "pixabay": False}
    
    # Check Gemini
    if api_key_gemini:
        try:
            import google.generativeai as genai
            from urllib.parse import urlparse
            
            config_args = {"api_key": api_key_gemini}
            
            # Sanitize endpoint if provided
            if api_endpoint_gemini:
                if "googleapis.com" in api_endpoint_gemini and "/models/" in api_endpoint_gemini:
                     parsed = urlparse(api_endpoint_gemini)
                     api_endpoint_gemini = f"{parsed.scheme}://{parsed.netloc}"
                config_args["client_options"] = {"api_endpoint": api_endpoint_gemini}
            
            genai.configure(**config_args)
            
            models_to_try = ['gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-pro']
            for model_name in models_to_try:
                try:
                    m = genai.GenerativeModel(model_name)
                    # Use generate_content with a dummy prompt for a real check
                    response = await asyncio.to_thread(m.generate_content, "Hi")
                    if response:
                        status["gemini"] = True
                        break
                except:
                    continue
        except Exception as e:
            print(f"Gemini Validation Error: {e}")
            pass
            
    # Check Pexels
    if api_key_pexels:
        try:
            import requests
            headers = {'Authorization': api_key_pexels}
            # Run in thread to avoid blocking
            resp = await asyncio.to_thread(requests.get, "https://api.pexels.com/v1/curated?per_page=1", headers=headers)
            if resp.status_code == 200:
                status["pexels"] = True
        except:
            pass

    # Check Pixabay
    if api_key_pixabay:
        try:
            import requests
            # Run in thread to avoid blocking
            resp = await asyncio.to_thread(requests.get, f"https://pixabay.com/api/?key={api_key_pixabay}&per_page=3")
            if resp.status_code == 200:
                status["pixabay"] = True
        except:
            pass
            
    return status

@app.post("/generate-video")
async def create_video(
    script: UploadFile,
    voiceover: UploadFile = None,
    competitor_url: str = Form(""),
    base_genre: str = Form("Documentary"),
    api_key_pexels: str = Form(""),
    api_key_pixabay: str = Form(""),
    api_key_gemini: str = Form(""),
    api_endpoint_gemini: str = Form(""),
    aspect_ratio: str = Form("16:9"),
    voice_name: str = Form("Female (Default)"),
    background_music: UploadFile = None,
    bg_music_volume: float = Form(0.1)
):
    script_text = (await script.read()).decode("utf-8")
    voiceover_bytes = None
    if voiceover:
        voiceover_bytes = await voiceover.read()
    
    bg_music_bytes = None
    if background_music:
        bg_music_bytes = await background_music.read()
        
    output_path = await generate_video(
        script_text=script_text,
        voiceover_file=voiceover_bytes,
        competitor_url=competitor_url,
        base_genre=base_genre,
        api_key_pexels=api_key_pexels,
        api_key_pixabay=api_key_pixabay,
        api_key_gemini=api_key_gemini,
        api_endpoint_gemini=api_endpoint_gemini,
        aspect_ratio=aspect_ratio,
        voice_name=voice_name,
        background_music_file=bg_music_bytes,
        bg_music_volume=bg_music_volume
    )
    return FileResponse(output_path, media_type="video/mp4", filename="autovideo.mp4")