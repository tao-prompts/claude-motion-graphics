---
name: "ai-video-motion-graphics"
description: "Code-driven motion graphics, explainer animations and sound design for AI video, talking heads and vertical shorts, rendered frame-by-frame in Python/OpenCV/PIL + ffmpeg, with switchable style modes (tutorial cinematic, vertical documentary explainer, AI-film overlays, pure code animation, flat 2.5D animated explainer, 3D voxel scale-zoom). Use for captions, callouts, split screens, counters, charts, AR UI, tracked graphics, pause trimming, SFX, 2D explainer animations, 3D voxel / Powers-of-Ten zooms, or 'animate this'."
---

# AI video motion graphics

Claude writes Python that renders every frame: source footage + tracked/timed graphics -> JPG frames -> ffmpeg encode with a mixed audio track. Created by Tao Prompts (AI-video education on YouTube) and written to be shared: the house defaults in each mode are starting points, and any user can switch modes or override a palette at any time. The **shared workflow** applies to every job; the look, layouts and sound come from a **mode**.

Read `references/sandbox-notes.md` before running long renders. Mode A's hard-won feedback lives in `references/style-rules.md`; pull techniques from `references/techniques.md` as needed. `scripts/examples/intro_render_example.py` is a complete, approved 22 s Mode A intro (talking head -> AR UI -> asset board -> 4-step process) to copy from.

**Motion graphics family:** this skill puts graphics on or around footage. For a character-driven **music video** built entirely in code (song -> character/environment/prop sheets -> painted characters that turn, emote and dance, 8 environments, props, glowing code-style lyric text, orbit camera, lip-sync plates), hand off to the sibling skill **`ai-music-video-animation`** (Mode E below). The two share the same sandbox habits (2 background workers, contact sheets before full renders, versioned delivery beside the sources).

## 0. Setup (automatic, first run on any machine)

**Before the first render in a session, run `python <skill>/scripts/setup_env.py` yourself - never ask the user to install anything.** It is idempotent and only does what is missing:
- pip-installs numpy, opencv-python-headless, scipy, pillow, skia-python, faster-whisper (retries with `--user` / `--break-system-packages`);
- makes the **Poppins** fonts available in `<skill>/assets/fonts/` (bundled with their SIL Open Font License; if missing it copies an installed copy or downloads them from the official Google Fonts repo). `mg_kit` and `flat25d_kit` load fonts from that folder first, then system fonts, then DejaVu;
- checks ffmpeg and prints the one-line install command for the user's OS if it is absent (winget / brew / apt) - offer to run it.
Word timings additionally need the faster-whisper model download (Hugging Face) or a user-supplied SRT. Nothing in this skill calls a paid API; all graphics and sound are synthesised in code.

## 1. Pick a mode first

Decide from the user's words, the aspect ratio and any reference video, and state the chosen mode in one line before building. The user can switch at any time ("use the documentary style", "switch to Mode B") - when they do, swap palette, type, layouts and sound together and keep the shared workflow.

| Mode | Use when | Signature |
|---|---|---|
| **A. Tutorial cinematic** | 16:9 YouTube tutorials, intros, process explainers over a talking head or AI clips | dark grid, green accent, Poppins, glass AR UI, step lists |
| **B. Vertical documentary explainer** | 9:16 shorts/reels about news, money, history; reference looks like Vox / Johnny Harris / Economist shorts | charcoal + paper textures, B&W assets, ONE red accent, serif numbers, split screens, varied reveals, tactile foley |
| **C. AI-film overlays** | graphics living inside AI-generated scenes (Seedance, Artlist...) | tracked billboards, chalk illustrations, particle reveals, before/after |
| **D. Pure code animation** | animate an illustration or build a scene with no footage and no AI video tool | procedural painted layers + cut-out character with breathing, blinks, hair sway |
| **F. Flat 2.5D animated explainer** | a fully animated science/idea explainer with no footage (40-90 s, VO-driven), bright flat-vector look with characters, isometric worlds, holograms | rich saturated palettes that change per scene, cel-shaded 2D shapes with banded (segmented) gradients, rounded isometric blocks, mature characters, story-driven match-cut transitions; toolkit `scripts/flat25d_kit.py` |
| **G. 3D voxel scale-zoom** | a fully 3D stylised journey through scales or worlds with no footage ("Powers of Ten", galaxy -> atom, any continuous zoom story), 20-40 s | every level built from matte, vivid clay-like cubes (Genshin-bright, not neon), blocks scatter/assemble at transitions, continuous log zoom with smooth acceleration, scale counter + ruler, 8-bit + ambient SFX; Three.js rendered headless frame by frame |
| **E. Character music video** | an animated cartoon music video or lyric video with characters, synced to a song, no footage | use the **`ai-music-video-animation`** skill: parametric painted characters, environment/prop sheets repainted in code, glowing code-style lyrics |

If a reference video is given, its style beats the mode defaults - analyse it (workflow step 2) and note the differences.

**Switching modes (for anyone using this skill):** say "use Mode B", "switch to the documentary style", "make it a flat 2.5D explainer" etc. Claude then swaps palette, type, layouts, transitions and sound together and keeps the shared workflow. Modes can also be mixed on purpose (e.g. Mode F scenes cut into a Mode A talking-head intro) - state which mode each section uses in the beat table. Personal house rules (colours, fonts, banned effects) can be added by the user in their own copy under the relevant mode.

## 2. Shared workflow (all modes)

