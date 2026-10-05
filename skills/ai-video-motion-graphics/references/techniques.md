# Techniques

Contents: 0 Whisper word SRT · 1 Word timing · 2 Draft matching · 3 PiP & person mattes · 4 Camera/ground tracking · 5 Object tracking · 6 World-anchored billboards · 7 3D slabs, curved walls, layer stacks · 8 Before/after · 9 Particles & dissolves · 10 Chalk illustrations · 11 Analysis overlays · 12 Graphics-only layer from two renders

## 0 Whisper word SRT
- `scripts/word_srt.sh in.mp4 out.srt` (needs HF domains allowlisted). Skim for misheard product names (Seedance, Artlist, Tao Prompts) and note wording that differs from the script.

## 1 Word timing
- Preferred: word-level SRT → `scripts/srt_words.py` → list of (start, end, word).
- Fallback: plot RMS envelope (dB) + spectrogram with 0.1 s ticks, read syllable onsets; known transcript helps. State that timings are estimated.

## 2 Draft matching (user mock-ups)
- `scripts/match_frames.py`: downsample every draft frame and every source frame to 96×54 gray, pick min mean-abs-diff → (shot, src time) per draft frame. Linear fits give offsets (e.g. src = t − 2.52).
- Slider position: per column, compare draft to original vs graphics versions; columns closer to graphics = revealed side.
- Card rectangles: diff draft frame vs background plate; row/column scans give bounds; view the frame to confirm.
- Brightness spikes where matching fails are often effects baked into the graphics version (e.g. glitch flashes) — check before "fixing".

## 3 PiP & person mattes
- PiP box: diff frame vs the known background (e.g. grid PNG resized to 1920×1086 and cropped 3:1083); largest connected component. Corner radius: inspect max-over-time brightness near a corner.
- Composite PiP last with a rounded-rect mask (~21 px radius) so graphics never cover it; add your own soft shadow if the card overlaps.
- Person matte without ML: GrabCut at half-res with seeds (definite FG ellipse on face/torso, definite BG in known background zones like a lamp or shelf), propagate each frame from the previous mask (eroded→FG, dilated band→probable). Then full-res refine with a guided filter (box-filter implementation, r=10 eps=2e-4, then r=4 eps=1e-4) using grayscale as guide, temporal blend 0.7/0.3. Great for dark hair against light walls.
- Text "behind the head": composite text before re-applying `person * matte`.

## 4 Camera / ground tracking
- Frame-to-frame homography: SIFT (2500 feats) on half-res frames, ratio test 0.72, RANSAC 5 px; save per-transition matrices; chain to map any ref-frame ground point to any frame (`H_r→i`). Works for tabletop/diorama footage where the ground is the dominant plane.
- Full tracking makes on-screen text slide fast when the camera moves; it reads as "hard to follow". Either use billboards anchored to objects (static-world feel, as requested) or damp motion — but prefer placing text in screen space for readability.

## 5 Object tracking
- LK median of good features in a 60 px radius around the anchor, forward-backward check (<1.5 px) — mark invalid when too few points survive or the anchor leaves frame. Anchor on textured parts of the object (not sky above it). Start tracks after the object finishes appearing.
- Coloured HUD rings etc.: HSV threshold + connected components each frame.

## 6 World-anchored billboards
- Position = tracked anchor + offset × local scale^0.6; always face camera; flip-in via Y-rotation with perspective; gentle sway. Hide/fade when tracking invalid.

## 7 3D slabs, curved walls, layer stacks
- Project local rect corners with rotation (Ry·Rx) and focal ≈1500: `x' = cx + f·X/(f+Z)`.
- Extruded text: draw N layers at z=depth·k/N with darker face colour, then the face; soft blurred shadow first.
- Curved screens: split texture into ~18 vertical strips on a cylinder; accumulate *premultiplied* warps into one buffer and composite once (otherwise AA seams show as dark lines).
- Layer stack: tilt plates ~50°, lift each by ~150 px, scale 0.7; plates = base video, analysis RGBA, graphics RGBA; thin clay outline + faint white plate so each layer reads; labels to the right with leader lines; collapse back to the finished frame.

