# Lessons from the first production (Tao's feedback, v1 -> v5)

Story & variety
- Give the video a story of the characters' ORIGIN and a JOURNEY: Brush is typed in a code editor and compiled line by line; Render is diffused from noise under a GENERATING bar; they travel through different worlds, meet, and perform together. "Standing in one place doing the same thing" was called repetitive.
- One environment per musical phrase. A second half that stays on one stage reads as repetitive — move the chorus through several locations (highway, timeline studio, dream party) and come back to the stage for the finale.
- Build the environments FROM the user's environment sheets (repaint them in code). When the user said "use the original environments", inventing new ones was rejected.
- Every prop must make sense for the character using it (see prompts.md).
- Finale needs the most spectacle: particles, beams, props floating in the background, fireworks on the beat, confetti.
- Don't add gags that don't fit the story (a cursor flying out of the monitor at the end "didn't make sense").

Text
- Plain cartoon lettering was rejected. Use code-style glowing monospace text (fxtext.code_text): type-on with a block cursor, decode from scrambled glyphs, pixel-form, flicker; glitch/backspace/pop exits.
- Mix placements: only SOME lines in a translucent terminal panel; integrate the rest into the world — typed into the sky behind the character, painted onto a road surface in perspective (on_quad), rising out of a lane behind a rider, typed as a clip on a timeline track, forming out of a constellation, bouncing to the beat.
- Every text must stay readable >= 1 s (aim 1.2-2 s). Lines that flashed for 0.3-0.7 s were called pointless — merge or cut them.
- Keep text fully inside the frame (account for camera zoom, beat bounce and glyph height). Check every text moment on a contact sheet.

Motion & camera
- Moving shots need visible motion: a tracking camera that follows riders along a winding road, flowing lane dashes/cubes/wind streaks, trails. A static frame with riders that "stop" read as not moving.
- Paths/roads must run off the edge of the frame, never end mid-screen.
- Keep two characters apart on screen; never let one hide behind the other.
- 3D-feeling moves work in flat 2D: orbit = pan the world + turn characters through their drawn views + circle props/clones on an ellipse with depth sorting (behind/in front) and depth scaling.
- Transitions should come from the world: dive through a screen, light-trail whip, shiny-square dissolve, iris on a halo, cut on a jump, flash, timeline playhead scrub, code-rain wipe, pull back out of a monitor. Never repeat one back to back.

Lip sync
- Code can only do mouth flaps from word timings. For real lip sync, export clean stills (text hidden, mouths closed, face big, camera steady 3-5 s) and the user animates them in an AI video model.
