---
name: collect
description: Download YouTube videos and extract frames using yt-dlp and ffmpeg for YOLO training data. Use when you need to gather frames from a video URL.
---

## Instructions
1. Read config.json for video_url, fps, output_dir
2. Run: uv run .agents/skills/collect/scripts/run.py
3. Outputs: output/video.mp4, output/frames/frame_*.jpg
