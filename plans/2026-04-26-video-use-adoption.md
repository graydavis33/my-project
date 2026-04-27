# Video-Use + HyperFrames Adoption Plan

**Goal:** Adopt three components — `browser-use/video-use` (Claude Code skill, single-clip AI edit), `heygen-com/hyperframes` (Node-based premium motion graphics), and a new tiny `python-scripts/multicam-mirror/` tool — so Gray can edit his A-cam + B-cam onboarding video end-to-end via Claude Code, with both camera tracks staying in lockstep through every cut.

**Architecture:** `video-use` installs as a Claude Code skill at `~/.claude/skills/video-use/` (Nate's documented path; works on the VSCode Claude extension because it reads `~/.claude/`). HyperFrames runs via `npx` only — no global install — and scaffolds projects under `web-apps/hyperframes/{project-name}/`. `multicam-mirror` is a new Python tool that takes the JSON EDL produced by `video-use` (cut decisions made against A-cam) and applies the same cuts to B-cam after computing the audio offset once via `audalign`. Both tracks emerge cut-perfect, ready to drag onto a Premiere/Resolve timeline as a multicam.

**Tech Stack:** Python 3.13 (`uv` for video-use, `pip` for multicam-mirror), Node 22+ (HyperFrames already runs via existing Node 24), ffmpeg 8.1 (already installed), ElevenLabs Scribe API.

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `~/.claude/skills/video-use/` | Create (git clone) | The video-use skill, picked up by Claude Code automatically |
| `~/.claude/skills/video-use/.env` | Create | `ELEVENLABS_API_KEY=...` |
| `web-apps/hyperframes/.gitignore` | Create | Ignore `node_modules/`, rendered MP4s, npm cache |
| `web-apps/hyperframes/README.md` | Create | "How to scaffold / preview / render a hyperframes project" |
| `web-apps/hyperframes/test-onboarding/` | Create (scaffolded) | First throw-away project to verify the toolchain |
| `python-scripts/multicam-mirror/main.py` | Create | CLI: `python main.py <a_cam.mp4> <b_cam.mp4> <video_use_edl.json>` |
| `python-scripts/multicam-mirror/sync.py` | Create | Audio offset detection via `audalign` (or scipy fallback) |
| `python-scripts/multicam-mirror/render.py` | Create | Per-segment ffmpeg extracts for the offset-shifted B-cam EDL |
| `python-scripts/multicam-mirror/README.md` | Create | Usage + how it composes with video-use |
| `python-scripts/multicam-mirror/requirements.txt` | Create | `audalign`, `numpy`, etc. |
| [CLAUDE.md](CLAUDE.md) | Modify | Bump python-scripts count 15 → 16, add hyperframes web-app, add video-use to Custom Skills |
| [context/priorities.md](context/priorities.md) | Modify | Add adoption note (date + onboarding video as the validation case) |
| [decisions/log.md](decisions/log.md) | Modify | Log adoption decision + multicam-mirror design |

---

## Decisions Locked In

- **video-use lives at `~/.claude/skills/video-use/`** — Nate's documented path; works for Claude Code (VSCode extension reads `~/.claude/`). Cloned directly, no symlink.
- **Skill is git-cloned, not workspace-tracked.** Updates via `git pull` in that folder. Not mirroring it into `python-scripts/` because that would split the source-of-truth.
- **HyperFrames runs via `npx`** — no global install. Saves disk + lets us pin per-project versions later if needed.
- **HyperFrames projects live under `web-apps/hyperframes/{project-name}/`** — it's HTML/Node, parallel to `analytical/`, `payday-checklist/`, etc. Per-project node_modules gitignored.
- **`multicam-mirror` is a new Python tool, not an extension.** No existing tool sees both cams + an EDL. Per build-discipline: this passes the "≥50% overlap with existing tool" test (zero overlap).
- **`audalign` is the sync engine.** Sub-frame accuracy on shared room audio. scipy cross-correlation is the fallback if audalign install is finicky on Windows.
- **ElevenLabs Scribe** is video-use's transcription engine. Gray needs to provide an API key.
- **Don't extend content-pipeline yet.** Validate video-use standalone first. After 5 real Sai shots, then add a `--full-edit` flag to content-pipeline that delegates to video-use.
- **Don't extend footage-organizer.** Different concern (sort vs cut).

---

## Tasks

### Task 1: Install `uv` (the Python package manager video-use uses)

**Why:** video-use's install runs `uv sync`. uv isn't on Gray's system.

**Command (Windows-friendly):**
```bash
pip install uv
uv --version  # verify
```

### Task 2: Clone video-use into the Claude Code skills folder

```bash
git clone https://github.com/browser-use/video-use "$HOME/.claude/skills/video-use"
cd "$HOME/.claude/skills/video-use"
uv sync
```

`uv sync` reads `pyproject.toml` and installs the skill's Python deps into a local `.venv`.

### Task 3: Create the .env for video-use

```bash
cp "$HOME/.claude/skills/video-use/.env.example" "$HOME/.claude/skills/video-use/.env"
# Then Gray pastes ELEVENLABS_API_KEY into that file
```

Gray gets a key from https://elevenlabs.io/app/settings/api-keys.

### Task 4: Verify HyperFrames CLI runs

```bash
npx hyperframes --help
npx hyperframes doctor   # checks Node version, ffmpeg, Chrome paths
```

If `doctor` flags missing Chrome, install Chrome (Gray almost certainly has it).

### Task 5: Scaffold a test HyperFrames project

```bash
mkdir -p "c:/Users/Gray Davis/my-project/web-apps/hyperframes"
cd "c:/Users/Gray Davis/my-project/web-apps/hyperframes"
npx hyperframes init test-onboarding
```

Add `.gitignore` for `node_modules/`, `*.mp4`, `.cache/`.

### Task 6: Verify HyperFrames Studio (preview) loads

```bash
cd web-apps/hyperframes/test-onboarding
npx hyperframes preview
```

Opens the Studio in browser. Quick visual confirm; close server.

### Task 7: Build `python-scripts/multicam-mirror/` MVP

**Files:**
- `main.py` — CLI entry: `python main.py <a_cam.mp4> <b_cam.mp4> <video_use_edl.json> [--out-dir DIR]`
- `sync.py` — `compute_offset(a_audio_path, b_audio_path) -> float` via audalign
- `render.py` — `extract_segments(video_path, ranges, out_dir)` via ffmpeg
- `requirements.txt` — `audalign`, `numpy` (audalign already pulls these but explicit is fine)
- `README.md`

**Algorithm:**
1. Extract audio from A-cam and B-cam via ffmpeg (`-vn -ac 1 -ar 48000`)
2. Run `audalign` to get the A→B offset in seconds
3. Read `video_use_edl.json` (the EDL produced by video-use)
4. For every cut range `[start, end]` in the EDL: produce `[start + offset, end + offset]` for B-cam
5. Use ffmpeg to extract per-segment clips from B-cam at the shifted ranges
6. Concat the B-cam segments into `final_b.mp4`
7. Output: `final_a.mp4` (already produced by video-use) + `final_b.mp4` (multicam-mirror's output) — same length, same cut points, drop both onto a Premiere multicam timeline.

### Task 8: Validation — run the full pipeline on the onboarding video

1. Open Claude Code in the folder containing the A-cam + B-cam footage.
2. Prompt Claude: `"edit this onboarding video using video-use"` — pointing at the A-cam clip.
3. video-use produces `final_a.mp4` + an `edl.json`.
4. Run `python python-scripts/multicam-mirror/main.py a_cam.mp4 b_cam.mp4 path/to/edl.json --out-dir ./out/`.
5. Get `final_b.mp4`.
6. Drop both into Premiere/Resolve as a multicam sequence — verify they're frame-locked.

### Task 9: Update CLAUDE.md, priorities.md, decisions/log.md

- `CLAUDE.md`: 15 → 16 python-scripts, add hyperframes web-app, add video-use to Custom Skills section.
- `context/priorities.md`: refresh `_Last updated_` note.
- `decisions/log.md`: append decision (adoption + multicam-mirror design + why we didn't extend content-pipeline yet).

### Task 10: Add memory entries

- `reference_video_use_skill.md` — what it is, where it lives, how Claude Code triggers it
- `reference_hyperframes.md` — what it is, where projects live, npx commands
- `reference_multicam_mirror.md` — purpose, CLI, audalign-based sync
- Update `MEMORY.md` index

---

## Validation Criteria

- [ ] `uv --version` returns a version
- [ ] `~/.claude/skills/video-use/.venv/` exists and `uv sync` completed without errors
- [ ] `~/.claude/skills/video-use/.env` contains a real `ELEVENLABS_API_KEY`
- [ ] `npx hyperframes doctor` reports all green
- [ ] `web-apps/hyperframes/test-onboarding/` is scaffolded and `npx hyperframes preview` opens Studio
- [ ] `python python-scripts/multicam-mirror/main.py --help` shows usage
- [ ] Onboarding A-cam edits successfully via video-use → produces `final_a.mp4` + `edl.json`
- [ ] `multicam-mirror` produces a frame-locked `final_b.mp4`
- [ ] CLAUDE.md, priorities.md, decisions/log.md, and memory entries all updated
- [ ] `git status` clean after final commit

---

## Risks / Watch-Outs

- **uv install on Windows** can be finicky. Fallback: `pip install uv` per the task above (we picked the simpler path).
- **video-use's `uv sync`** may pull macOS-specific deps. If errors appear, we either patch the lock file or install missing deps manually.
- **`audalign` on Windows** may need C build tools. Fallback: pure scipy cross-correlation (~30 lines, no external deps).
- **ElevenLabs API cost.** Scribe is ~$0.40/hour of audio. Onboarding video might be 5–15 min → $0.03–$0.10 per pass. Cheap.
- **Token cost.** Per Nate's video, ~238k tokens for a 30s clip with motion graphics. The onboarding video could be 5+ min → potentially 2M+ tokens. Caching matters; first runs are expensive.
- **HyperFrames Studio port collision.** Default 3000 may clash with Analytical's frontend; if so, set the port explicitly or stop other servers.

---

## Out of Scope (this plan)

- Extending `content-pipeline` with `--full-edit` flag — wait until video-use proves itself on 5 real shots.
- Building a Graydient Media `DESIGN.md` for HyperFrames brand spec — Day 30+ work.
- Wrapping video-use in a Python CLI — it's already an agent skill; let Claude Code drive it.
- Multicam beyond 2 cameras — A + B is the use case; if Gray adds C-cam later, generalize then.
