# Prompt templates (fill in the [brackets])

All image prompts target GPT Image (or similar). Always attach the earlier sheets as references so style stays consistent, and keep designs simple enough to repaint in code: flat shapes, dot eyes, thick wobbly ink outlines, watercolour washes, paper grain, no 3D, no text.

## 1. Song (Suno / any music generator)
Keep it ~40 s: [Intro] 4-5 s, one [Verse] split between the two characters (male/female vocal tags), one [Chorus] together, short [Outro] + [End]. Plain, literal lyrics read better than clever ones ("I'm made with code, line by line" beat a metaphor-heavy first draft).
Style box example: `upbeat electro-pop duet, male and female vocals trading lines, 120 BPM, chiptune synth arps, glitchy vocal chops, hand claps, funky bass, playful cartoon energy, catchy singalong hook, short song`
Suno often overruns: generate a few takes, crop to length.

## 2. Character sheet (both characters on ONE sheet = shared scale + style)
```
DESIGN SHEET PROMPT — "[Title]"
A professional 2D animation model sheet for a short cartoon music video, showing two characters who [relationship]. Clean organized grid on warm cream watercolor paper.
LAYOUT
- Top row: full-body turnarounds of both characters side by side at correct relative scale — front, 3/4 front, side profile, 3/4 back, back. Thin pencil height-guide lines.
- Second row: expression grid, 6 faces per character — happy, surprised, angry, scared, smug, love-struck.
- Third row: 4 interaction poses — [pose 1]; [pose 2]; [pose 3]; [pose 4].
- Bottom row: palette swatches per character, 3 small props, a simple backdrop.
CHARACTERS (must remain visually consistent across all panels)
1. [NAME] — [simple shape-based description, colours, face, limbs, personality]
2. [NAME] — [...]
TONE
[one line]
DESIGN RULES
Simple bold graphic shapes, flat 2D only, no 3D rendering or realistic shading, thick hand-inked black outlines with slight wobble, flat watercolor washes with visible brush texture, soft muted palette, no pure black or pure white, very few labels and no extra text.
STYLE
hand-painted 2D cartoon model sheet, p5.brush watercolor look, ink linework, flat colors, paper grain texture, indie animation studio style, clean minimalist layout, organized grid composition
```

## 3. Environment sheet (2x2, one location per song section; do a second sheet for variety)
```
ENVIRONMENT SHEET PROMPT — "[Title]"
A 2x2 grid of four background environment paintings for a short 2D cartoon music video, panels separated by thin pencil borders on warm cream watercolor paper. Each panel is a wide 16:9 background plate with NO characters in it, leaving a clear open floor area in the lower-middle third where two small cartoon characters will later perform. Use the uploaded character sheet as the reference for art style, linework, paper texture and palette.
PANEL 1 (top left) — [LOCATION]: [3-4 concrete visual elements, palette]
PANEL 2 (top right) — ...
PANEL 3 (bottom left) — ...
PANEL 4 (bottom right) — ...
DESIGN RULES
Flat 2D only, no 3D rendering, simple bold shapes built from a few clear layers (background, midground, floor), thick hand-inked wobbly outlines, flat watercolor washes with visible brush texture and paper grain, glows painted as soft light washes, no pure black or pure white, no text, no letters, no logos, no characters.
STYLE
hand-painted 2D cartoon background plates, p5.brush watercolor look, ink linework, flat layered scenery, indie animation studio style, storybook illustration, organized 2x2 grid composition
```
Good variety set for a "digital world" story: a real-world start (desk at night), a paper/blueprint world, an AI dream world, a stage; then dark/neon ones: GPU city, a winding data highway, a neural-network garden, a video-editing timeline studio.

## 4. Props & effects sheet (5x2)
```
PROPS & EFFECTS SHEET PROMPT — "[Title]"
A 2D animation prop and effects model sheet for a hand-painted cartoon music video set in [world]. 5x2 grid of 10 separate items, each centred in its own cell with generous empty space, on warm cream watercolor paper, thin pencil borders. Use the uploaded character and environment sheets as the reference for art style, linework, paper texture and palette.
PROPS
1-7. [name]: [one-line visual]   (vehicles/rides, power-ups, portals, containers, story objects)
EFFECTS (drawn as stylized painted effects, frozen at a key moment)
8-10. [ink splash burst / pixel firework / light ribbon trail ...]
DESIGN RULES / STYLE  — as above, plus: Palette: [list]. No characters, no text.
```
Pick rides that match the characters' nature (a code character rides a code block, an AI blob rides a halo disc) — the user rejected a paint palette hoverboard and a mouse-cursor ship as "not making sense" for these characters.
