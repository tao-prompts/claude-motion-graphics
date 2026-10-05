# AI Music Video Animation - a Claude skill

Make a short hand-painted 2D cartoon music video, rendered entirely in code and synced to your song. Characters, environments, props, glowing code-style lyrics and camera moves are all drawn by Claude. Created by **Tao Prompts**.

Sibling of `ai-video-motion-graphics`: that skill puts graphics on your footage; this one builds a whole animated music video from nothing.

## How it works
1. Claude writes the lyrics and style tags; you generate the song (e.g. in Suno) and add the MP3.
2. Claude writes image prompts for a character sheet, environment sheet and props sheet; you generate them and add the images.
3. Claude repaints everything in code, syncs it to the beat and the sung words, and renders the video.
4. Optional: Claude exports lip-sync stills you can animate in an AI video model.

## Contents
- `SKILL.md` - the instructions Claude follows.
- `references/` - lessons, engine API, prompt templates.
- `scripts/` - engine, characters, environments, props, text effects, render tools, and the full "Code & AI" example.
- `fonts/` - Space Mono, Luckiest Guy, Permanent Marker (see `fonts/LICENSES.md`).
