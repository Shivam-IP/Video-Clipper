# AI Video Scene Splitter 🎬

A full-stack automated video processing pipeline that detects semantic scene changes and splits video files into distinct clips. 

Built with **Python**, **Gradio**, **Google Gemini 2.5 Flash**, and **FFmpeg**. Designed for high-performance deployment on **Railway.app**.

## 🚀 Overview

This tool automates the process of "Shot Boundary Detection" using a multi-modal AI approach. Instead of relying solely on pixel-threshold differences, it leverages the **Gemini 2.5 Flash** model to semantically understand video content.

**Key Capabilities:**
* **Ingest:** Accepts video URLs (YouTube, Vimeo, etc.) via `yt-dlp`.
* **Analyze:** Detects cuts based on:
    * Subject changes (e.g., Person A → Person B).
    * Location shifts (Indoor → Outdoor).
    * Significant visual discontinuities.
* **Process:** Splits the raw video file into downloadable `.mp4` clips using `ffmpeg` with zero re-encoding (stream copy) for maximum speed.
* **Interface:** Provides a clean web UI via Gradio.

## 🛠️ Tech Stack

* **Core Logic:** Python 3.11+
* **AI Model:** Google Gemini 2.5 Flash (via `google-genai` SDK)
* **Video Processing:** FFmpeg (System-level), yt-dlp
* **Frontend:** Gradio
* **Infrastructure:** Railway (Nixpacks)

---

## ⚡ Quick Start (Local)

### Prerequisites
* Python 3.10 or higher
* [FFmpeg](https://ffmpeg.org/download.html) installed and added to your system PATH.
* A Google AI Studio API Key.

### Installation

1.  **Clone the repository**
    ```bash
    git clone [https://github.com/yourusername/ai-video-splitter.git](https://github.com/yourusername/ai-video-splitter.git)
    cd ai-video-splitter
    ```

2.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set Environment Variables**
    Create a `.env` file or export your key directly:
    ```bash
    export GEMINI_API_KEY="your_actual_api_key_here"
    ```

4.  **Run the App**
    ```bash
    python app.py
    ```
    Access the UI at `http://localhost:7860`.

---

## ☁️ Deployment (Railway)

This repository is optimized for **Railway.app** using Nixpacks to handle system-level dependencies.

### 1. Push to GitHub
Ensure your repository contains:
* `app.py`
* `requirements.txt`
* `nixpacks.toml` (Crucial for FFmpeg installation)

### 2. Connect to Railway
1.  Log in to [Railway.app](https://railway.app/).
2.  Click **New Project** → **Deploy from GitHub repo**.
3.  Select this repository.

### 3. Configure Variables
1.  Go to the **Variables** tab in your Railway project.
2.  Add the following key:
    * `GEMINI_API_KEY`: Your Google Gemini API key.

### 4. Build & Deploy
Railway will automatically detect the `nixpacks.toml` configuration, install FFmpeg, build the Python environment, and expose the Gradio interface.

---

## 📂 Project Structure

```text
├── app.py              # Main application logic & Gradio UI
├── requirements.txt    # Python dependencies
├── nixpacks.toml       # Railway build config (Installs FFmpeg)
├── .gitignore          # Ignores temp video files & env vars
└── README.md           # Documentation
