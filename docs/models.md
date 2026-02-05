# models reference

## vision models (for labeling)

used in the label skill to detect objects in game screenshots and return bounding boxes.

| model | input cost | output cost | speed | quality | notes |
|-------|-----------|-------------|-------|---------|-------|
| **gpt-5-nano** | cheapest | cheapest | fastest | good | **default** — best for high-volume labeling |
| **gpt-5-mini** | low | low | fast | better | reasoning model, slight thinking overhead |
| **gpt-4.1-nano** | $0.10/1M | $0.40/1M | very fast | good | non-reasoning, excellent for structured output |
| **gpt-4.1-mini** | $0.40/1M | $1.60/1M | fast | very good | **best accuracy/cost balance** |
| **gpt-4o** | $2.50/1M | $10.00/1M | medium | excellent | legacy, 25x more expensive than 4.1-nano |
| **gpt-5.2** | $1.75/1M | $14.00/1M | slow | best | flagship reasoning, overkill for bbox detection |

### how to change

edit `config.json`:

```json
{
  "model": "gpt-4.1-mini"
}
```

### structured outputs

the label skill uses the responses API with `text=RESPONSE_SCHEMA` (strict JSON schema enforcement). this means:

- the model is **guaranteed** to return valid JSON matching our bounding box schema
- no more regex fallback parsing needed
- works with all models listed above

### cost estimate

for a 5-minute gameplay video at 1 fps = ~300 frames:

| model | est. cost (300 frames) |
|-------|----------------------|
| gpt-5-nano | ~$0.10-0.30 |
| gpt-4.1-nano | ~$0.15-0.40 |
| gpt-4.1-mini | ~$0.50-1.50 |
| gpt-4o | ~$5-15 |

costs depend on image resolution and number of detected objects.

### batch API (for large jobs)

openai's batch API gives 50% off with 24-hour async processing. good for re-labeling large datasets where speed isn't critical. not currently integrated but could be added to the label skill.

## YOLO models (for training)

used in the train skill as the base model for transfer learning.

| model | size | mAP@50 (coco) | speed | use case |
|-------|------|---------------|-------|----------|
| **yolov8n.pt** | 3.2M params | 37.3 | fastest | **default** — quick iteration, small datasets |
| yolov8s.pt | 11.2M params | 44.9 | fast | better accuracy, still fast |
| yolov8m.pt | 25.9M params | 50.2 | medium | good balance for larger datasets |
| yolov8l.pt | 43.7M params | 52.9 | slow | high accuracy, needs GPU |
| yolov8x.pt | 68.2M params | 53.9 | slowest | maximum accuracy |

### how to change

```json
{
  "yolo_model": "yolov8s.pt"
}
```

### training config

| param | default | what it does |
|-------|---------|-------------|
| epochs | 50 | training iterations over the full dataset |
| train_split | 0.8 | 80% train / 20% validation |
| imgsz | 640 | image size for training (set in train skill) |

### when to use larger models

- **yolov8n** (default): <500 training images, quick experiments
- **yolov8s**: 500-2000 images, production use on fast hardware
- **yolov8m+**: 2000+ images, GPU available, accuracy is priority