1. **Inventory everything first.** `ffprobe` every file (size, fps, duration, audio). Build a contact sheet of each clip and the reference (6-40 thumbnails) and actually look at it. Read any instructions PDF in the folder. For talking heads, check full-screen vs picture-in-picture (`scripts/find_pip.py`) and **scan for internal jump cuts** (`scripts/find_jump_cuts.py`) - section cuts must land on the frame before one. Users sometimes drop a regraded or regenerated version of the footage (e.g. a desaturated avatar with different framing): check sync by comparing audio, then use theirs.
2. **Analyse any reference video**: transcript + words per minute, beat structure, how text appears (size, font class, position), backgrounds, colour accents, transition style, and the sound (spectrogram: steady low band = music/drone bed; rapid HF clicks = counter ticks; broadband bursts = hits/transitions). Also make 5 fps filmstrips of 3-4 graphic sections to see HOW things move (how circles draw, how numbers roll, how maps fill, how the camera moves over images) - static thumbnails hide the animation.
3. **Get word timings.** `scripts/word_srt.sh` (whisper.cpp; needs `huggingface.co` + `*.hf.co` allowlisted), the user's SRT, or `pip install faster-whisper` and pass a float32 16 kHz numpy array (passing a file path can crash in PyAV with `metadata_errors`); `word_timestamps=True`, `initial_prompt` with product names. Parse SRTs with `scripts/srt_words.py`. Fallback: waveform + spectrogram (see techniques).
4. **If the user sends a draft/mock-up or a drawn outline, measure it before designing.** `scripts/match_frames.py` recovers source shots/times from a draft; a hand-drawn perspective outline is mapped exactly with `canvas_quad_from_outline`. Keep the user's structure and timing unless asked.
5. **Trim pauses (talking heads / AI avatars) when asked.** Cut on **audio level, not transcript gaps** - whisper folds words into tokens ("$555 billion" swallows "dollars"), and gap-based cutting deletes them. Recipe: RMS over 25 ms; silence = below (peak - 42 dB) for > 0.42 s; keep 0.10 s before speech and 0.14 s after; snap to frames; 20 ms audio fades. Remap word times through the segment list and deliver an SRT of the edited timeline.
6. **Hide or soften cuts.** Put most cuts under graphic scenes. On camera use a 4-frame crossfade built from REAL frames on both sides of the cut (continue past the cut point in the source). No zoom punch-ins (rejected as not smooth).
7. **Map beats to words.** Write a beat table: word/time -> what appears. Graphics land on the spoken word (rise-in ~0.05 s early). Scene boundaries only inside pauses, never mid-word or mid-caption. Plan where the person/PiP is and keep graphics clear of it (or behind it with a clean matte). Drop captions wherever the on-screen graphic already says the same thing (e.g. no "$555 billion" caption under a $555B counter) - redundant text was called out.
8. **Plan the transitions as a list** (see "Transitions" below) before rendering - every boundary gets a deliberate choice, and no effect repeats back to back.
9. **Prototype with 6-18 test frames** (`render(i)` -> contact sheet) including mid-transition frames, plus zoom crops of small detail (logos, eye bars, edges). Fix issues before the full render.
10. **Render full frames in the background** (2 workers, `setsid nohup ... &`, poll the frame count; `scripts/render_template.py`). Keep previous versions' frame folders only until encoded (disk fills fast). Never `pkill -f` a pattern that also matches your own shell command, and don't chain `grep` into `&&` (no match = exit 1 stops the chain).
11. **Sound** per mode (section 3). Voice always dominant. Always export an SFX-only stem, and say you can't hear audio.
12. **Encode, review, deliver.** Film grain makes CRF files huge (~150 MB for 40 s); for delivery use `-vf hqdn3d=2:1:3:3 -b:v 3.6M -maxrate 4.8M -bufsize 8M` (~20 MB, fits the device-commit limit). Contact-sheet the final encode, deliver versioned files (`..._v3.mp4`, `..._SFX_stem_v3.wav`) beside the sources, summarise changes briefly.

When iterating on feedback: change only what was asked; keep previously-approved elements unless told otherwise ("don't get rid of all the motion graphics" - e.g. a liked line chart stays); re-render only affected frame ranges when possible; re-time audio events if timing moved; apply every point in a round before re-rendering (users often add notes mid-render). When the user says "go back", point to the earlier version and revert the working code too. When patching code with string replacement, match what is literally in the file (a real `−`/`·` character vs a `−` escape).

### Transitions (all modes)

- **Never use the same transition effect three, four, five times in a row** - not even twice back to back. A uniform zoom/fly-through on every cut was rejected as repetitive; a blur dissolve everywhere feels the same way.
- Mix **hard cuts** (the default in documentary shorts) with a few **content-motivated reveals**, each used once:
  - **iris / match cut** - a circle already on screen (a counter circle) opens up to reveal the next scene;
  - **sheet drop** - the next paper scene drops down from the top over the old one;
  - **page push** - the next scene scrolls up and pushes the old one out (shadow at the seam);
  - **line wipe** - a thin red line (continuing a red chart line) sweeps across, new scene behind it, soft red glow;
  - **panel expand** - a split-screen panel keeps growing until it covers the frame, its content fades, then the next full-screen scene;
  - **fill-the-frame** - an element (e.g. a white valuation circle) keeps growing until the frame is that colour, then the next scene fades up from it.
- Transition windows start at the boundary and the outgoing scene keeps animating underneath, so scene functions must render sensibly a little past their end.
- Give each transition its own sound (or none for hard cuts): don't put the same page-flip on every boundary.

## 3. Modes in detail

### Mode A - Tutorial cinematic (16:9)

