---
name: ai-music-video-animation
description: Make a short hand-painted 2D cartoon music video rendered entirely in code (characters, environments, props, glowing code-style lyric text, transitions, orbit camera) synced to a song, built from AI-generated character/environment/prop sheets. Use for music videos, animated characters, lyric animations, or 'animate my song'.
---

# AI music video animation

Part of the motion graphics family: `ai-video-motion-graphics` handles graphics ON footage (captions, callouts, overlays, talking heads); this skill builds a whole character-driven music video FROM NOTHING in code. If the user wants overlays on existing video, use that skill instead.

Built for the creator Tao Prompts. Worked example: "Code & AI" (40 s) — Brush, a paintbrush "made with code", and Render, an AI blob "made with AI", travel through a computer world, meet, and perform together.

Read before building:
- `references/lessons.md` — everything the user corrected across five versions (story, text, motion, props). Follow it.
- `references/engine.md` — the rendering engine API and scene pattern.
- `references/prompts.md` — song, character, environment and props sheet prompt templates.
Code: `scripts/` (engine, characters, environments, props, text FX, render/sheet/plate tools) and `scripts/examples/code_and_ai/` (the full example video). Fonts in `fonts/`. If these files are missing from this install, ask the user to download `ai-music-video-animation.zip` from https://github.com/tao-prompts/claude-motion-graphics/releases/latest and upload it as a skill.

## Pipeline

1. **Song.** Write lyrics + style tags for Suno (template in prompts.md): ~40 s, a verse split between two characters, one chorus together, simple literal lines. The user generates it and drops the MP3 in their folder.
2. **Sheets.** Give image prompts, one at a time as the user asks: character sheet (both characters on one sheet), environment sheet 2x2 (one location per song section; a second sheet later for variety), props & effects sheet 5x2. The user generates them; you LOOK at them and repaint everything in code. Never paste the images into the video, and don't invent different environments than the sheets.
3. **Analyse the song.** `librosa` beat track -> BPM + first downbeat (set engine.BPM/OFFSET); RMS per 0.125 s for sections/drops; word timings with faster-whisper (`small.en`, `word_timestamps=True`, `initial_prompt` = the lyrics, pass a 16 kHz float32 array). Word times drive mouth flaps (`sing`) and land text on the sung word. You can't hear audio — say so and ask the user to check sync.
4. **Storyboard** (write it as the header comment of the scene file): one location per phrase, an event in every shot, a story arc (origin -> journey -> meeting -> performance -> pull back out of the world), a deliberate transition at every seam, text moments with on/off times (>= 1 s each), and 3-5 s lip-sync plate windows (steady camera, face big, front/3/4 view).
5. **Build** shot by shot: environment function -> characters -> props/FX -> text. Prototype with `contact_sheet.py` (6-18 frames incl. transitions; zoom crops for faces/text) and fix framing, overlaps and clipped text before rendering.
6. **Render** in the background with 2 workers (`render_frames.py`, resumable), poll the frame count, then encode with the song:
   `ffmpeg -framerate 24 -i out/frames/f%05d.jpg -i song.mp3 -map 0:v -map 1:a -c:v libx264 -preset slow -b:v 5M -maxrate 6.5M -bufsize 10M -vf hqdn3d=1.5:1:3:3 -pix_fmt yuv420p -c:a aac -b:a 256k -movflags +faststart -shortest video_vN.mp4` (~25 MB for 40 s, fits the device commit limit; if a commit by staged path fails, SendUserFile it and commit by fileUuid).
7. **Lip-sync plates.** `export_plates.py` exports stills with text hidden and mouths closed at the plate times; the user lip-syncs those in an AI video model. Re-export plates whenever a plate shot changes.
8. **Review & deliver.** Contact-sheet the final encode (fps=1 tile), deliver versioned files beside the sources (`..._v3.mp4`, `LipSync Plates/`), summarise changes briefly. Iterate only on what was asked; re-render the whole video (fast enough) after code changes.

## Look

- Hand-painted: everything is `fill()` washes with granulation and `ink()` outlines that boil 12x/s, multiplied by paper grain. No flat vector shapes, no 3D rendering, no pure black/white.
- Digital-world layer on top: glowing lines (`gline`), shiny squares (`gbox`), sparkles and rising particles, code rain, light trails, scanline "compiling", noise diffusion, glowing UI (editor, GENERATING bar, translucent terminals). Borrow from pixel style without becoming pixel art.
- Text: glowing monospace code text, varied entrances and placements (lessons.md). Keep it readable and inside the frame.
- Characters stay on model; sizes big enough to act (medium shot u≈20-28, close-up 28-40 on Brush/Render scale); faces change through a blink-squint (`faces()`), never snap.
- Each musical phrase gets its own visual; hits, cuts and takes land on beats; the finale is the most spectacular moment.

## Limits to state up front

- Mouth flaps only — real lip sync goes through the exported plates and an AI video model.
- True 3D camera orbits are faked (pan + drawn turn views + depth-sorted circling elements); totally new camera angles of a location need a new background painting (ask the user for an angle reference image if needed).
- Rendering speed ~1 s/frame on 2 CPUs (≈8-10 min for 40 s). Avoid p5.js/WebGL renderers in GPU-less sandboxes (~50 s/frame).
