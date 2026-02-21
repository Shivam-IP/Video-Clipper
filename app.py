import gradio as gr
import yt_dlp
import subprocess
import os
import json
import time
import socket
from google import genai
from pydantic import BaseModel

# --- Configuration ---
API_KEY = os.environ.get("GEMINI_API_KEY")
MAX_FILE_SIZE_MB = 100 
MIN_SCENE_DURATION = 2.0  # Seconds: Clips shorter than this will be merged

# --- DNS BYPASS PATCH ---
try:
    YOUTUBE_IP = socket.gethostbyname('www.youtube.com')
except:
    YOUTUBE_IP = "142.250.190.46" 

original_getaddrinfo = socket.getaddrinfo
def patched_getaddrinfo(*args):
    if args[0] in ['www.youtube.com', 'youtube.com']:
        return original_getaddrinfo(YOUTUBE_IP, *args[1:])
    return original_getaddrinfo(*args)
socket.getaddrinfo = patched_getaddrinfo

class SceneCuts(BaseModel):
    cut_timestamps_seconds: list[float]

def process_video(url_input, file_input):
    if not API_KEY:
        return None, "Error: GEMINI_API_KEY not found."

    input_path = "temp_input.mp4"
    for f in os.listdir():
        if (f.startswith("clip_") and f.endswith(".mp4")) or f == input_path:
            try: os.remove(f)
            except: pass

    if file_input:
        file_size = os.path.getsize(file_input) / (1024 * 1024)
        if file_size > MAX_FILE_SIZE_MB:
            return None, f"Error: File too large ({file_size:.1f}MB)."
        input_path = file_input
        log_msg = "Processing upload..."
    elif url_input:
        log_msg = "Downloading URL..."
        ydl_opts = {'outtmpl': input_path, 'format': 'mp4', 'quiet': True, 'force_ipv4': True}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url_input])
        except Exception as e:
            return None, f"Download failed: {str(e)}"
    else:
        return None, "Please provide a source."

    client = genai.Client(api_key=API_KEY)
    try:
        video_file = client.files.upload(file=input_path)
        while video_file.state == "PROCESSING":
            time.sleep(2)
            video_file = client.files.get(name=video_file.name)
            
        prompt = "Analyze this video. Return a JSON list of timestamps (seconds) for scene cuts. Focus on subject or location changes."
        
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=[video_file, prompt],
            config={'response_mime_type': 'application/json', 'response_schema': SceneCuts},
        )
        try: client.files.delete(name=video_file.name)
        except: pass
        
        raw_timestamps = json.loads(response.text).get("cut_timestamps_seconds", [])
        
        # --- Minimum Duration Logic ---
        filtered_timestamps = []
        last_timestamp = 0.0
        for ts in sorted(raw_timestamps):
            if (ts - last_timestamp) >= MIN_SCENE_DURATION:
                filtered_timestamps.append(ts)
                last_timestamp = ts
        
        if not filtered_timestamps:
            return None, "No scenes met the minimum duration requirement."

        # Accurate Slicing Logic
        clips = []
        start_time = 0.0
        filtered_timestamps.append("end") 

        for i, end_time in enumerate(filtered_timestamps):
            output_clip = f"clip_{i+1:03d}.mp4"
            clips.append(output_clip)
            
            cmd = ["ffmpeg", "-y", "-i", input_path, "-ss", str(start_time)]
            if end_time != "end":
                cmd += ["-to", str(end_time)]
            
            # Re-encoding for accuracy
            cmd += ["-c:v", "libx264", "-crf", "23", "-preset", "ultrafast", "-c:a", "aac", output_clip]
            
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if end_time != "end":
                start_time = end_time

        return clips, f"Success! Created {len(clips)} clean clips (Min Duration: {MIN_SCENE_DURATION}s)."
    except Exception as e:
        return None, f"Processing error: {str(e)}"

# --- UI ---
with gr.Blocks(title="AI Video Clipper") as demo:
    gr.Markdown("# 🎬 Pro AI Video Scene Splitter")
    with gr.Tabs():
        with gr.TabItem("🔗 URL"):
            url_box = gr.Textbox(label="YouTube Link")
        with gr.TabItem("📁 Upload"):
            file_box = gr.Video(label="Local File (Max 100MB)")
            
    run_btn = gr.Button("Split Video", variant="primary")
    with gr.Row():
        output_display = gr.File(label="Generated Scenes", file_count="multiple")
        log_display = gr.Textbox(label="Logs")

    run_btn.click(fn=process_video, inputs=[url_box, file_box], outputs=[output_display, log_display])

if __name__ == "__main__":
    demo.launch()