House style (details in `references/style-rules.md`):
- Clean, contemporary, "YouTuber cinematic". No neon/purple tech glow, no clip-art.
- **Palette**: dark grid background (`#0F1218`-ish, `assets/dark_grid.jpg`), white text, saturated green `#01FE81`, sky blue `#368AD6` secondary, deeper green `#16A860` for audio/checks. Never red; no pastels. (Older default white/ink/clay `#D97757` - only if the user hasn't moved on.)
- **Fonts**: Poppins Bold/Medium for UI and titles; bold italic serif (TeX Gyre Termes Bold Italic) for "cursive" accent words - large and bold, not thin Lora Italic.
- **Readable at a glance**: over footage, white with strong soft shadow and the background (not the person) darkened ~25%; coloured words on grids get a tight crisp shadow. Big sizes (56-72 px captions, ~100 px accent words, 270 px hero words). Near eye level; consecutive captions at the same height.
- **On dark backgrounds** every image/video/card gets a thin white border + faint white glow (`place_card`).
- **Floating UI**: dark translucent glass, white text, behind the person (matte), perspective per the user's reference/drawing (side nearest the person recedes; lay the panel out wide ~1.9:1), staged one step at a time (references first -> compact centred strip -> prompt types). @tags = coloured text, no boxes. Never show credits/costs.
- **Generated video moments**: `loading_card` (progress bar + top-down load), not noisy dissolves.
- **Process/step explainers**: big step list on the left with a sliding highlight + filling connector + checks; stage on the right with a big "STEP N Name" title that swaps cleanly. Use "Post-production", not "Video editing". Only specific, real content in timeline graphics.
- Footage plays in real time and sharp - never frame-blended slow motion; hold a sharp frame for a pause. Section cuts avoid source jump cuts; soften with a 0.2 s zoom-blur blend (vary it if there are many section cuts).
- **Less is more**: 2-3 callouts max, one idea at a time, fade before action beats. Status/pipeline indicators sit right under a video card, large, with arrows on the active step.
- Never draw brand logos - composite the official file (premultiplied `RGBa` resize).
- **Sound**: `pop`, `swell`, `glass`, ticks, chimes; **no whooshes**; shot-audio beds only where wanted.

Section patterns:
- **Talking-head intro**: hero word behind the head via person matte (letter rise with overshoot), bold-italic accent words beside the head, background darkened, slow push-in; cut before any source jump cut. Variant: result screens behind the head as a curved wall (particle materialise), captions curved with them; logo lockup in front of/behind the head as asked.
- **AR interface beside the speaker**: glass panel warped to the drawn outline, behind the person; reference images fly from the laptop into slots; staged morph to a compact strip; prompt types with coloured @tags; Generate click with ripple.
- **Asset board -> generated video**: assets generate one by one with labels, rise to a top row, curved accent arrows point down into a `loading_card` video; caption under it.
- **Process explainer**: left step list with sliding highlight; right stage per step (idea card typing -> assets generating -> assets merge into loading video -> video shrinks into a preview above an editing timeline of real clips + audio).
- **Process explainer with a single video**: rounded video card + PiP; big step pipeline under the card; analysis phase on a held sharp frame; 3D exploded layer stack that collapses into the finished render.

### Mode B - Vertical documentary explainer (9:16, 1080x1920)

**Script (if asked to write one):** analyse the reference transcript (typically ~135 wpm; ~75-80 words = 30 s). Structure: concrete hook (date + jaw-dropping number) -> tangible comparison ("twice the entire economy of Russia") -> specific cause chain (what actually happened) -> the parallel today with a named company and numbers -> short ironic close. Research and verify every figure with web search, cite sources, and flag numbers that mislead (e.g. a headline net loss that is mostly a non-cash accounting charge vs the operating loss; people's current titles). When the user wants text for ElevenLabs, give only the paste-ready VO.

**Look:**
- Backgrounds: charcoal `~#222` and paper `~#ECEBE7`, each with fine grain + subtle low-frequency mottling + vignette. Full-frame B&W photo plates (trading floor, empty office, data center) darkened to 30-45% behind text, or blurred down to ~18% when foreground objects must stand out.
- Colour: black / white / grey + ONE accent red `#C8181F` (loss, warning, emphasis). Signs and colours must match meaning - spending/outflow is `-$500B+` in red with money visibly draining, never a growing white number.
- Type: high-contrast serif (TeX Gyre Termes) for numbers, dates, headlines and the end line; Inter Medium/SemiBold for labels and titles; single-word serif captions (~96 px, white, soft shadow) at chest height on camera. Keep type clean - AI-generated stylised "paper clipping" text was tried and rejected.
- Assets: B&W engraving/halftone cut-outs with occasional red. Ask the user to generate an asset sheet, e.g.:
  > A 4x3 asset sheet of 12 separate editorial illustrations, each centred in its own cell with generous empty space, on a pure flat white background. High-contrast black-and-white photo-illustration with fine engraving/halftone texture (WSJ hedcut x Bloomberg Businessweek collage). Monochrome except a small deep crimson (#C8181F) accent where noted. Crisp cut-out silhouettes, no shadows, frames, text, logos or watermarks. 1. ... 12. ...

  plus separate 9:16 full-bleed B&W background plates. Cut out: flood-fill near-white (min channel > 228, low saturation) from the border, open 3x3, keep only connected components whose centre lies inside the main blob's bbox (drops stray bits from neighbouring cells), crop to bbox.
- Logos: official files only, premultiplied-alpha resize, on white rounded cards with padding. Real people: real press photos (never AI likenesses), B&W, rounded card with a thin white border; a red bar across the eyes is an accepted editorial device. Label people with their correct current role.

**Layouts that worked:**
- **Split-screen push**: a panel slides down from the top (0.6 s ease) to 960 px and pushes the talking head down ~700 px so the face sits in the bottom half; thin light seam + shadow. Captions (when not redundant) sit just under the seam (y ~1015). The panel can keep growing past 960 px to hand over into a full-screen scene.
- **Full-screen asset scenes**, one idea each: a drawn red line chart with start/end labels (liked), big-number counters, country silhouette x2 = company comparison, scale-true circles (area ratio) for valuations, names struck through in red, a faucet dropping its last coin, burning money, a money stack draining into AI chips.
- **On-camera explainer card**: ONE centred dark rounded card (lower half) that reads like a sentence - [A] -red arrow "buy"-> [B], with the qualifier ("with BORROWED money") under the arrow. Do not pop separate things on the left and right of the head - viewers can't tell how they relate.
- **Around the head**: only in clear zones (corners, chest height), in front of the person. Don't put graphics behind the head unless the matte is clean - GrabCut on dark hair against a dark room leaves a ragged edge. Don't download ML matting models without asking.
- End on a settled frame: the closing line in serif with the key word in red italic.

**Subtle interactivity (from the reference - small, constant life in every graphic, never busy):**
- **Circle counters** draw as a clockwise radial sweep from 12 o'clock (`cv2.ellipse` with an end angle), and the number inside only appears once the sweep is ~80% done; a pie wedge can sweep in afterwards for a percentage.
- **Rolling counters**: digits get a vertical motion blur proportional to roll speed (box kernel ~3x the per-frame change, fading to sharp as the number settles).
- **Red ink spreading** inside a silhouette (map, logo, object): noise-perturbed distance field from a seed point, clipped to the sprite's alpha, growing to ~35% of the width - organic partial coverage, not a full fill.
- **Line charts**: the red line draws on, a faint red gradient fills the area under it, and the leading dot pulses gently once drawn.
- **Photos**: slow push-in (Ken Burns, ~7-8% over 3 s) inside their rounded cards.
- Small physical touches: an hourglass rocking a degree or two as it lands, embers floating up off burning money, a cloud drifting sideways, bills flying from a draining stack into a destination.

**Motion & timing**: reveals 0.5 s (blur-in + rise), pops 0.6 s with slight overshoot, panel slides 0.6 s, transitions per the Transitions list (hard cuts plus a few motivated reveals, ~0.35-0.5 s each). Every text/graphic stays readable for >= 1-1.5 s before the scene changes - move a boundary to the next pause if needed; nothing should flash and vanish.

**Depth (keep subtle)**: three layers - background plate pushes in ~1.2%/s, objects drift up ~12 px/s (5 px/s inside split panels), text stays still. Dark scenes get slow dust motes in 3 depths (near = bigger/brighter/faster). Soft bloom behind hero numbers: gaussian ellipse with amplitude ~0.07 (white) or ~0.3 (red) as a fraction of 255 - larger values blow out.

**Sound**: a dark documentary drone under the whole VO (sines at 55/82.4/110/165/220 Hz with slow tremolo + 300-1600 Hz filtered air, ~-20 dB under the voice, fading in/out) plus **tactile synthesised foley**, never whooshes (rejected twice as generic):
- page flip for page-like moves (scroll/push, paper sheets): band-passed noise 0.9-7.5 kHz with fast flutter AM + a short snap at the end - not on every scene change;
- paper rip on losses: accelerating train of 2-8 ms band-passed noise grains (1.2-9.5 kHz) + a low tear body;
- pen scratch for drawn lines, circle sweeps and strike-throughs: 2.2-7 kHz noise with ~6-14 Hz stroke modulation; marker stroke for arrows, eye bars and line wipes;
- coin hit: inharmonic ring (3.1 kHz x 1, 2.76, 5.4, 8.9) with bounces at +0.17/+0.29/+0.37 s and a short roll; water drip = fast rising sine chirp;
- bill flutter = several quiet page flicks; stamp = 95 Hz thump + paper slap; metal clunk = 120 Hz + 820/1370 Hz partials; sand trickle; typewriter taps; quiet crowd murmur under a trading-floor plate; ink spread = soft 150-900 Hz swell;
- counter ticks that slow as the number settles; sub boom (62 -> 32 Hz sweep) on the biggest numbers; camera shutter (two clicks) on photo cards; low `swell` for iris / panel-expand transitions.

**Pitfalls**: pad an RGBA layer before blurring its alpha for a drop shadow (otherwise the shadow gets hard square edges that look like a dirty crop); compositing helpers must clip to the destination canvas size (split panels are 1080x960, not full frame).

### Mode C - AI-film overlays
- **World-anchored graphics**: track camera (ground homography chain) and objects (LK with forward-backward check); billboard text/illustrations anchored in 3D; hide tethers/labels when tracking is invalid; prefer screen-space text if tracking makes it hard to read.
- Chalk illustrations from a generated sprite sheet (alpha from luminance), noise/edge draw-on reveals, particle materialise/dissolve, curved screen walls, 3D layer stacks.
- **Before/after**: slider over original vs graphics versions; glide in, crawl slowly through the middle, accelerate out.
- Keep shots real-time and sharp; hold a frozen sharp frame for analysis moments; 2-3 callouts max. Palette/type follow Mode A unless the user says otherwise.
- Details: `references/techniques.md`, `scripts/mg_kit.py`.

### Mode D - Pure code animation (no footage, no AI video tool)
- Character from a flat illustration: cut out with a border flood-fill on near-white; keep its contact shadow as a multiply layer.
- Painted environment in the illustration's palette: sky gradient + paper noise; cumulus clouds shaded by "mass above" (blurred mask shifted down) rather than a hard horizontal line; noise-curve hill layers with slope shading; meadow with flowers; swaying grass blades drawn at 2x and downsampled; simple line-art props (e.g. windmills with rotating lattice sails); drifting petals. Keep the palette muted to match the character.
- Life without redrawing: breathing (small vertical remap anchored at the base), hair sway (horizontal displacement fading out below the hairline), blinks (paint the lid with skin colour from the rows just below each eye + a dark lid line; 4 frames half/closed/closed/half), parallax camera pan + slow push, light grain and vignette.
- Be upfront about the limit: a cut-out illustration can't be re-posed (turn, stand, talk) - that needs image-to-video (Seedance/Kling through a connected tool), OR redrawing the character as a parametric painted character, which is what the `ai-music-video-animation` skill does (turns, expressions, walks, dances).

### Mode E - Character music video
Hand off to the **`ai-music-video-animation`** skill. It covers the whole pipeline: Suno lyrics/style prompt -> character, environment and props sheet prompts -> repainting the sheets in code (skia: boiling ink + watercolour + paper grain) -> beat/word analysis -> storyboard -> render with transitions, digital particle FX, glowing code-style lyric text and orbit camera -> lip-sync plate stills for an AI video model. Its glowing code text (`fxtext.code_text`) and digital FX (`envs2.gline`/`gbox`/`particles`) can also be borrowed for Mode C/D jobs.

### Mode F - Flat 2.5D animated explainer (no footage)
Full notes, rejected looks and the review history: `references/flat-explainer.md`. Toolkit: `scripts/flat25d_kit.py` (one file, skia-python); worked example: `scripts/examples/flat25d_example.py`.

**Script first.** ~105-115 words for 40-45 s; one concrete visual idea per sentence, 3-5 s each; explain like it is for a smart 10-year-old. Abstract logic (timelines, paradoxes, odds) needs one persistent visual that builds step by step - too many cut-aways made an earlier explainer impossible to follow. Hand the user paste-ready code blocks (VO script, shot plan). Insert requested "beats" as real silence in the VO at a measured gap and shift later cues.

**Look:**
- Rich, deep, saturated colour - never pastel - and a **different background world per scene** (sunny street, warm room, dusk city, navy lab, bright village, magenta nebula, red-orange stage). `post()` adds saturation, bloom, vignette and grain to every frame.
- Depth from layered **2D** shapes, not 3D-engine lighting: `shape()` (base + hard shadow crescent + light rim + texture), `band_fill()` gradients made of **solid colour segments**, `sphere()` concentric discs. Slightly imperfect outlines (`wcirc`, `wpoly`) - nothing perfectly round or square.
- Rounded isometric (`IsoR`, `iso_island(biome)`) with bevel highlights; all repeated objects share one design (every world an island, the special one gold).
- Varied 3D-feeling forms: tapered banded towers, domes, rings, pyramids, saucers, pedestals, landmarks (`esb`, `liberty`).

**Characters and action:** hero large and centred, interacting (looking around, photographing, inspecting); IK arms for props (`person(..., hands_at=...)`) and a check for duplicate limbs. Non-humans mature, not cute (`alien_profile`, `alien_back` with a front-face turn) and high-contrast against the background. Show actions literally: hands typing on a glowing keyboard, readable syntax-coloured code (`code_lines`).

**Effects:** rotating cyan holograms (`holo_island`, rendered offscreen with `IsoRot`, scanlines, flicker, emitter + light cone, away from screens); reality glitches that start local and spread (`wire_version` + `block_mask` + `glitch_np`); in-scene screens as the brightest neon element.

**Transitions:** every boundary is story-driven - glitch blocks resolving into the next screen, camera dives into a TV/orb/hologram and out of the next scene, an object flying from one scene into its place in the next under a circle wipe, pull-backs from close-ups. No plain slides, zooms or whooshes; fade labels out before a dive.

**Workflow:** asset test sheet -> 12-18-frame contact sheet with zoomed character crops -> full render (2 workers, ~0.5-0.8 s/frame) -> re-render only changed ranges -> encode with a bitrate cap (`-b:v 4.5M -maxrate 6.5M`, ~23 MB per 40 s). Sound: soft pad bed, pops/chimes on reveals, glitch bursts, sub booms, typing ticks, shutter clicks, rising chirps on dives; always ship an SFX stem.


### Mode G - 3D voxel scale-zoom (Three.js, no footage)
A camera dives continuously through nested worlds (galaxy -> solar system -> Earth -> tree -> grasshopper -> cells -> DNA -> atom -> nucleus/quarks -> strings -> quantum foam), each world built from cubes. Approved result: 35 s, 11 levels. The engine core is in the appendix at the end of this file; the full project (11 level builders, timeline page, renderer, synth SFX) was shipped to the user as `Voxel_PowersOfTen_project.zip` - ask for it if you need to copy a level.

**Pipeline:** Three.js page (`index.html` + level modules) served on localhost -> Playwright + headless Chromium (`--use-angle=swiftshader --enable-unsafe-swiftshader`), `window.renderAt(t)` then `page.screenshot` per frame (1920x1080, 30 fps, ~2 s/frame on CPU) -> ffmpeg with the synth SFX. Each level builder returns `{sc, cam, update(t), bloom:[strength,radius,threshold], exp}`; the timeline table `LV = [name, start, lead, exponent, label, sublabel]` drives everything, and each builder receives `(env, lead, D)` where `D` is its local time at the outgoing boundary. Post: EffectComposer with a two-render-target mix pass (crossfade + light zoom blur, assign `tA/tB` AFTER constructing the ShaderPass - uniform cloning nulls textures), UnrealBloom, OutputPass, then CA/vignette/grain; per-level exposure via `renderer.toneMappingExposure` (OutputPass applies it).

**Voxel engine (`Vox`):** one InstancedBufferGeometry box per object with per-instance `iPos, iScl, iCol, iGlow, iRnd`; all animation in the vertex shader: `uAsm` (staggered assemble from a random scatter), `uOut` (blocks fly radially outward from the dive target `uCenter`, tumbling, past the camera), a travelling pulse wave, and a column mode for wave-field terrain. Shapes: `voxSDF` (voxelise an SDF, keep only surface cells - capsules/ellipsoids/spheres + noise for trees, insects), lattice sphere shells for planets/cells/nucleons, heightfield columns for terrain, `chain` for thin legs/antennae/orbits. Mark the dive-target cube with stagger `.99` so it assembles last and leaves last.

**Look (user feedback, in order):**
- Blocks are the bulk of the image; glow and neon are accents only (thin rings, fresnel orbs, wire cores, sparks). All-neon/shiny looked wrong.
- Matte clay shading: hemisphere ambient + wrapped sun + per-face tones (top 1.0, sides .78-.86, bottom .62) + bevel-darkened edges + faint grain; emission only where `iGlow > 1` (city lights, sun, quarks, a highlighted target block).
- But colours stay **vivid and bright** ("Genshin Impact" saturation): saturated palettes, bright gradient backgrounds per level (blue sky, teal cells, violet DNA, magenta nucleus), not dark and muted. Earthy-only was too dull.
- Hero subjects must contrast with their surroundings: the tree sits on a rock cliff with a dirt top and an orange/pink-flecked canopy above green fields; the grasshopper is yellow-lime on a darker leaf.
- Clouds: thin, translucent (opacity ~.4) - solid white blocks looked like blobs. Fade clouds/atmosphere/rings out as the camera passes through them.
- Optional extra level for continuity between big jumps (e.g. Earth -> tree on a cliff -> grasshopper).

**Camera (most important feedback): smooth, never start-stop.** Use `logPos` (constant scale-rate log zoom toward a point just above the target) driven by `zoomU`: the level arrives with momentum from the previous dive, settles into a slow wide drift so the whole world is readable, then smoothly accelerates into the dive and keeps that speed through the outgoing crossfade (no clamp at the end). Holds, partial zooms that stop, and a perfectly constant rate were all rejected (constant rate also lost the wide views). Only the very first shot eases in from rest; the ending cranes up with an ease-out. ~3 s per level; the first level can be shorter (3 s was enough for the galaxy).

**Transitions:** 0.5 s crossfade centred just before each boundary; outgoing blocks scatter around the camera while the incoming level's blocks swirl in and lock; a spark burst from the target; the scale counter (10^n m, decoding text) sweeps its exponent during the crossfade, plus a side ruler. In-level reveals: a proton breaking open to show three quark orbs with gluon chains, strings bursting into the foam.

**Sound:** ambient bed rising in pitch across the film + per-level textures (sparkles, sun rumble, wind, birds, chirps, bubbles, plucks, orbit whirr, crackle, boom) + an **8-bit layer**: square-wave pentatonic blips as blocks snap in, crushed-noise scatter + rising power-up arpeggio + a coin ding on each new label, short chip motifs per level, a title jingle. Build the 18 s mix, then retime events to a longer cut by piecewise time-mapping `put()` start times (keeps each sound's length).

**Pitfalls:** additive `PointsMaterial` sprites with size attenuation become screen-filling white blobs near the camera - use the capped-size, near-faded point shader; a BackSide atmosphere sphere floods the screen when the camera goes inside it; ShaderMaterial outputs linear colour (square sRGB-designed values or they wash out); lots of glowing cubes + bloom overexpose - keep bloom ~.35-.6 with threshold .8+; never `pkill -f` a pattern contained in your own command line.

## 4. Reusable code

- Mode G voxel engine: copy the appendix below into `vox.js` (needs Three.js and a tiny `lib.js` with `THREE, rnd, clamp, sm, GLOW`); the full 11-level project ships as `Voxel_PowersOfTen_project.zip`.
- `scripts/mg_kit.py` - easing, fonts, rounded masks/shadows, `words_line`, `glow_icon`, `pill`, `frosted`, `BeforeAfterSlider`, whip transition, `warp_rgba` + `quad3d`, dotted boxes/arrows, `bottom_gradient`, `place_card`, `loading_card`, `canvas_quad_from_outline`, `glass_panel`, `canvas_to_screen`, `tight_shadow`, `text_shadow_footage`, palette constants.
- `scripts/flat25d_kit.py` - Mode F toolkit: banded/cel shapes, wobble paths, rounded iso + biome islands, rotating holograms, people with IK, mature aliens, shops/towers/landmarks/vehicles, glitch + transition helpers, `post()`. `scripts/examples/flat25d_example.py` renders a street scene -> code-glitch transition -> alien lab with a hologram.
- `scripts/sfx_kit.py` - `Mixer`: tick/chime/thud/sparkle/scribble/typing, `pop`, `swell`, `glass`; shot-audio beds; mix-under-voice with limiter; stem export (`whoosh`/`swish` exist but are discouraged in every mode). Build Mode B foley on top of `Mixer.put` from the recipes above.
- `scripts/person_matte.py` - propagated GrabCut + guided filter; `--static-fg` polygon for desks/laptops in locked-off shots. Written for 1920x1080 - adapt seeds and sizes for 9:16.
- `scripts/find_jump_cuts.py`, `scripts/word_srt.sh`, `scripts/srt_words.py`, `scripts/find_pip.py`, `scripts/match_frames.py` - inputs & analysis.
- `scripts/setup_env.py` - one-time environment setup (packages, Poppins fonts, ffmpeg check); run it automatically before the first render.
- `scripts/render_template.py` - skeleton renderer + chunked background rendering + encode.
- `scripts/examples/intro_render_example.py` + `intro_sfx_example.py` - the full approved Mode A intro.
- `assets/dark_grid.jpg` - approved dark grid background (1920x1086; crop rows 3:1083).
- Mode B building blocks to re-create when needed: `text_rgba` (cached PIL text layer with padding), `blit` (scale / blur / padded shadow), `reveal` (blur-in rise), `sprite` (pop + parallax drift), `split(t, p, panel_fn, fade)` (push layout, p > 1 expands to full frame), `head(t)` (segment remap + real-frame crossfade), `captions`, `circle` / `rect` / `poly_line` (16x subpixel AA), `pie` (radial sweep), `mblur_text` (rolling-counter blur), `ink_rgba` (ink spread inside a sprite), `embers`, `bgz` (background push), `dust`, `glow`, and a `TRANS = {time: (kind, duration)}` table rendered in `render(i)` (kinds: cut, iris, drop, push, redwipe, white).

If a script or helper listed here is missing from this install, the updated scripts/references ship in the `ai-video-motion-graphics.skill` package - ask the user to upload it, or reimplement from the descriptions above. Import helpers with `sys.path.insert(0, '<skill>/scripts')`; copy and adapt rather than rewriting from scratch.

## Appendix - Mode G voxel engine core (`vox.js`)

```js
import { THREE, rnd, clamp, sm, GLOW } from './lib.js';
export const V = (x, y, z) => new THREE.Vector3(x, y, z);
const col = new THREE.Color();

const VS = `
attribute vec3 iPos, iScl, iCol; attribute float iGlow; attribute vec4 iRnd;
uniform float uT,uAsm,uOut,uSpread,uPulse,uWaveF,uWaveS,uGlowW,uCol; uniform vec3 uCenter,uWaveD;
varying vec3 vN,vW,vCol,vLN; varying vec2 vUv; varying float vGlow;
mat3 rotA(vec3 a,float g){a=normalize(a);float s=sin(g),c=cos(g),o=1.-c;
 return mat3(o*a.x*a.x+c,o*a.x*a.y+a.z*s,o*a.z*a.x-a.y*s, o*a.x*a.y-a.z*s,o*a.y*a.y+c,o*a.y*a.z+a.x*s, o*a.z*a.x+a.y*s,o*a.y*a.z-a.x*s,o*a.z*a.z+c);}
void main(){
 float st=iRnd.w;
 float ai=clamp((uAsm-st*.45)/.55,0.,1.);ai=ai*ai*(3.-2.*ai);
 float oi=clamp((uOut-st*.45)/.55,0.,1.);oi=oi*oi*(3.-2.*oi);
 float k=(1.-ai)+oi;
 vec3 rd=normalize(iRnd.xyz*2.-1.+vec3(1e-3));
 vec3 rc=iPos-uCenter;vec3 radial=rc/(length(rc)+1e-3);
 vec3 off=(rd*(1.-ai)*1.6+(radial*1.6+rd*.9)*oi)*uSpread*(k*k*.75+k*.25);
 float wv=sin(dot(iPos,uWaveD)*uWaveF-uT*uWaveS+st*2.)*.5+.5;
 vec3 sc=iScl*mix(.15,1.,clamp(1.-k,0.,1.))*(1.+uPulse*(wv-.5));
 float colH=0.;
 if(uCol>.5){float d=length(iPos.xz);float T=uT*2.2+1.5;colH=.25+max(0.,sin(d*1.1-T*2.2)*1.1+sin(iPos.x*.45+T*.6)*sin(iPos.z*.4-T*.45)*1.1+.45)*uCol;sc.y*=colH;}
 mat3 R=rotA(rd,k*3.6);
 vec3 lp=R*(position*sc);
 vec4 w=modelMatrix*vec4(lp+iPos+off+vec3(0.,colH*.5,0.),1.);
 vN=normalize(mat3(modelMatrix)*(R*normal));vLN=normal;vW=w.xyz;vUv=uv;vCol=iCol;
 vGlow=iGlow*(1.+uGlowW*(wv-.5)*2.)+k*.25+(uCol>.5?smoothstep(1.9,2.6,colH)*.9:0.);
 gl_Position=projectionMatrix*viewMatrix*w;}`;
const FS = `
uniform vec3 uL,uFogC,uSky,uGnd;uniform float uAmb,uFogD,uSun,uSpec,uSat,uGlowK,uOp;
varying vec3 vN,vW,vCol,vLN;varying vec2 vUv;varying float vGlow;
float hh(vec2 p){return fract(sin(dot(p,vec2(12.9898,78.233)))*43758.5453);}
void main(){vec2 e2=min(vUv,1.-vUv);float e=min(e2.x,e2.y);
 vec3 N=normalize(vN);vec3 V=normalize(cameraPosition-vW);
 float lum=dot(vCol,vec3(.299,.587,.114));vec3 alb=mix(vec3(lum),vCol,uSat);
 float bev=mix(.7,1.,smoothstep(.0,.11,e));
 float face=vLN.y>.5?1.:(vLN.y<-.5?.62:(abs(vLN.x)>.5?.86:.78));
 float grain=.94+.06*hh(floor(vUv*14.)+vCol.xy*31.);
 float wrap=max((dot(N,uL)+.25)/1.25,0.);
 vec3 hemi=mix(uGnd,uSky,N.y*.5+.5);
 vec3 c=alb*(hemi*uAmb+vec3(1.,.96,.9)*wrap*uSun)*bev*face*grain;
 c+=vec3(1.)*pow(max(dot(reflect(-uL,N),V),0.),20.)*uSpec*bev;
 c+=alb*pow(1.-max(dot(N,V),0.),3.)*.3;
 float em=max(vGlow-1.,0.);c+=vCol*em*uGlowK*mix(.6,1.,smoothstep(.06,.16,e));
 float d=length(vW-cameraPosition);c=mix(c,uFogC,1.-exp(-d*uFogD));
 gl_FragColor=vec4(c,uOp);}`;

// cube collector
export class Vox {
  constructor() { this.p = []; this.s = []; this.c = []; this.g = []; this.r = []; }
  add(x, y, z, sx, sy, sz, color, glow = .5, st) {
    this.p.push(x, y, z); this.s.push(sx, sy ?? sx, sz ?? sx);
    if (Array.isArray(color)) this.c.push(...color); else { col.set(color); this.c.push(col.r, col.g, col.b); }
    this.g.push(glow); this.r.push(rnd(), rnd(), rnd(), st ?? rnd() * .98); return this;
  }
  get n() { return this.g.length; }
  mesh(o = {}) {
    const box = new THREE.BoxGeometry(1, 1, 1); const g = new THREE.InstancedBufferGeometry();
    g.index = box.index; g.setAttribute('position', box.attributes.position); g.setAttribute('normal', box.attributes.normal); g.setAttribute('uv', box.attributes.uv);
    const A = (a, k) => new THREE.InstancedBufferAttribute(new Float32Array(a), k);
    g.setAttribute('iPos', A(this.p, 3)); g.setAttribute('iScl', A(this.s, 3)); g.setAttribute('iCol', A(this.c, 3)); g.setAttribute('iGlow', A(this.g, 1)); g.setAttribute('iRnd', A(this.r, 4));
    g.instanceCount = this.n;
    const u = {
      uT: { value: 0 }, uAsm: { value: 1 }, uOut: { value: 0 }, uSpread: { value: o.spread ?? 1 }, uPulse: { value: o.pulse ?? .2 }, uWaveF: { value: o.waveF ?? 2 }, uWaveS: { value: o.waveS ?? 3 }, uGlowW: { value: o.glowW ?? .4 }, uCol: { value: o.col ?? 0 },
      uCenter: { value: o.center ?? V(0, 0, 0) }, uWaveD: { value: (o.waveD ?? V(.7, .3, .6)).clone().normalize() },
      uL: { value: (o.light ?? V(-.5, .8, .4)).clone().normalize() }, uFogC: { value: new THREE.Color(o.fogC ?? 0x000000) }, uAmb: { value: o.amb ?? .55 }, uFogD: { value: o.fogD ?? 0 }, uSun: { value: o.sun ?? 1.0 }, uSpec: { value: o.specM ?? .04 }, uSat: { value: o.sat ?? 1.08 }, uOp: { value: o.opacity ?? 1 }, uGlowK: { value: o.glowK ?? 1.0 },
      uSky: { value: new THREE.Color(o.sky ?? '#8fa6c0') }, uGnd: { value: new THREE.Color(o.gnd ?? '#3a3128') },
    };
    const m = new THREE.Mesh(g, new THREE.ShaderMaterial({ uniforms: u, vertexShader: VS, fragmentShader: FS, transparent: (o.opacity ?? 1) < 1, depthWrite: (o.opacity ?? 1) >= 1 }));
    m.frustumCulled = false; m.u = u; return m;
  }
}
// set life uniforms on many meshes
export function life(meshes, t, asm, out) { for (const m of meshes) { m.u.uT.value = t; m.u.uAsm.value = asm; m.u.uOut.value = out; } }

// powers-of-ten camera: constant scale-rate approach from start to end
export function logPos(start, end, u, ratio, ease = 1) { const uu = Math.max(0, u); const e = 1 - Math.pow(ratio, uu); return start.clone().lerp(end, e); }
// life helpers given local time t, scene lead and boundary time D
export const asmAt = (t, lead) => sm(lead - .48, lead + .7, t);
export const outAt = (t, D) => sm(D - .62, D + .16, t);

// smooth zoom profile per level: arrives with momentum from the previous cut, settles into a slow wide drift to show the level,
// then smoothly accelerates into the dive and keeps that speed through the outgoing transition. velocity never jumps or hits zero.
export function zoomU(t, lead, D) {
  const t0 = lead - .45; const x = Math.max(0, (t - t0) / (D - t0));
  const U = y => (1 - Math.exp(-12 * y)) / 12 + .25 * y + .6667 * Math.pow(y, 4);
  if (x <= 1) return U(x);
  const v1 = Math.exp(-12) + .25 + 2.6668; return U(1) + v1 * (x - 1);
}
```

Use: `const vx = new Vox(); vx.add(x,y,z, sx,sy,sz, "#ff6a8a", .5); const m = vx.mesh({spread:2, center:T, sky:"#e0f4ff", gnd:"#3a4a60", fogC, fogD:.03}); scene.add(m);` then in `update(t)`: `life([m], t, asmAt(t, lead), outAt(t, D)); look(cam, logPos(start, end, zoomU(t, lead, D), ratio), target);` with `ratio` = final distance / start distance (e.g. .004-.012).