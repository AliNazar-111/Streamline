import subprocess
import sys

def check_gpu():
    print("--- Checking Hardware via WMIC ---")
    try:
        cmd = "wmic path win32_VideoController get name"
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        print(result.stdout)
    except Exception as e:
        print(f"WMIC Error: {e}")

    print("\n--- Checking FFmpeg Encoders ---")
    try:
        cmd = "ffmpeg -encoders"
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if "h264_nvenc" in result.stdout:
            print("SUCCESS: h264_nvenc found!")
        else:
            print("WARNING: h264_nvenc NOT found in ffmpeg encoders.")
            
        if "h264_amf" in result.stdout:
            print("SUCCESS: h264_amf found!")
        
        if "h264_qsv" in result.stdout:
            print("SUCCESS: h264_qsv found!")
            
    except Exception as e:
        print(f"FFmpeg Error: {e}")

if __name__ == "__main__":
    check_gpu()