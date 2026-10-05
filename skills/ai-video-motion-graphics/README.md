# AI Video Motion Graphics - a Claude skill

Code-driven motion graphics, explainer animations and sound design, rendered frame by frame in Python (skia / OpenCV / PIL) and encoded with ffmpeg. Created by **Tao Prompts** (AI-video education on YouTube).

Examples of every style and install steps: https://github.com/tao-prompts/claude-motion-graphics

## Styles (switch any time: "use the vertical editorial style")
| Style | For |
|---|---|
| A. Tutorial UI animations | 16:9 tutorials and intros over a talking head or AI clips |
| B. Vertical editorial style | 9:16 news / money / history shorts |
| C. AI-video overlays | graphics living inside AI-generated scenes |
| D. 2D illustration animation | bringing a single illustration to life with no footage |
| E. Character music video | hands off to the sibling skill `ai-music-video-animation` |
| F. 2D animated explainer | fully animated, VO-driven science/idea explainers with characters, isometric worlds and holograms |
| G. 3D voxel animation | a continuous 3D "Powers of Ten" zoom through scales or worlds, built from clay-like cubes |

## Install
1. Upload `ai-video-motion-graphics.zip` as a skill in Claude (Settings -> Capabilities -> Skills), or copy this folder to `~/.claude/skills/` for Claude Code.
2. That's it. On first use Claude runs `scripts/setup_env.py`, which installs the Python packages and sets up the Poppins fonts (bundled under their SIL Open Font License in `assets/fonts/`). The only thing it can't install silently is ffmpeg - Claude will give you (or run) the one-line command for your OS.

## Contents
- `SKILL.md` - the instructions Claude follows (workflow, styles, transitions, sound).
- `references/` - style rules, techniques, sandbox notes, 2D explainer notes.
- `scripts/` - `mg_kit.py`, `sfx_kit.py`, `flat25d_kit.py`, analysis helpers and worked examples.
- `assets/` - backgrounds and Poppins fonts (SIL Open Font License, see `fonts/OFL.txt`).
