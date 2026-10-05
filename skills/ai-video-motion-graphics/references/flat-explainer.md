# Mode F - Flat 2.5D animated explainer: full notes

Hard-won rules from building a 41 s science explainer ("are we living in a simulation?") through five rounds of review, plus an earlier physics explainer that failed on clarity. Everything here is implemented in `scripts/flat25d_kit.py`; `scripts/examples/flat25d_example.py` shows a full scene + transition + render loop.

## 1. Script and story (do this before any drawing)
- ~40-45 s = ~105-115 words of VO. One visual idea per sentence; each idea gets 3-5 s on screen.
- Explain like it's for a smart 10-year-old: short sentences, concrete objects, no jargon. If the user says "simpler", remove a concept rather than rewording it ("time isn't the same for everyone" -> just say the consequence).
- Abstract logic (timelines, paradoxes, probabilities) needs ONE persistent visual that builds up step by step and stays on screen long enough to read. Too many cuts away from it = confusion (an FTL-paradox draft failed exactly this way). Prefer topics that map to concrete pictures.
- Give paste-ready blocks: the VO script in one code block (for ElevenLabs etc.), the shot plan in another.
- Pacing beats: when asked for "a beat" between lines, insert silence into the VO at the measured gap (RMS < peak-42 dB), then shift every later cue by the same amount. Typical beat: 0.7-0.8 s.

## 2. Look
- **Palette: rich, saturated, deep.** Not pastel. Mid-tone saturated colours (sky #0670D8 -> #13A2EE, grass #5FD22E, magenta #B0146E, violet #3A0C92, orange #FF5A10). Finish every frame with `post()` (saturation x1.14, light contrast, bloom on highlights, vignette, grain).
- **Vary the backgrounds per scene**: sunny street, warm lamp-lit room, dusk alien city, deep-navy lab, bright village, magenta nebula, red-orange "odds" stage. A video that stays purple-space for 40 s was rejected.
- **Depth from 2D layering, not a 3D engine.** Iso blocks rendered with lighting/gradients looked like "3D engine graphics" and were rejected. Use:
  - `shape()` = base colour + hard-edged shadow crescent (offset copy) + thin light rim, then a banded overlay and grain.
  - `band_fill()` = gradients made of 3-6 **solid colour segments** (2.5D), never a smooth ramp, on towers, cylinders, blocks, spheres, buildings, windows.
  - `sphere()` = concentric offset discs, lighter toward the light.
  - slight imperfection: `wcirc / woval / wblob / wpoly` wobble outlines a few %; nothing should be a perfect circle or box.
- **Rounded isometric**: `IsoR.block()` draws a rounded hexagon underlay (soft bevel seams) + banded faces + a top-edge highlight. All repeated objects share one design language (e.g. every simulated world is an `iso_island(biome)`; the special one is the same island in `'gold'` with rays), never mix a globe with cubes.
- More 3D forms than circles/rectangles: tapered towers with banded cylinder shading, domes, rings, cones, prisms, pyramids, saucers, pedestals.
- Detail density like a pro explainer: every scene has 3 depth layers (sky/far skyline, mid set, foreground props) plus ambient life (clouds drifting, taxis, walkers, twinkles, bokeh, sparkles).

## 3. Characters
- Humans: `person()` - flat cartoon, cel-shaded, expressions (calm/happy/surprised), look/up head turns, walk cycle. For holding props use **IK**: `hands_at=[(lx,ly),(rx,ry)]` in local coordinates (elbows bend down/out). Always check for duplicated limbs (a raised arm pose + separately drawn hands on a prop looked like four hands).
- The hero sits **centre frame, large**, and **interacts** with the environment (looks around, takes a photo with a flash, inspects with a magnifier). Put them next to a recognisable landmark when the story is "the real world" (Empire State Building, Statue of Liberty are in the kit: `esb()`, `liberty()`; landmark architecture is fine to draw, logos/characters are not).
- Non-human characters must read **mature**, not childlike: aliens with elongated craniums, almond eyes, bioluminescent dot markings, slim necks, armoured suits (`alien_profile`, `alien_back`, front head on turn). Make them **contrast** with the background (bright cyan/lavender/green skin + magenta/gold suits on deep navy). Childish round heads with big cute eyes were rejected.
- Show actions explicitly: when a character "programs", show a close-up of long-fingered hands tapping a glowing keyboard, then readable code on screen (`code_lines`) - syntax-coloured, typed out char by char.

## 4. Signature effects
- **Holograms**: `holo_island()` renders the object offscreen with `IsoRot` (true yaw rotation), tints it cyan, adds scanlines, flicker and an additive glow; place it over an emitter disc with a light cone, **away from screens** (a world popping up over the code screen looked wrong).
- **Reality glitch**: `wire_version()` (Canny edges + grid + binary on navy) composited through `block_mask()` cells whose coverage ramps up, plus `glitch_np()` slice shifts / RGB split / pixel blocks. Start local (one landmark) then spread over most of the screen.
- Neon screens inside scenes (Pong, monitors) must be the brightest, most saturated element so the eye goes there.
- Labels: pills and `text3d` (extruded) numbers; fade them before any camera dive so they don't hang over the transition.

## 5. Transitions: integrated, story-driven (no plain slides, zooms or whooshes)
Plan every boundary as a match or story moment, e.g.:
- glitching city -> code blocks -> resolve into the next scene's screen, camera pulls OUT of that screen;
- camera dives INTO a TV showing a sunset -> cross-match into the next scene's sunset sky;
- push into a glowing orb -> cyan flash -> hands at a keyboard lit cyan;
- pull back from a close-up (keyboard) to the wide shot;
- dive into a hologram -> the hologram becomes the real place as its cyan tint fades; reverse it to go back;
- an object flies from one scene into its place in the next (golden world -> balance scale) under a circle wipe with a gold ring;
- a word glitches into code blocks that resolve into the next location.
Implement scene-side camera moves with `cam()` inside the scene (sharp), and only use image-space `zoom_img` for very short blends.

## 6. Production workflow
1. Script -> VO from the user -> word timings (faster-whisper word_timestamps) -> beat table.
2. **Asset test sheet first** (characters, props, islands on one canvas) and get the look right before scenes.
3. Contact sheets of 12-18 test frames (incl. mid-transition frames) + zoomed crops of characters.
4. Full render with 2 background workers (~0.5-0.8 s/frame at 1080p); re-render only changed frame ranges when iterating.
5. Encode: `-c:v libx264 -preset medium -vf hqdn3d=1:1:2:2 -b:v 4.5M -maxrate 6.5M -bufsize 9M` -> ~23 MB for 41 s (grain makes CRF files huge).
6. Sound (sfx_kit): soft pad bed under VO, pops on label pops, chimes on reveals, glitch buzz bursts on glitches, sub boom on big words, typing ticks for coding, shutter double-click for photos, rising chirps on dives. Deliver an SFX stem; you cannot hear the mix.

## 7. Rejected along the way (don't repeat)
pastel palette; one-colour purple backgrounds; smooth "3D engine" gradients; perfect geometric shapes; cute/childlike aliens; hero small or static; static middle sections; globes mixed with cubes; holograms covering screens; four hands; glitch confined to one small area; generic slide/zoom transitions; captions over an already-labelled graphic; smiley-faced "light" (too childish for a mature science topic).
