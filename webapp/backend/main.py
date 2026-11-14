"""ATLAS — FastAPI backend.

Serves the ATLAS science outputs (built by src/preprocess_*.py + src/model.py)
as a JSON API, plus the vanilla HTML/CSS/JS frontend in ../frontend and the
generated images in ../../outputs.

Run from the repository root:
    pip install -r webapp/backend/requirements.txt
    uvicorn webapp.backend.main:app --reload --port 8000
or simply:
    bash webapp/run.sh

Deployment: this app is also the Vercel entrypoint — the repo-root
pyproject.toml sets [tool.vercel] entrypoint = "webapp.backend.main:app",
so Vercel runs it as-is and routes every request to it (see docs/12).

Design notes:
  * The backend is read-only and stateless; all science is precomputed in
    outputs/*.csv by the pipeline. This service only shapes, filters and
    re-weights it.
  * The CSVs are tiny, so they are read with the standard-library csv module
    — no pandas/numpy. That keeps the serverless bundle small and the cold
    starts fast on hosts like Vercel.
  * Re-weighting (Guide Objective 6) mirrors src/app.py exactly:
    D = sqrt( sum(w_k * dist_k^2) / sum(w over pillars with data) ),
    score = 100 * exp(-D). With the default weights, the stored official
    scores are returned untouched so the API can never drift from the
    published ranking.
"""
import csv
import math
import os
import re
from functools import lru_cache

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUTPUTS = os.path.join(ROOT, "outputs")
FRONTEND = os.path.join(ROOT, "webapp", "frontend")

DEFAULT_WEIGHTS = {"slope": 30.0, "flat": 20.0, "temperature": 20.0, "soil": 15.0, "relief": 15.0}
PILLARS = ["slope", "flat", "temperature", "soil", "relief"]
PRESETS = {
    "balanced": DEFAULT_WEIGHTS,
    "rover": {"slope": 45.0, "flat": 35.0, "temperature": 5.0, "soil": 5.0, "relief": 10.0},
    "habitat": {"slope": 10.0, "flat": 35.0, "temperature": 20.0, "soil": 10.0, "relief": 25.0},
    "isru": {"slope": 15.0, "flat": 10.0, "temperature": 25.0, "soil": 35.0, "relief": 15.0},
}

app = FastAPI(title="ATLAS API", description="Analog Terrain & Lunar Alignment System — Team Binary Knights",
              version="2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"])


_INT_RE = re.compile(r"^-?\d+$")


def _coerce(raw):
    """CSV field -> Python value: '' -> None, ints -> int, decimals -> float,
    everything else stays a string. Mirrors what pd.read_csv produced."""
    if raw is None:
        return None
    s = raw.strip()
    if s == "" or s.lower() == "nan":
        return None
    if _INT_RE.match(s):
        return int(s)
    try:
        f = float(s)
        return None if math.isnan(f) else f
    except ValueError:
        return raw


def _read_csv(name):
    p = os.path.join(OUTPUTS, name)
    if not os.path.exists(p):
        raise RuntimeError(f"Missing pipeline output: outputs/{name} — run the src/ pipeline first.")
    with open(p, newline="", encoding="utf-8") as fh:
        return [{k: _coerce(v) for k, v in row.items()} for row in csv.DictReader(fh)]


def _clean(v):
    """Make a value JSON-safe: NaN -> None."""
    if isinstance(v, float) and math.isnan(v):
        return None
    return v


def _rows(rows):
    return [{k: _clean(v) for k, v in r.items()} for r in rows]


@lru_cache(maxsize=1)
def _load():
    return (_read_csv("moon_profiles.csv"), _read_csv("earth_profiles.csv"),
            _read_csv("scores_ranking.csv"), _read_csv("mars_profiles.csv"))


