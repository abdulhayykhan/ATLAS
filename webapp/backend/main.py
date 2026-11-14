"""ATLAS — FastAPI backend.

Serves the ATLAS science outputs (built by src/preprocess_*.py + src/model.py)
as a JSON API, plus the vanilla HTML/CSS/JS frontend in ../frontend and the
generated images in ../../outputs.

Run from the repository root:
    pip install -r webapp/backend/requirements.txt
    uvicorn webapp.backend.main:app --reload --port 8000
or simply:
    bash webapp/run.sh

Design notes:
  * The backend is read-only and stateless; all science is precomputed in
    outputs/*.csv by the pipeline. This service only shapes, filters and
    re-weights it.
  * Re-weighting (Guide Objective 6) mirrors src/app.py exactly:
    D = sqrt( sum(w_k * dist_k^2) / sum(w over pillars with data) ),
    score = 100 * exp(-D). With the default weights, the stored official
    scores are returned untouched so the API can never drift from the
    published ranking.
"""
import math
import os
from functools import lru_cache

import pandas as pd
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


def _clean(v):
    """Make a value JSON-safe: NaN -> None, numpy scalars -> Python scalars."""
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    if hasattr(v, "item"):
        return v.item()
    return v


def _rows(df):
    return [{k: _clean(v) for k, v in row.items()} for row in df.to_dict("records")]


@lru_cache(maxsize=1)
def _load():
    def read(name):
        p = os.path.join(OUTPUTS, name)
        if not os.path.exists(p):
            raise RuntimeError(f"Missing pipeline output: outputs/{name} — run the src/ pipeline first.")
        return pd.read_csv(p)
    return read("moon_profiles.csv"), read("earth_profiles.csv"), read("scores_ranking.csv"), read("mars_profiles.csv")


def _merged_scores():
    _, earth, scores, _ = _load()
    keep = ["site_name", "country", "lat", "lon", "site_type", "terrain_type",
            "slope_mean_deg", "pct_slope_under_10deg", "temp_mean_c",
            "temp_seasonal_range_c", "sand_pct", "clay_pct", "coarse_fragments_pct"]
    if "regime" in earth.columns:
        keep.append("regime")
    return scores.merge(earth[keep], left_on="earth_site", right_on="site_name", how="left")


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
    top = s[s["rank_for_base"] == 1].sort_values("moon_base")
    return _rows(top[["moon_base", "earth_site", "country", "analog_score", "lat", "lon"]])


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
    if base not in set(moon["base_name"]):
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

    s = _merged_scores()
    sub = s[s["moon_base"] == base].copy()
    if is_default:
        sub["display_score"] = sub["analog_score"]
        sub["display_rank"] = sub["rank_for_base"]
    else:
        sub["display_score"] = sub.apply(lambda r: _rescore(r, weights), axis=1)
        sub["display_rank"] = sub["display_score"].rank(ascending=False, method="min").astype(int)
        sub = sub.sort_values("display_rank")
    cols = ["display_rank", "earth_site", "country", "lat", "lon", "site_type", "terrain_type",
            "display_score", "analog_score", "slope_mean_deg", "pct_slope_under_10deg",
            "temp_mean_c", "temp_seasonal_range_c", "sand_pct", "clay_pct",
            "coarse_fragments_pct", "dist_slope", "dist_flat", "dist_temperature",
            "dist_relief", "dist_soil"]
    if "regime" in sub.columns:
        cols.insert(7, "regime")
    return {"base": base, "preset": preset, "weights": weights,
            "official": is_default, "results": _rows(sub[cols])}


@app.get("/api/compare")
def compare(base: str = Query(...), site: str = Query(...)):
    moon, earth, scores, _ = _load()
    b = moon[moon["base_name"] == base]
    e = earth[earth["site_name"] == site]
    s = scores[(scores["moon_base"] == base) & (scores["earth_site"] == site)]
    if b.empty or e.empty or s.empty:
        raise HTTPException(404, "Unknown base/site pair")
    b, e, s = b.iloc[0], e.iloc[0], s.iloc[0]
    radar = {k: (None if pd.isna(s[f"dist_{k}"]) else round(1 - float(s[f"dist_{k}"]), 3))
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
    ref = m.iloc[0]
    e = earth.copy()
    e["slope_gap"] = (e["slope_mean_deg"] - float(ref["slope_mean_deg"])).abs()
    closest = e.nsmallest(3, "slope_gap")[["site_name", "country", "slope_mean_deg", "pct_slope_under_10deg"]]
    return {"region": _rows(m)[0], "closest_earth_sites": _rows(closest)}


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
