# Yolodex Labeling Rules

This document defines the labeling rules, edge cases, and a small test clip suite to keep YOLO labels consistent and trainable. These rules are written for gameplay frames and apply regardless of the class list, with a concrete class definition set for the current defaults.

If you use a different class list, replace the "Class Definitions" section with your own while keeping the global rules and edge cases unchanged.

## Global Rules (All Classes)

- Label only visible, unoccluded pixels. Do not hallucinate hidden parts.
- Use one axis-aligned bounding box per object instance.
- Boxes must be tight. Do not include large background areas. A 1-2 px buffer is acceptable for safety.
- If an object is partially off-screen, clip the box to the visible portion.
- If an object is heavily occluded, label only if its identity is clear and at least 50% of the object is visible.
- Do not label reflections, shadows, glow effects, or UI icons that are not the actual in-world object.
- Do not label the same object twice.
- If you are uncertain about class identity, skip the object.
- Minimum size: skip boxes with width or height < 2 px. Prefer skipping objects < 4 px on their shortest side unless they are crucial to the class.
- Class names must match the provided class list exactly and are normalized to snake_case.

## Class Definitions (Default Class List)

These definitions correspond to the default class list in `labeler/defaults.py`:

- `player_jake`
  - Include: the playable character’s full body, including clothing and accessories.
  - Include: hoverboard or board-like items attached to the player (no separate class).
  - Exclude: shadow, motion trails, or UI avatar icons.
  - Occlusion: label visible body only if identity is clear.

- `train`
  - Include: the visible body of a train car.
  - Multiple cars: label each train as a single contiguous object if cars are connected with no visible gap.
  - Exclude: rails, station platforms, and background scenery.

- `barrier`
  - Include: in-lane obstacles that block or collide with the player (barricades, signs, blockades).
  - Exclude: trains, ramps, side scenery, and purely decorative items.
  - If barrier is attached to a train, treat it as part of the train unless it is clearly distinct.

- `coin`
  - Include: individual collectible coins.
  - One box per coin. Do not group multiple coins into a single box.
  - If coins overlap or are too small to separate reliably, skip those coins.

- `powerup`
  - Include: collectible powerups (e.g., magnet, jetpack, score multiplier).
  - Exclude: coins, UI indicators, and purely visual effects after pickup.

## Edge Cases

- Motion blur: label if the object’s identity is clear; box should cover the blurred silhouette.
- Cutscenes, menus, or non-gameplay overlays: do not label any objects.
- UI/HUD: ignore entirely unless there is a class dedicated to UI elements.
- Heavy particle effects (explosions, dust): ignore unless they are the object itself.
- Duplicates in consecutive frames: label each frame independently; do not rely on previous labels.
- Overlaps: if two objects overlap (e.g., player in front of a train), label both with their own boxes.

## Test Clip Suite (Small, Targeted)

Create a small suite of short clips (5-10 seconds each) that cover all classes and edge cases. Each clip should be from a different source video to reduce bias. Sample at 2 fps for quick review (10-20 frames per clip).

Recommended suite for the default class list:

- Clip 01: Baseline run, clear lighting, player + coins + 1 train
- Clip 02: Dense coins, multiple coin rows, player centered
- Clip 03: Multiple trains in different lanes, partial occlusion of player
- Clip 04: Barriers only, no trains, varied barrier sizes
- Clip 05: Powerup pickups, powerup in motion blur
- Clip 06: Partial off-screen objects at frame edges
- Clip 07: Heavy visual effects (sparks/dust), verify ignore rules
- Clip 08: UI-heavy moment or pause screen, verify no labels

For alternate class lists:

- Replace the class coverage in each clip to ensure every class appears in at least two clips.
- Include at least one clip with heavy occlusion and one with motion blur.