def _merged_scores():
    _, earth, scores, _ = _load()
    keep = ["site_name", "country", "lat", "lon", "site_type", "terrain_type",
            "slope_mean_deg", "pct_slope_under_10deg", "temp_mean_c",
            "temp_seasonal_range_c", "sand_pct", "clay_pct", "coarse_fragments_pct"]
    if earth and "regime" in earth[0]:
        keep.append("regime")
    by_name = {e["site_name"]: e for e in earth}
    merged = []
    for s in scores:
        row = dict(s)
        src = by_name.get(s["earth_site"], {})
        for k in keep:
            row[k] = src.get(k)
        merged.append(row)
    return merged


def _rescore(row, weights):
    num = den = 0.0
    for k in PILLARS:
        d = row.get(f"dist_{k}")
        if d is not None and not (isinstance(d, float) and math.isnan(d)) and weights[k] > 0:
            num += weights[k] * float(d) ** 2
            den += weights[k]
    if den == 0:
        return None
    return round(100.0 * math.exp(-math.sqrt(num / den)), 1)


# --------------------------------------------------------------------------- API
@app.get("/api/health")
def health():
    moon, earth, scores, _ = _load()
    return {"status": "ok", "moon_bases": len(moon), "earth_sites": len(earth), "score_rows": len(scores)}


@app.get("/api/moon-bases")
def moon_bases():
    moon, _, _, _ = _load()
    out = _rows(moon)
    for r in out:
        slug = r["base_name"].replace(" ", "").lower()
        r["hillshade_url"] = f"/outputs/hillshade_{slug}.png"
    return out


@app.get("/api/earth-sites")
def earth_sites():
    _, earth, _, _ = _load()
    return _rows(earth)


@app.get("/api/winners")
def winners():
    """Top-1 novel match per base under the official (balanced) weights."""
    s = _merged_scores()
    top = sorted((r for r in s if r["rank_for_base"] == 1), key=lambda r: r["moon_base"])
    cols = ["moon_base", "earth_site", "country", "analog_score", "lat", "lon"]
    return [{c: _clean(r.get(c)) for c in cols} for r in top]


@app.get("/api/rankings")
def rankings(base: str = Query(...),
             preset: str = Query("balanced"),
             slope: float = Query(None), flat: float = Query(None),
             temperature: float = Query(None), soil: float = Query(None),
             relief: float = Query(None)):
    """Ranking of all Earth sites for one Moon base.

    Either a named preset or explicit pillar weights (0-100 each). With the
    balanced preset and no explicit weights, the stored official scores and
    ranks are returned verbatim.
    """
    moon, _, _, _ = _load()
    if base not in {r["base_name"] for r in moon}:
        raise HTTPException(404, f"Unknown base '{base}'")
    if preset not in PRESETS:
        raise HTTPException(400, f"Unknown preset '{preset}' (choose from {sorted(PRESETS)})")
    weights = dict(PRESETS[preset])
    custom = False
    for k, v in [("slope", slope), ("flat", flat), ("temperature", temperature),
                 ("soil", soil), ("relief", relief)]:
        if v is not None:
            weights[k] = float(v)
            custom = True
    is_default = (not custom) and preset == "balanced"

    sub = [dict(r) for r in _merged_scores() if r["moon_base"] == base]
    if is_default:
        for r in sub:
            r["display_score"] = r["analog_score"]
            r["display_rank"] = r["rank_for_base"]
    else:
        for r in sub:
            r["display_score"] = _rescore(r, weights)
        scored = [r["display_score"] for r in sub if r["display_score"] is not None]
        for r in sub:
            s = r["display_score"]
            r["display_rank"] = None if s is None else 1 + sum(1 for x in scored if x > s)
        sub.sort(key=lambda r: (r["display_rank"] is None, r["display_rank"] or 0))
    cols = ["display_rank", "earth_site", "country", "lat", "lon", "site_type", "terrain_type",
            "display_score", "analog_score", "slope_mean_deg", "pct_slope_under_10deg",
            "temp_mean_c", "temp_seasonal_range_c", "sand_pct", "clay_pct",
            "coarse_fragments_pct", "dist_slope", "dist_flat", "dist_temperature",
            "dist_relief", "dist_soil"]
    if sub and "regime" in sub[0]:
        cols.insert(7, "regime")
    return {"base": base, "preset": preset, "weights": weights,
            "official": is_default,
            "results": [{c: _clean(r.get(c)) for c in cols} for r in sub]}


