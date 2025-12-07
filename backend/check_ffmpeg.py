import imageio_ffmpeg
import subprocess
import os

ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
print(f"FFmpeg path: {ffmpeg_exe}")

try:
    result = subprocess.run([ffmpeg_exe, "-encoders"], capture_output=True, text=True)
    for line in result.stdout.splitlines():
        if any(x in line for x in ["nvenc", "amf", "qsv", "videotoolbox"]):
            print(line)
except Exception as e:
    print(f"Error running ffmpeg: {e}")
