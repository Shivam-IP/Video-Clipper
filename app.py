import gradio as gr
import yt_dlp
import subprocess
import os
import json
import time
from google import genai
from pydantic import BaseModel

API_KEY = os.environ.get("GEMINI_API_KEY")

class SceneCuts(BaseModel):
    cut_timestamps_seconds: list[int]

def process_video(url):
    if not API_KEY:
        return None, "Error: GEMINI_API_KEY environment variable not set."

    # 1. Download Video
    video_filename = "input_video.mp4"
    ydl_opts = {
        'outtmpl': video_filename,
        'format': 'mp4',
        'quiet': True
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        return None, f"Download failed: {str(e)}"

    # 2. Upload to Gemini
    client = genai.Client(api_key=API_KEY)
    try:
        video_file = client.files.upload(file=video_filename)
        
        # Poll until processing completes
        while video_file.state == "PROCESSING":
            time.sleep(3)
            video_file = client.files.get(name=video_file.name)
            
        if video_file.state == "FAILED":
            return None, "Gemini failed to process the video."

        # 3. Request Cut Analysis
        prompt = """
        Analyze this video. Return a list of timestamps (in seconds) where a cut should happen.
        A cut must happen when:
        - The main subject or person in the frame changes.
        - The background or location changes (e.g., indoor to outdoor).
        - There is a sudden, significant visual change.
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[video_file, prompt],
            config={
                'response_mime_type': 'application/json',
                'response_schema': SceneCuts,
            },
        )
        
        client.files.delete(name=video_file.name)
        
        # 4. Extract Timestamps
        cut_data = json.loads(response.text)
        timestamps = cut_data.get("cut_timestamps_seconds", [])
        
        if not timestamps:
            return None, "No scene changes detected."

        # 5. Slice Video with FFmpeg
        clips = []
        start_time = 0
        
        # Ensure the last clip goes to the end of the video
        timestamps.append("end") 

        for i, end_time in enumerate(timestamps):
            output_clip = f"clip_{i+1:03d}.mp4"
            clips.append(output_clip)
            
            if end_time == "end":
                cmd = ["ffmpeg", "-y", "-i", video_filename, "-ss", str(start_time), "-c", "copy", output_clip]
            else:
                cmd = ["ffmpeg", "-y", "-i", video_filename, "-ss", str(start_time), "-to", str(end_time), "-c", "copy", output_clip]
                
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            start_time = end_time

        return clips, "Success! Video split into scenes."

    except Exception as e:
        return None, f"Processing error: {str(e)}"

# Gradio Interface
demo = gr.Interface(
    fn=process_video,
    inputs=gr.Textbox(label="Paste Video URL (YouTube/Vimeo)"),
    outputs=[
        gr.File(label="Download Generated Clips", file_count="multiple"),
        gr.Textbox(label="Status Logs")
    ],
    title="AI Scene Detector & Video Clipper"
)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 7860)))
