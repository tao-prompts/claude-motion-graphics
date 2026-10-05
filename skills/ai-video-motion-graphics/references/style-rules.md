# Style rules (learned from creator feedback)

Each rule came from a real revision request. Follow them by default; the user's current request wins if it conflicts.

## Look & feel
- Clean, contemporary, cinematic YouTuber vibe. Avoid neon purple/blue "futuristic AI" styling, flat 2D vector/cartoony UI, and cheap-looking stick figures or clip-art doodles.
- Prefer real textures: e.g. AI-generated chalk illustrations (white chalk on black, alpha from luminance) over hand-coded line art; felt/paper feel when the footage is crafty.
- Modern UI components: thin crisp lines with soft glow, frosted-glass capsules/pills (blurred background + light tint + thin white border), generous corner radii.
- Accent colour: clay `#D97757` was the old default. On the Beginner Guide 2026 intro the user moved to a **dark grid background + saturated green `#01FE81`** accent (sky blue `#368AD6` for secondary clips, deeper green `#16A860` for audio clips / check marks). Ask or reuse the latest palette the user approved. **Never red. No pastel accents** (pastel yellow / pastel green and muted greens were rejected as cheap-looking). Success check / error X keep white rim + soft glow.

## Text & readability (most frequent feedback)
- Text over footage: white, bold, strong soft shadow, plus a dark gradient behind the lower part of the frame. Black text over busy/dark video is unreadable.
- On light backgrounds (white grid, bright rooms) use charcoal or white-with-shadow + a subtle dark top/bottom scrim.
- Size up: captions ~56px, key phrase ~96px, pipeline labels ~32px bold, callout labels ~40px. "Too small" is a recurring note.
- Position near eye level / lower-middle. Nothing important at the very top of frame ("no one will see it"). Keep consecutive captions at the same height.
- Word-synced reveals: each word rises in on its SRT time (start ~0.04–0.1s early). Key words in clay or on a clay pill whose box is centred on the *ink bbox* of the text (measure glyph bounds, not layout box).
- Don't let text sit on top of the PiP or the face; put titles behind the person (matte) when depth is wanted, making sure hair/head overlap looks clean.

## Timing & edits
- Never cut between shots while a caption is on screen; hold the shot, fade the caption, then cut.
- Keep shots real-time. No frame-blended slow motion (blurry). For "analysis" moments, hold one sharp frame instead.
- Pick footage windows that show the interesting part (e.g. lock-on + rockets, pyramids popping up, mammoth era) — scan the clip with a contact sheet first.
- Make sure the final seconds land on a clean, settled moment, not mid-transition.

## Density
- Callouts: 2–3 maximum, dotted white boxes + dotted white arrows + white text (no coloured pills), shown one at a time, cleared before action beats. If asked, remove them entirely.
- Tracking/analysis visuals: fewer, bolder elements beat many thin ones. Dim/desaturate the video ~30% during analysis so white overlays pop.
- Tethers/leader lines only if they truly connect to something tracked; otherwise drop them.

## Motion
- Before/after slider: glide in fast and ease down near the middle, crawl slowly (not stopped) for ~1.5–2s so both sides can be compared, then accelerate out to full reveal.
- Screens around a speaker: form a gently curved wall behind the head/neck and drift slowly left→right; don't orbit. Materialise with particles + noise-dissolve; captions warped onto the same curve.
- Titles: rise per letter/word with eased overshoot; big word behind the head, then shrink into a top band.

## Sound
- Voice always dominant. SFX subtle and relevant. **No whooshes at all** (user: "that whoosh sound isn't the best") - use `Mixer.pop` for text/cards appearing, `Mixer.swell` (soft tonal chord) for big words/scene changes, `Mixer.glass` for UI panels, ticks for snaps/typing, a chime when a generation finishes. Prefer the shots' own audio as quiet beds (≈-16 dB) aligned to where each shot plays; add only a few UI cues (ticks, soft chime on a check, a sweep under a slider).
- Always re-time SFX when visual timing changes, and export an SFX-only stem.

## Branding
- Use the official logo file the user provides; never draw a brand logo. Resize in premultiplied alpha to avoid dirty corners; soft small shadow only.

## Learned on the Beginner Guide 2026 intro (talking head -> AR UI -> asset board -> 4-step process)

### Text over talking-head footage
- White text, never ink/black, over a bright room. Strong soft drop shadow + darken the BACKGROUND ~25% (not the person, use the matte) while text is on screen.
- Big word behind the head (Poppins Bold ~270px, letter-by-letter rise with overshoot) is fine; the head hiding one letter is accepted.
- Secondary "cursive" words: a **bold italic serif**, large (~100-128px). The thin Lora Italic was rejected as hard to read. Default: TeX Gyre Termes Bold Italic (`/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyretermes-bolditalic.otf`, Times-like, matches the user's own reference). Alternatives to offer: Pagella / Bonum bold italic, Lora at wght 700. Show a comparison strip on the actual footage when asked about fonts.

### AR / floating UI in a real room
- The panel sits BEHIND the person (matte him + chair + desk on top). Perspective: the side nearest the person recedes, far side is nearer/larger, like the reference UI. When the user draws the outline, map the panel exactly to it (`canvas_quad_from_outline`) and lay the panel out WIDE (~1.9:1) so text isn't squashed.
- Dark mode glass: dark translucent (blur*0.36 + small tint), white text, ~0.35-alpha white border. Light frosted glass was replaced.
- Stage the UI - never everything at once. References fill the panel first (big row), then slide into a compact strip that stays centred/right (left side is hidden behind the shoulder), then the prompt box pops in and types.
- @tags in prompts: coloured text only (light pink on dark glass). No tag boxes/pills.
- Never show credits/cost numbers. Reference images fly from the laptop screen into their slots (screen-space flight, cursor attached).

### Board / process scenes (grid background)
- Dark grid background preferred; every image/video/card gets a thin white border + faint white glow (`place_card`) - black shadows vanish on dark.
- Asset board: assets generate one by one in a row with labels; then rise to a top row and curved accent arrows (with a tight dark shadow) point DOWN into the generated video in the middle; caption under it.
- "Generating video" = `loading_card`: dark placeholder, progress bar with %, clip loads top-to-bottom with an accent scan line (~0.5 s). Noisy blotch dissolves on a big video card were rejected.
- 4-step process: big list on the LEFT (heading + 4 large rows), stage on the RIGHT. Make step changes obvious: a highlight bar that SLIDES between rows, a filling connector line, check marks on done steps, and a big "STEP N  Name" title above the stage that swaps (old out, new in 0.16 s later - never overlapping).
- Step names: Ideation / Asset generation / Video animation / **Post-production** (not "Video editing").
- Editing timeline graphic: only specific, real content (video clips with thumbnails from the actual film + audio track). Generic labels ("Title", "Mask", "Color grade") were rejected - omit rather than invent.
- Don't lay shot audio (e.g. lightsaber fight) under process/explainer animation unless asked.

### Transitions
- Check the talking-head file for internal jump cuts (`scripts/find_jump_cuts.py`). Cut to the next section on the frame BEFORE a jump; a one-frame flash of the next take reads as "a jump in the transition". Blend with a 0.2 s zoom-blur from the frozen last clean frame.
