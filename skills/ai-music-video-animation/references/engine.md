# Engine reference (scripts/)

Python + skia-python (pip install skia-python), numpy, opencv, ffmpeg. 1920x1080, 24 fps, ~1 s/frame on 2 CPUs.
Why not the p5.js/p5.brush repos (JohnHeibel/ClaudeAnimationBase, PDoomVideo)? Same look, but headless Chrome with software WebGL took ~50 s/frame in a GPU-less sandbox. This engine reproduces the look (boiling ink, watercolour washes, paper grain) natively.

engine.py
- Time: clamp, lerp, seg, ease/easeIn/easeOut/backOut/elasticOut, kf(t, [(t,v)...]), spring, pulse(t) (beat-locked), bp(t) beat position, arcPt. BPM/OFFSET set the beat (detect with librosa).
- Boil: CTX.bi = int(t*12); rng(key) and boil(P, key, amp) wobble outlines 12x/s; keys must be stable per element.
- Paint: fill(P, col, key, tex, edge, outline) watercolour wash + granulation + darkened edge; ink(P, w, col, key, closed) variable-width brush line; wash, shade (multiply), glow (additive), grad_rect, blob_union/fillpath (cumulus shapes via path ops).
- Shapes: ell, rect, rrect, catmull, densify, ribbon, topath.
- Camera: cam_begin(cx, cy, zoom, rot) ... cam_end(), to_screen, shake.
- Full-frame: brush_wipe, iris, flash; finish() multiplies paper grain + vignette.
- PERFORMANCE: creating a new skia Paint with a shader costs ~20 ms the first time it is drawn -> cache shader paints (texpaint). A full-device clipPath per shape is slow; draw textures with the path itself.

chars.py — Brush (walking paintbrush) and Render (AI blob), both drawn from parameters every frame
- brush(x, y, u, o) / render_bot(x, y, u, o); (x, y) = ground point, u = size unit.
- o keys: eyes (dot happy closed wide angry sad heart star x narrow), brows, mouth (smile open O frown grin flat smirk wobble), mouthOpen (singing), lookX/lookY, head (heading in turns: 0 front, .25 right, .5 back -> drawn turn views), sq (squash), rot, bend (spine curve), aL/aR arm angles, aLpos/aRpos hand targets, walk phase, lift, hair sway, key (unique per instance), noShadow; Render: glitch (pixel shedding), mat, halo spin, lean.
- emote(kind, x, y, s, k, age): excl, spark, hearts, sweat, music (glowing notes), q, anger. sparkle(), heart_pts, star_pts.
- To make NEW characters, follow the same pattern: a few parametric parts (body path, face on a sub-frame, noodle limbs via _limb, hooks), always fill()+ink() so they boil.

envs.py (sheet 1: desk at night with drawScreen hook, code world, AI dream cloud, stage) · envs3.py (sheet 2: gpucity + road_quad/road_pt, highway + hw_at/hw_lane, garden, timeline + playhead_x) · envs2.py (digital FX: gline glowing lines, gbox shiny squares, particles, editor() code-editor UI, light_whip, data_rain_wipe, dive_streaks, noise_dissolve, grid_floor).
props.py: keycap, cursor_ship, palette_board, gpu_prop, portal, film_reel, data_chest, ink_splash, pixel_firework, light_ribbon, code_board, halo_disc.
fxtext.py: code_text(t, text, x, y, size, t0, t1, cols, style=type|decode|pixel|flicker, out=glitch|delete|pop, panel, scan, beat, wave); lettering() (cartoon font, rejected for this project); gen_bar() GENERATING progress bar. Fonts in ../fonts.

Scene pattern (see examples/code_and_ai)
- A shot is fn(t): cam_begin -> environment(t) -> things behind characters (text, trails, ghosts) -> characters -> things in front -> cam_end -> screen-space text -> transitions. Pure function of t (frames render out of order in 2 workers).
- SHOTS = [(start, fn), ...]; draw(t) picks the shot; special transitions that need both shots (playhead scrub) render both and clip.
- render(t) creates the surface, clears to paper, draws, returns finish(...) as BGR.
- Example layering: scenes.py (v1 shots + helpers: sing, jump, take, bounce, faces, ghost, confetti) -> scenes2.py (v2: editor intro, scanline birth, digital FX) -> scenes3.py (v3-v5: 8 environments, props, integrated text, orbit, playhead scrub; it monkeypatches scenes2's environment hooks). For a NEW video, copy scenes3.py as a template and rewrite the shots; keep helpers.
