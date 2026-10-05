# AI Video Motion Graphics — a free Claude skill

Teach Claude to make motion graphics, animated explainers and sound effects for your videos. Claude writes the code, renders every frame and hands you back a finished MP4. You don't need to know how to code.

Created by **Tao Prompts** (AI video tutorials on YouTube).

## What it can make

| Mode | Use it for |
|---|---|
| **A. Tutorial cinematic** | 16:9 YouTube tutorials and intros over a talking head or AI clips |
| **B. Vertical documentary** | 9:16 shorts about news, money or history (Vox / Johnny Harris style) |
| **C. AI-film overlays** | graphics placed inside AI-generated video scenes |
| **D. Pure code animation** | bringing an illustration to life with no footage |
| **F. Flat 2.5D explainer** | fully animated science or idea explainers with characters |
| **G. 3D voxel zoom** | a "Powers of Ten" style zoom from galaxies down to atoms |

Captions, callouts, split screens, counters, charts, floating UI panels, pause trimming and sound effects all come built in.

---

## Install (beginners start here)

You need a paid Claude plan (Pro, Max, Team or Enterprise), because skills run code.

1. **Download the skill.** Go to the [**Releases**](https://github.com/tao-prompts/claude-motion-graphics/releases/latest) page and download **`ai-video-motion-graphics.zip`**. Don't unzip it.
2. **Turn on code execution.** In the Claude app or at claude.ai, open **Settings → Capabilities** and switch on **Code execution and file creation**.
3. **Upload the skill.** On the same page, under **Skills**, click **Upload skill** and pick the zip you downloaded.
4. **Try it.** Start a new chat and type one of the prompts below.

The first time you use it, Claude installs everything it needs on its own.

### Prompts to try

- *"Write a 40-second explainer script about black holes, then animate it in Mode F."*
- *"Add Mode A motion graphics to my talking-head intro."* (attach your video)
- *"Turn this clip into a vertical documentary short in Mode B."* (attach your video)
- *"Make a 3D voxel zoom from the Milky Way down to an atom."*

You can switch styles any time: *"switch to Mode B"*, *"use the documentary style"*.

---

## Install in Claude Code (if you use the terminal app)

Run these two commands inside Claude Code:

```
/plugin marketplace add tao-prompts/claude-motion-graphics
/plugin install ai-video-motion-graphics@tao-prompts
```

Or copy the `skills/ai-video-motion-graphics` folder into `~/.claude/skills/`.

**ffmpeg:** Claude Code runs on your own computer, so you also need [ffmpeg](https://ffmpeg.org/download.html). If it's missing, Claude will tell you the one-line command to install it, or run it for you.

---

## What's inside

- `skills/ai-video-motion-graphics/SKILL.md`: the instructions Claude follows
- `references/`: style rules and techniques
- `scripts/`: the animation and sound toolkits, plus worked examples
- `assets/`: background textures and the Poppins font (SIL Open Font License)

Nothing in this skill calls a paid API. Every graphic and sound is generated in code.

## License

The code and instructions are released under the [MIT License](LICENSE). The Poppins fonts are under the SIL Open Font License (`assets/fonts/OFL.txt`).
