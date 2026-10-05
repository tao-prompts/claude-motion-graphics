# AI Video Motion Graphics - a Claude skill

Code-driven motion graphics, explainer animations and sound design, rendered frame by frame in Python (skia / OpenCV / PIL) and encoded with ffmpeg. Created by **Tao Prompts** (AI-video education on YouTube).

## Modes (switch any time: "use Mode F", "switch to the documentary style")
| Mode | For |
|---|---|
| A. Tutorial cinematic | 16:9 tutorials and intros over a talking head or AI clips |
| B. Vertical documentary explainer | 9:16 news / money / history shorts |
| C. AI-film overlays | graphics living inside AI-generated scenes |
| D. Pure code animation | animating an illustration with no footage |
| E. Character music video | hands off to the sibling skill `ai-music-video-animation` (optional) |
| F. Flat 2.5D animated explainer | fully animated, VO-driven science/idea explainers with characters, isometric worlds and holograms |
| G. 3D voxel scale-zoom | a continuous 3D "Powers of Ten" zoom through scales or worlds, built from clay-like cubes |

## Install
1. Add this folder (or the `.skill` file) as a skill in Claude (Claude app: Settings -> Capabilities -> Skills, or `~/.claude/skills/` for Claude Code).
2. That's it. On first use Claude runs `scripts/setup_env.py`, which installs the Python packages and sets up the Poppins fonts (bundled under their SIL Open Font License in `assets/fonts/`). The only thing it can't install silently is ffmpeg - Claude will give you (or run) the one-line command for your OS.

## Try it
- "Write a 40-second explainer script about black holes, then animate it in Mode F" (record or generate the VO, drop the audio in your folder, and ask Claude to build it).
- "Add Mode A motion graphics to my talking-head intro" (with a video file).
- Run `python scripts/examples/flat25d_example.py out 120` to render a 4-second Mode F sample.

## Contents
- `SKILL.md` - the instructions Claude follows (workflow, modes, transitions, sound).
- `references/` - style rules, techniques, sandbox notes, Mode F notes.
- `scripts/` - `mg_kit.py`, `sfx_kit.py`, `flat25d_kit.py`, analysis helpers and worked examples.
- `assets/` - backgrounds.
- `assets/fonts/` - Poppins (SIL Open Font License, see `OFL.txt`).