## 8 Before/after slider
- Frame-aligned original and graphics renders; `img[:, :x] = graphics[:, :x]`.
- Motion: `p = 0.46·easeOut((t−t0)/0.8) + 0.10·smoothstep((t−t0−0.5)/2.05) + 0.44·easeInOut((t−t0−2.3)/0.95)` → glide, crawl, reveal.
- Visual: 1–2 px white divider + soft glow, frosted capsule handle (≈52×128) with thin chevrons, frosted label pills at bottom corners that fade as their side shrinks. See `mg_kit.BeforeAfterSlider`.

## 9 Particles & dissolves
- Reveal field = 0.55·smooth noise + 0.45·|x−0.5|·2 (or +edge term to draw outlines first); alpha = clip((p·1.15 − field)/0.12). Add a bright edge band at the front.
- Particles: sample targets on the destination surface, start at random offsets (110–340 px), eased paths with a sine swirl, arrive at the time the reveal front passes; then drift and fade. Start them only ~0.2 s before the reveal or they read as floating snow.

## 10 Chalk illustrations
- Generate a sprite sheet (e.g. Seedream 2K, 16:9, "white chalk on pure matte black, textured strokes, cross-hatching, each drawing centred in its own cell, no text"). Crop by hand-measured boxes (drawings don't align to an even grid), keep the largest blob, alpha = clip((lum−0.13)/0.62)^0.75·1.3.
- Composite with a dark halo (blurred alpha, ~0.8) so white chalk reads on light footage; draw-on with a noise/edge reveal field; chalk dust at the reveal front; dissolve out into dust.

## 11 Analysis overlays (explainers)
- Hold one sharp frame; dim 30% + desaturate 40%.
- Ground grid (white, dark outline), 20–30 feature points (white dot, clay core, dark ring), 3–4 landmark boxes with thick white corner brackets and dark label chips (name + coordinates), dashed clay "text zone"/"illustration zone" boxes derived from where the finished graphics actually land.

## 12 Graphics-only layer from two renders
- diff = max_channel(|graphics − original|); alpha = clip((diff − 0.10)/0.12), dilate 3 px, blur 1 px. Split by region (e.g. top band = text, right block = illustration) if you need separate layers.

## 13 AR glass panel fitted to a drawn outline
- User scribbles a 4-point outline on a screenshot -> convert screenshot px to frame px (subtract the player border, scale to 1920). `canvas_quad_from_outline(outline, panel_rect, canvas_size)` gives the quad for `warp_rgba`; animate intro by scaling the quad about its centre (0.92->1) + small x offset, bob with a sine.
- Order: background plate -> glass (`glass_panel`, blurs only the plate) -> warped UI -> person/desk matte on top (static-camera desk polygon via `person_matte.py --static-fg`). Clip UI content to the (animated) panel shape so growing panels never spill.
- Staged layout by morphing slot rects between layouts with `eio` and a 0.05 s stagger per item.
- Thumbnails flying into slots: compute slot corners in screen space via the canvas homography, fly in screen space (drawn over the person), switch to the in-canvas thumbnail on landing with a small bounce.

## 14 Board with converging arrows
- Quadratic bezier from each asset's label (bottom) to spread points on the video card's top edge, control point 75 % down near the start x; grow the stroke with `eo`, arrowhead at the end, a dot travelling along each curve. Draw arrows on their own layer and add `shadowed(layer,(0,3),5,0.75)` so they read on any background.

## 15 Step list with sliding highlight
- `active_pos(t) = sum(eio((t - SA[k]) / 0.4))` gives a continuous row index; draw base rows, then the highlight bar at `LY0 + active_pos*LGAP`, then per-row text whose colour mixes by `on = clamp(1 - |active_pos - k|)`. Connector line fills to the same position.
