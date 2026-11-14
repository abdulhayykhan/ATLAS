# 12 — Deployment & Submission

*Status: the complete codebase is on GitHub. This document records the push, how to deploy both apps, and the exact Space Apps submission steps that remain.*

## 12.1 Source of truth — GitHub (pushed 14 November 2026)

- **Repository:** https://github.com/abdulhayykhan/ATLAS (public)
- **Branch:** `main`
- **Push record:** the remote moved from the team's initial commit `d65a712` ("init ATLAS with docs and dataset metadata") to the complete build in one push on 14 Nov 2026, authorised by a team collaborator via GitHub's device sign-in flow.
- **Files on GitHub:** 55 (verified through the GitHub API after the push — includes `src/`, `outputs/`, `docs/00–12`, `webapp/`, `scripts/`, README, DATA_DOCUMENTATION, DOCUMENTATION).
- **Commit chain on `main`:**

| Commit | Content |
|---|---|
| `d65a712` | Team init — README, DATA_DOCUMENTATION, label files |
| `1212ff2` | Complete pipeline: 4 Moon bases (both poles), scoring, Mars, Streamlit app |
| `ead7a59` | Guide-#09 discovery run: 14 novel sites, classics excluded, presets, clustering |
| `e5ee866` | Documentation set docs/00–10 + DOCUMENTATION.md index |
| `54cba0b` | Full-stack web app: FastAPI backend + responsive vanilla frontend |
| `79e9b24` | Documentation update: docs/12 deployment & submission guide, README fixes |
| *(cleanup)* | Removed the init commit's `data/moon/` label & saved-web-page downloads (11 files) |

- **Cleanup note (14 Nov 2026):** the initial commit had committed a partial set of PDS label files and saved Lunar ODE web pages under `data/moon/`. They were removed from the repository: the set was south-pole only (the pipeline uses both poles), two labels described products the project does not use, and every label in any case travels with its PDS product download. `.gitignore` now excludes the whole local `data/` tree, which `scripts/download_data.sh` recreates on any machine. Nothing in `src/` or `webapp/` reads the committed copies — both apps run from `outputs/` alone.

- The raw rasters (~2.3 GB) are **not** in the repo by design — `.gitignore` excludes `data/`. Anyone can rebuild them with `scripts/download_data.sh` (see `09_reproduction_guide.md`). The apps need only the committed `outputs/` folder (~5 MB).

## 12.2 Deploy option A — Streamlit app (fastest)

1. Go to https://share.streamlit.io and sign in with a GitHub account that can see the repo.
2. **New app** → repository `abdulhayykhan/ATLAS`, branch `main`, main file path `src/app.py`.
3. Deploy. The app installs `requirements.txt` and reads only `outputs/` — no data download, no secrets, no API keys.
4. Copy the resulting `*.streamlit.app` URL for the submission form.
5. Sanity-check after deploy: all six pages open; the Analog Finder map renders; rankings show Mount Erebus #1 for de Gerlache (72.1).

## 12.3 Deploy option B — FastAPI web app

The web app is a standard ASGI service; any Python host works.

**Local / VPS:**
```bash
git clone https://github.com/abdulhayykhan/ATLAS.git
cd ATLAS
bash webapp/run.sh 8000        # http://localhost:8000
```

**Render / Railway / similar (no Dockerfile needed):**
- Build command: `pip install -r webapp/backend/requirements.txt`
- Start command: `uvicorn webapp.backend.main:app --host 0.0.0.0 --port $PORT`
- Root directory: repository root. No environment variables, no secrets.

**Hugging Face Spaces (Docker SDK) also works:** point the Space at this repo with the same uvicorn start command on port 7860.

Sanity-check after deploy: `GET /api/health` returns `{"status": "ok", "moon_bases": 4, "earth_sites": 14, "score_rows": 56}`; open the site on a phone — the ranking table must collapse into stacked cards and the menu into the hamburger button.

**Which one to submit?** Both links can go in the project. If only one: the web app — it is the more polished, fully responsive interface and demonstrates the full-stack build. The Streamlit app remains the analysis workbench.

## 12.4 Demo video (2 minutes)

- Follow the shot-by-shot script kept with the team (`ATLAS_demo_script.md`): problem → Moon bases → discovery rankings → live re-weighting with a mission preset → Compare radar → Mars page → methodology/honesty note.
- Record the **deployed** app (not localhost) so judges see the real thing; include one phone-width shot of the responsive UI.
- Upload to YouTube as **Unlisted**, title: `ATLAS — Analog Terrain & Lunar Alignment System | NASA Space Apps 2026`.

## 12.5 Space Apps portal submission checklist

Project fields (portal: https://www.spaceappschallenge.org/2026/ — sign in, open the team **Binary Knights**, create/edit the project):

| Field | Value |
|---|---|
| Project name | **ATLAS — Analog Terrain & Lunar Alignment System** |
| Challenge | Identify Earth Locations that Analog the Permanent Moon Base Locations and Mars |
| Summary (short) | ATLAS profiles NASA's four permanent Moon base sites (Peary, Shackleton, de Gerlache, Amundsen) from LRO LOLA, Diviner and illumination data, then discovers and ranks 14 previously uncatalogued Earth analog sites across six terrain types with a transparent weighted dissimilarity model, live mission re-weighting, and a Mars (Jezero) extension. |
| GitHub / source link | https://github.com/abdulhayykhan/ATLAS |
| Demo link | the deployed app URL from §12.2 or §12.3 |
| Video link | the unlisted YouTube URL from §12.4 |
| Resources used | NASA PDS / PGDA (LOLA, Diviner, Mazarico illumination), Copernicus DEM GLO-30, NASA POWER, SoilGrids 2.0, MGS MOLA — full citations in `DATA_DOCUMENTATION.md` |
| Details to mention | Novelty rule (famous analogs excluded by design, used only as a validation control); both lunar poles covered; honest limitations (temperature gap, resolution mismatch) stated in `outputs/methodology.md` and `docs/08_validation_and_qa.md` |

**Deadline: Sunday 15 November 2026, 23:59 PKT.** Submit early — the portal slows down near the deadline — and screenshot the confirmation page.

## 12.6 After submission

- Do not rewrite the repo history; small additive commits are fine, but keep `outputs/` consistent with the submitted claims.
- If judges ask how a number was produced, the answer path is: `docs/09_reproduction_guide.md` (commands + acceptance numbers) → `docs/08_validation_and_qa.md` (audit trail) → the specific phase document.
- Local-event (Cedar College Karachi) pitch timing is arranged by the local organisers — confirm the slot with them directly; it is not set by the global portal.
