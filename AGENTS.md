# Yolodex

## Project Overview

Automated pipeline to generate YOLO training data from YouTube gameplay videos using vision LLMs for labeling.

## Architecture

1. video-ingestion/ - Download YouTube videos, extract frames
2. labeler/ - Send frames to vision LLM, get bounding box labels
3. yolo-converter/ - Convert labels to YOLO format
4. trainer/ - Train YOLO model on generated data

## Commands

- Python 3.11+
- pip install -r requirements.txt
- Test: pytest

## Conventions

- Use Python
- Type hints everywhere
- Each component should be runnable standalone