@app.get("/api/compare")
def compare(base: str = Query(...), site: str = Query(...)):
    moon, earth, scores, _ = _load()
    b = next((r for r in moon if r["base_name"] == base), None)
    e = next((r for r in earth if r["site_name"] == site), None)
    s = next((r for r in scores if r["moon_base"] == base and r["earth_site"] == site), None)
    if b is None or e is None or s is None:
        raise HTTPException(404, "Unknown base/site pair")
    radar = {k: (None if s.get(f"dist_{k}") is None else round(1 - float(s[f"dist_{k}"]), 3))
             for k in PILLARS}
    return {
        "base": base, "site": site,
        "analog_score": _clean(s["analog_score"]), "rank_for_base": int(s["rank_for_base"]),
        "of_sites": int(len(earth)),
        "radar_similarity": radar,   # 1 = identical; soil None => pillar not scored (drawn neutral)
        "moon": {"slope_mean_deg": _clean(b["slope_mean_deg"]),
                 "pct_slope_under_10deg": _clean(b["pct_slope_under_10deg"]),
                 "temp_seasonal_mean_c": _clean(b["temp_seasonal_mean_c"]),
                 "elev_std_m": _clean(b["elev_std_m"]), "elev_mean_m": _clean(b["elev_mean_m"]),
                 "psr_pct": _clean(b["psr_pct"]), "sun_visibility_pct": _clean(b["sun_visibility_pct"]),
                 "earth_visibility_pct": _clean(b["earth_visibility_pct"])},
        "earth": {"slope_mean_deg": _clean(e["slope_mean_deg"]),
                  "pct_slope_under_10deg": _clean(e["pct_slope_under_10deg"]),
                  "temp_mean_c": _clean(e["temp_mean_c"]),
                  "elev_std_m": _clean(e["elev_std_m"]), "elev_mean_m": _clean(e["elev_mean_m"]),
                  "temp_seasonal_range_c": _clean(e["temp_seasonal_range_c"]),
                  "analog_note": _clean(e.get("analog_note"))},
    }


@app.get("/api/mars")
def mars():
    _, earth, _, m = _load()
    ref = m[0]
    ranked = sorted(earth, key=lambda e: abs(e["slope_mean_deg"] - float(ref["slope_mean_deg"])))
    cols = ["site_name", "country", "slope_mean_deg", "pct_slope_under_10deg"]
    closest = [{c: _clean(r.get(c)) for c in cols} for r in ranked[:3]]
    return {"region": _rows(m)[0], "closest_earth_sites": closest}


@app.get("/api/methodology", response_class=HTMLResponse)
def methodology():
    p = os.path.join(OUTPUTS, "methodology.md")
    if not os.path.exists(p):
        raise HTTPException(404, "methodology.md not found in outputs/")
    try:
        import markdown
        html = markdown.markdown(open(p).read(), extensions=["tables", "fenced_code"])
    except ImportError:
        html = "<pre>" + open(p).read().replace("<", "&lt;") + "</pre>"
    return HTMLResponse(html)


@app.get("/api/downloads/{name}")
def downloads(name: str):
    allowed = {"moon": "moon_profiles.csv", "earth": "earth_profiles.csv", "scores": "scores_ranking.csv"}
    if name not in allowed:
        raise HTTPException(404, "Unknown download")
    p = os.path.join(OUTPUTS, allowed[name])
    from fastapi.responses import FileResponse
    return FileResponse(p, filename=f"atlas_{allowed[name]}", media_type="text/csv")


# ------------------------------------------------------------------ static web
if os.path.isdir(OUTPUTS):
    app.mount("/outputs", StaticFiles(directory=OUTPUTS), name="outputs")
if os.path.isdir(FRONTEND):
    app.mount("/", StaticFiles(directory=FRONTEND, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
