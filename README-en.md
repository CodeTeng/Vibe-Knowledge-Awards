# Vibe-Knowledge-Awards

<p align="center">
  <img src="https://img.shields.io/badge/type-Agent%20Skill-6E56CF" alt="type">
  <img src="https://img.shields.io/badge/render-Canvas%20%2B%20seek(t)-0A7CFF" alt="render">
  <img src="https://img.shields.io/badge/audio-numpy%20synth-1DB954" alt="audio">
  <img src="https://img.shields.io/badge/ratio-16%3A9%20%7C%201920%C3%971080-FF8A00" alt="ratio">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="license">
</p>

<p align="center"><b>Turn one idea into a narration-free, Douyin "Vibe Knowledge Awards" style short — drawn frame by frame in code.</b></p>

<p align="center"><a href="README.md">简体中文</a> · <b>English</b></p>

---

## What is this

A **skill** for AI coding agents that produces narration-free knowledge shorts in the Douyin "Vibe Knowledge Awards" style.

The finished film is 2–5 minutes, 16:9 landscape, **no voiceover** — the viewer reads one line of subtitle at the bottom while the screen **acts the sentence out**. Nothing is filmed or cut from stock footage; every frame is **drawn by code**: Canvas + JavaScript paints each frame → Playwright screenshots the browser frame by frame → ffmpeg encodes the video → sound is mixed in.

It is not template-filling: every shot is written against a storyboard, each concept first gets a concrete image a layperson recognizes, and whatever the sentence says is exactly what's on screen. The full method and workflow live in `SKILL.md` and `references/`.

## Install to your local Agent

> **Tip — easiest install**: just give the repo URL to a command-capable agent (e.g. Claude Code) and say *"install this skill locally: git@github.com:CodeTeng/Vibe-Knowledge-Awards.git"*. It will clone it, drop it into your skills folder, and set up the dependencies and fonts for you. Manual steps are below.

Put this repo into your agent's skills directory, **keeping the folder name `vibe-knowledge-awards`** (it must match the skill name in `SKILL.md`; the GitHub repo name and this folder name may differ). For Claude Code that is usually `~/.claude/skills/vibe-knowledge-awards`.

```bash
git clone git@github.com:CodeTeng/Vibe-Knowledge-Awards.git vibe-knowledge-awards
# move it into your agent's skills dir, e.g.:
#   mv vibe-knowledge-awards ~/.claude/skills/

cd vibe-knowledge-awards
pip install -r requirements.txt     # playwright / numpy / scipy / Pillow
python -m playwright install        # browser driver
python engine/get_fonts.py          # open-source fonts (SIL OFL, not shipped in the repo)
```

You also need **Google Chrome** and **ffmpeg** (with an H.264 encoder such as libx264) installed. The render script drives your local Chrome; fonts are fetched separately under the SIL Open Font License, so run `get_fonts.py` once.

## Two styles

The topic decides the style, chosen after the storyboard:

- **C · Nocturne** — for abstract, invisible mechanisms (math, logic, information, physics) broken into small experiments you can act out. Deep blue-black ground, big type, instruments with scales and things drawn to look like the real object; sound fully synthesized in code. When unsure, pick C.
- **B · Fable** — for a psychological / behavioral mechanism, told from an animal experiment or everyday scene toward "what you should do". Each scene is a flat illustration drawn in code, with characters and motion, over a background track. The most labor-intensive.

One film uses one style only. Colors, type, layout, title cards and sound specs for both are in `references/worlds.md`.

## How to use

### Hand it to the Agent (recommended)

Give a finished script, or just a topic, to an agent that has this skill installed. It follows the workflow in `SKILL.md`:

1. **Thesis & fact table** — one-sentence claim + concept list; verify every year / name / number.
2. **Find the image** — give each concept something a layperson recognizes to act it out (the step that makes or breaks the film).
3. **Script + storyboard** — one subtitle per line; for each line write what's on screen, what it's doing, and what sound.
4. **Pick a style** — C Nocturne or B Fable.
5. **Build the project, do the hardest shot first** — screenshot and self-check.
6. **First 30 seconds** — you review a 30s sample before the full film is built.
7. **Build out → add sound → final check → deliver.**

It stops at key points (image, storyboard, 30s sample) to show you the plan and waits for your OK before moving on.

### Run the scripts manually

Create the project inside your own project folder — **not inside the skill directory**.

```bash
# 1. New project (C Nocturne; --world B for Fable; --size 1080x1920 for vertical/square; duration defaults to the bundled BGM, override with --secs)
python scripts/new_film.py <project_dir> --world C

# 2. Self-check the picture while writing film.js
python engine/render.py <project_dir> --serve              # live browser preview
python engine/render.py <project_dir> --sheet 16           # contact sheet of 16 even frames
python engine/render.py <project_dir> --density            # motion-density check: flag static spans

# 3. Render the full film (silent)
python engine/render.py <project_dir>                      # → renders/raw.mp4
python engine/render.py <project_dir> --jobs 4             # long film, 4-way parallel

# 4. Sound + mux + cover (bundled BGM by default; the video ends when the BGM ends)
python engine/audio.py  <project_dir> --beats              # measure the BGM's BPM / downbeats / sections (for beat-sync)
python engine/render.py <project_dir> --events             # export the SFX event table
python engine/audio.py  <project_dir> --probe              # synth sound + mux → renders/final.mp4, plus an audio probe
python engine/render.py <project_dir> --cover 18.5         # grab one frame as the cover → renders/cover.jpg
```

Engine API, command details and gotchas are in `references/engine.md`; subtitles / drawing / finding images / storyboard in `references/visualization.md`; sound design in `references/worlds.md`.

## Samples

TODO

## License

The engine, scripts and the method notes in the docs are under the MIT License — see `LICENSE`.

The subtitles and visual designs transcribed from reference films in `references/analysis.md`, `references/prompts.md`, `references/visualization.md`, and `examples/stim_B`, `examples/info_C`, come from other people's shorts and **remain the copyright of their original authors**; they are for study and comparison only — not licensed for copying, publishing, or passing off as your own work. For a new film, start an empty skeleton with `python scripts/new_film.py` and write each shot from your own storyboard.

## Acknowledgements

This project is adapted from the open-source project **[HeyChengC/vibe-knowledge-film](https://github.com/HeyChengC/vibe-knowledge-film)** (released under MIT). Thanks to the original author. This repository stays MIT-licensed.
