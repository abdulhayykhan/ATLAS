/* ATLAS frontend — vanilla JS. Talks only to the FastAPI backend (/api/*). */
"use strict";

const $ = (s, el) => (el || document).querySelector(s);
const $$ = (s, el) => Array.from((el || document).querySelectorAll(s));
const fmt = (v, d = 1) => (v === null || v === undefined || Number.isNaN(v)) ? "—" : Number(v).toFixed(d);
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));

async function api(path) {
  const r = await fetch(path);
  if (!r.ok) throw new Error(`${path} -> ${r.status}`);
  return r.json();
}

/* ------------------------------------------------------------------ state */
const state = {
  bases: [], sites: [], winners: [],
  finder: { base: null, preset: "balanced", weights: null, map: null, layer: null, loaded: false },
  compareLoaded: false, marsLoaded: false, methodologyLoaded: false,
};
const PRESET_WEIGHTS = {
  balanced: { slope: 30, flat: 20, temperature: 20, soil: 15, relief: 15 },
  rover:    { slope: 45, flat: 35, temperature: 5,  soil: 5,  relief: 10 },
  habitat:  { slope: 10, flat: 35, temperature: 20, soil: 10, relief: 25 },
  isru:     { slope: 15, flat: 10, temperature: 25, soil: 35, relief: 15 },
};
const PILLAR_LABELS = { slope: "Slope", flat: "Flat area", temperature: "Temperature", soil: "Soil proxy", relief: "Relief" };

/* -------------------------------------------------------------- navigation */
function showPage(name) {
  $$(".page").forEach((p) => p.classList.toggle("active", p.id === `page-${name}`));
  $$(".main-nav a").forEach((a) => a.classList.toggle("active", a.dataset.nav === name));
  $("#mainNav").classList.remove("open");
  $("#navToggle").setAttribute("aria-expanded", "false");
  window.scrollTo({ top: 0 });
  if (name === "finder") initFinder();
  if (name === "compare") initCompare();
  if (name === "mars") initMars();
  if (name === "methodology") initMethodology();
  if (state.finder.map && name === "finder") setTimeout(() => state.finder.map.invalidateSize(), 60);
}
function route() {
  const name = (location.hash || "#overview").slice(1);
  const valid = ["overview", "bases", "finder", "compare", "mars", "methodology"];
  showPage(valid.includes(name) ? name : "overview");
}
document.addEventListener("click", (e) => {
  const a = e.target.closest("[data-nav]");
  if (a) { /* hash change handles it */ }
});
$("#navToggle").addEventListener("click", () => {
  const nav = $("#mainNav");
  nav.classList.toggle("open");
  $("#navToggle").setAttribute("aria-expanded", nav.classList.contains("open"));
});
window.addEventListener("hashchange", route);

/* ---------------------------------------------------------------- overview */
async function loadOverview() {
  try {
    state.bases = await api("/api/moon-bases");
    state.winners = await api("/api/winners");
    $("#baseChips").innerHTML = state.bases.map((b) => `
      <div class="card base-chip">
        <h3>${esc(b.base_name)}</h3>
        <span class="pole ${b.pole === "S" ? "south" : ""}">${b.pole === "N" ? "NORTH POLE" : "SOUTH POLE"}</span>
        <div class="metric-line"><span>Coordinates</span><b>${fmt(b.lat, 2)}°, ${fmt(b.lon, 2)}°</b></div>
        <div class="metric-line"><span>Sun visibility</span><b>${fmt(b.sun_visibility_pct)}%</b></div>
        <div class="metric-line"><span>Earth visibility</span><b>${fmt(b.earth_visibility_pct)}%</b></div>
        <div class="metric-line"><span>Permanently shadowed</span><b>${fmt(b.psr_pct)}%</b></div>
        <div class="metric-line"><span>Seasonal mean temp</span><b>${fmt(b.temp_seasonal_mean_c, 0)} °C</b></div>
      </div>`).join("");
    const byName = Object.fromEntries(state.winners.map((w) => [w.moon_base, w]));
    $("#winnerCards").innerHTML = state.bases.map((b) => {
      const w = byName[b.base_name]; if (!w) return "";
      return `<div class="card winner-card">
        <div class="for-base">Best NEW match for ${esc(b.base_name)}</div>
        <div class="winners-name">${esc(w.earth_site)}</div>
        <div>${esc(w.country)}</div>
        <div class="winner-score">${fmt(w.analog_score)} <small>/ 100 analog score</small></div>
      </div>`;
    }).join("");
    renderBaseProfiles();
  } catch (err) {
    $("#baseChips").innerHTML = `<p class="loading">Could not load data (${esc(err.message)}). Is the backend running?</p>`;
  }
}

function renderBaseProfiles() {
  const rows = [
    ["Mean elevation", "elev_mean_m", " m", 1], ["Relief — elevation std", "elev_std_m", " m", 1],
    ["Mean slope", "slope_mean_deg", "°", 2], ["Area flatter than 10°", "pct_slope_under_10deg", "%", 1],
    ["Surface roughness (mean)", "roughness_mean_m", " m", 2],
    ["Permanently shadowed area", "psr_pct", "%", 1],
    ["Sun visibility", "sun_visibility_pct", "%", 1], ["Earth visibility", "earth_visibility_pct", "%", 1],
    ["Mean temperature (seasonal)", "temp_seasonal_mean_c", " °C", 1],
    ["Winter cold level (1st pct)", "temp_winter_cold_p1_k", " K", 1],
  ];
  $("#baseProfiles").innerHTML = state.bases.map((b) => `
    <article class="base-profile">
      <div>
        <h3>${esc(b.base_name)} <small style="color:var(--muted);font-size:.85rem">
          ${fmt(b.lat, 2)}°, ${fmt(b.lon, 2)}° · ${fmt(b.crater_diameter_km, 0)} km crater · ${fmt(b.roi_radius_km, 0)} km study area</small></h3>
        ${rows.map(([label, key, unit, d]) =>
          `<div class="metric-line"><span>${label}</span><b>${fmt(b[key], d)}${unit}</b></div>`).join("")}
        <p class="sources">Sources: ${esc(b.sources)}</p>
      </div>
      <figure>
        <img src="${esc(b.hillshade_url)}" alt="Shaded relief map of ${esc(b.base_name)} crater" loading="lazy">
        <figcaption>Shaded relief (LOLA DEM) — ${esc(b.base_name)}</figcaption>
      </figure>
    </article>`).join("") +
    `<div class="note-box"><strong>Peary is at the North Pole</strong> — ATLAS processes both poles:
     LDEM/LDSM/LDRM 80N–75N grids and the Diviner <em>poln</em> temperature tables are included.
     The north grids are stored with the opposite row handedness to the south — ATLAS's mapping was
     validated against named craters at both poles.</div>`;
}

/* ----------------------------------------------------------------- finder */
function buildSliders(weights) {
  $("#weightSliders").innerHTML = Object.keys(PILLAR_LABELS).map((k) => `
    <div class="slider-row">
      <label for="w-${k}">${PILLAR_LABELS[k]} <output id="wo-${k}">${weights[k]}</output></label>
      <input type="range" id="w-${k}" min="0" max="60" step="1" value="${weights[k]}" data-pillar="${k}">
    </div>`).join("");
  $$("#weightSliders input[type=range]").forEach((inp) => {
    inp.addEventListener("input", () => {
      $(`#wo-${inp.dataset.pillar}`).textContent = inp.value;
      state.finder.weights = currentSliderWeights();
      debounceRanking(true);
    });
  });
}
function currentSliderWeights() {
  const w = {};
  $$("#weightSliders input[type=range]").forEach((i) => (w[i.dataset.pillar] = Number(i.value)));
  return w;
}
let rankTimer = null;
function debounceRanking(custom) {
  clearTimeout(rankTimer);
  rankTimer = setTimeout(() => loadRanking(custom), 180);
}

async function initFinder() {
  if (!state.sites.length) {
    try { state.sites = await api("/api/earth-sites"); } catch (e) { /* notes degrade gracefully */ }
  }
  if (state.finder.loaded) { if (state.finder.map) refreshMap(await lastRanking()); return; }
  state.finder.loaded = true;
  const sel = $("#finderBase");
  sel.innerHTML = state.bases.map((b) => `<option>${esc(b.base_name)}</option>`).join("");
  state.finder.base = sel.value;
  sel.addEventListener("change", () => { state.finder.base = sel.value; loadRanking(false); });
  $$("#presetChips .chip").forEach((chip) => chip.addEventListener("click", () => {
    $$("#presetChips .chip").forEach((c) => c.classList.toggle("active", c === chip));
    state.finder.preset = chip.dataset.preset;
    state.finder.weights = null;
    buildSliders(PRESET_WEIGHTS[state.finder.preset]);
    loadRanking(false);
  }));
  buildSliders(PRESET_WEIGHTS.balanced);
  initMap();
  loadRanking(false);
}

let _lastRanking = null;
async function lastRanking() { return _lastRanking; }

function initMap() {
  const box = $("#finderMap");
  if (typeof L === "undefined") { box.innerHTML = `<p class="loading">Map library unavailable offline — the ranking table below carries the same data.</p>`; return; }
  state.finder.map = L.map("finderMap", { worldCopyJump: true }).setView([18, 10], 2);
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    { attribution: "© OpenStreetMap contributors", maxZoom: 10 }).addTo(state.finder.map);
  state.finder.layer = L.layerGroup().addTo(state.finder.map);
}

async function loadRanking(customWeights) {
  const base = state.finder.base || $("#finderBase").value;
  const params = new URLSearchParams({ base, preset: state.finder.preset });
  if (customWeights && state.finder.weights) {
    for (const k of Object.keys(PILLAR_LABELS)) params.set(k, state.finder.weights[k]);
  }
  try {
    const data = await api(`/api/rankings?${params}`);
    _lastRanking = data;
    renderRanking(data);
    refreshMap(data);
  } catch (err) {
    $("#rankingTable tbody").innerHTML = `<tr><td colspan="9">Failed to load (${esc(err.message)})</td></tr>`;
  }
}

function renderRanking(data) {
  const banner = $("#customBanner");
  if (data.official) { banner.classList.add("hidden"); }
  else {
    banner.classList.remove("hidden");
    banner.textContent = `Custom ranking — weights: ` + Object.keys(PILLAR_LABELS)
      .map((k) => `${PILLAR_LABELS[k]} ${data.weights[k]}`).join(" · ") +
      `. The official published ranking uses the Balanced profile.`;
  }
  const soil = (r) => (r.sand_pct === null) ? "no data" :
    `${fmt(r.sand_pct, 0)}/${fmt(r.clay_pct, 0)}/${fmt(r.coarse_fragments_pct, 0)}`;
  $("#rankingTable tbody").innerHTML = data.results.map((r) => `
    <tr class="${r.display_rank === 1 ? "rank1" : ""}">
      <td><b>${r.display_rank}</b></td>
      <td><b>${esc(r.earth_site)}</b><br><small style="color:var(--muted)">${esc(r.country)}</small></td>
      <td>${esc(r.terrain_type)}<br><small style="color:var(--muted)">${esc(r.regime || "")}</small></td>
      <td><span class="score-pill">${fmt(r.display_score)}</span></td>
      <td>${fmt(r.slope_mean_deg, 2)}</td><td>${fmt(r.pct_slope_under_10deg)}</td>
      <td>${fmt(r.temp_mean_c)}</td><td>${fmt(r.temp_seasonal_range_c)}</td><td>${soil(r)}</td>
    </tr>`).join("");
  $("#rankCards").innerHTML = data.results.map((r) => `
    <div class="rank-card">
      <header><h4>#${r.display_rank} ${esc(r.earth_site)}</h4><span class="rc-score">${fmt(r.display_score)}</span></header>
      <div class="rc-meta">${esc(r.country)} · ${esc(r.terrain_type)} · slope ${fmt(r.slope_mean_deg, 2)}° ·
      flat ${fmt(r.pct_slope_under_10deg)}% · temp ${fmt(r.temp_mean_c)} °C · seasonal ±${fmt(r.temp_seasonal_range_c)} °C</div>
    </div>`).join("");
  const notes = Object.fromEntries(state.sites.map((s) => [s.site_name, s]));
  $("#discoveryNotes").innerHTML = data.results.map((r) => {
    const s = notes[r.earth_site];
    return s ? `<p><b>#${r.display_rank} ${esc(r.earth_site)}</b> (${esc(s.country)}) — ${esc(s.analog_note || "")}</p>` : "";
  }).join("");
}

function refreshMap(data) {
  if (!state.finder.map || !data) return;
  state.finder.layer.clearLayers();
  data.results.forEach((r) => {
    const color = r.display_rank === 1 ? "#3ddc97" : r.display_rank <= 3 ? "#39c2ff" : "#8fa5cc";
    L.circleMarker([r.lat, r.lon], { radius: 8, color, weight: 2, fillColor: color, fillOpacity: 0.75 })
      .bindPopup(`<b>${esc(r.earth_site)}</b> (${esc(r.country)})<br>${esc(r.site_type || r.terrain_type)}<br>` +
                 `Analog Score: <b>${fmt(r.display_score)}</b><br>Slope: ${fmt(r.slope_mean_deg, 2)}° · Temp: ${fmt(r.temp_mean_c)} °C`)
      .addTo(state.finder.layer);
  });
}

/* ---------------------------------------------------------------- compare */
async function initCompare() {
  if (state.compareLoaded) return;
  state.compareLoaded = true;
  $("#cmpBase").innerHTML = state.bases.map((b) => `<option>${esc(b.base_name)}</option>`).join("");
  if (!state.sites.length) state.sites = await api("/api/earth-sites");
  $("#cmpSite").innerHTML = state.sites.map((s) => `<option>${esc(s.site_name)}</option>`).join("");
  const top = state.winners.find((w) => w.moon_base === $("#cmpBase").value);
  if (top) $("#cmpSite").value = top.earth_site;
  $("#cmpBase").addEventListener("change", loadCompare);
  $("#cmpSite").addEventListener("change", loadCompare);
  loadCompare();
}

async function loadCompare() {
  const base = $("#cmpBase").value, site = $("#cmpSite").value;
  try {
    const d = await api(`/api/compare?base=${encodeURIComponent(base)}&site=${encodeURIComponent(site)}`);
    $("#compareHead").innerHTML =
      `<span class="big-score">${fmt(d.analog_score)}</span>
       <span><b>${esc(site)}</b> for <b>${esc(base)}</b><br>
       <span style="color:var(--muted)">Rank #${d.rank_for_base} of ${d.of_sites} novel sites (official weights)</span></span>`;
    $("#cmpBaseName").textContent = base;
    $("#cmpSiteName").textContent = site;
    const rows = [
      ["Mean slope (°)", d.moon.slope_mean_deg, d.earth.slope_mean_deg, 2],
      ["Area flatter than 10° (%)", d.moon.pct_slope_under_10deg, d.earth.pct_slope_under_10deg, 1],
      ["Mean temperature (°C)", d.moon.temp_seasonal_mean_c, d.earth.temp_mean_c, 1],
      ["Relief — elevation std (m)", d.moon.elev_std_m, d.earth.elev_std_m, 1],
      ["Mean elevation (m)", d.moon.elev_mean_m, d.earth.elev_mean_m, 1],
    ];
    $("#compareTable tbody").innerHTML = rows.map(([l, m, e, dec]) =>
      `<tr><td>${l}</td><td><b>${fmt(m, dec)}</b></td><td><b>${fmt(e, dec)}</b></td></tr>`).join("") +
      (d.earth.analog_note ? `<tr><td colspan="3" style="white-space:normal;color:var(--muted)">
        <b style="color:var(--text)">Why this site is new:</b> ${esc(d.earth.analog_note)}</td></tr>` : "");
    drawRadar(d);
  } catch (err) {
    $("#compareHead").innerHTML = `<p class="loading">Failed to load (${esc(err.message)})</p>`;
  }
}

function drawRadar(d) {
  const keys = ["slope", "flat", "temperature", "relief", "soil"];
  const labels = ["Slope", "Flat area", "Temperature", "Relief", "Soil proxy"];
  const cx = 170, cy = 160, R = 108;
  const pt = (i, v) => {
    const a = -Math.PI / 2 + (i * 2 * Math.PI) / keys.length;
    return [cx + R * v * Math.cos(a), cy + R * v * Math.sin(a)];
  };
  let svg = `<svg viewBox="0 0 340 320" role="img" aria-label="Radar chart of per-factor similarity">`;
  [0.25, 0.5, 0.75, 1].forEach((ring) => {
    const pts = keys.map((_, i) => pt(i, ring).join(",")).join(" ");
    svg += `<polygon points="${pts}" fill="none" stroke="#22345f" stroke-width="1"/>`;
  });
  keys.forEach((_, i) => {
    const [x, y] = pt(i, 1);
    svg += `<line x1="${cx}" y1="${cy}" x2="${x}" y2="${y}" stroke="#22345f"/>`;
  });
  const vals = keys.map((k) => (d.radar_similarity[k] === null ? 0.5 : d.radar_similarity[k]));
  const poly = vals.map((v, i) => pt(i, v).join(",")).join(" ");
  svg += `<polygon points="${poly}" fill="rgba(160,107,255,.28)" stroke="#a06bff" stroke-width="2"/>`;
  vals.forEach((v, i) => {
    const [x, y] = pt(i, v);
    const neutral = d.radar_similarity[keys[i]] === null;
    svg += `<circle cx="${x}" cy="${y}" r="4" fill="${neutral ? "#070d1f" : "#39c2ff"}" stroke="#39c2ff" stroke-width="2"/>`;
  });
  labels.forEach((lab, i) => {
    const [x, y] = pt(i, 1.18);
    svg += `<text x="${x}" y="${y}" fill="#9db1d8" font-size="12" font-weight="600" text-anchor="middle">${lab}</text>`;
  });
  svg += `</svg>`;
  const missing = keys.filter((k) => d.radar_similarity[k] === null);
  $("#radarBox").innerHTML = `<h3 style="margin-top:.2rem">Per-factor similarity — ${esc(d.base)} vs ${esc(d.site)}</h3>` +
    svg + `<p class="radar-note">1 = identical on that factor.${missing.length ?
      ` Hollow marker: ${missing.map((k) => PILLAR_LABELS[k]).join(", ")} not scored for this site (no data coverage), drawn neutral.` : ""}</p>`;
}

/* ------------------------------------------------------------------- mars */
async function initMars() {
  if (state.marsLoaded) return;
  state.marsLoaded = true;
  try {
    const d = await api("/api/mars");
    const r = d.region;
    $("#marsBox").innerHTML = `
      <div class="card" style="margin-bottom:1rem">
        <h3 style="margin-top:.2rem">${esc(r.mars_region)} <small style="color:var(--muted)">${fmt(r.lat, 2)}° N, ${fmt(r.lon, 2)}° E</small></h3>
        <div class="metric-line"><span>Mean elevation</span><b>${fmt(r.elev_mean_m)} m</b></div>
        <div class="metric-line"><span>Relief — elevation std</span><b>${fmt(r.elev_std_m)} m</b></div>
        <div class="metric-line"><span>Mean slope</span><b>${fmt(r.slope_mean_deg, 2)}°</b></div>
        <div class="metric-line"><span>Area flatter than 5°</span><b>${fmt(r.pct_slope_under_5deg)}%</b></div>
        <div class="metric-line"><span>Area flatter than 10°</span><b>${fmt(r.pct_slope_under_10deg)}%</b></div>
        <p class="sources">Source: ${esc(r.source)}</p>
      </div>
      <h3>Which Earth sites move most like Jezero? (closest mean slope)</h3>
      <div class="card-grid">${d.closest_earth_sites.map((s) => `
        <div class="card"><h3 style="margin:.1rem 0">${esc(s.site_name)}</h3>
          <div class="rc-meta" style="color:var(--muted)">${esc(s.country)}</div>
          <div class="metric-line"><span>Mean slope</span><b>${fmt(s.slope_mean_deg, 2)}°</b></div>
          <div class="metric-line"><span>Area flatter than 10°</span><b>${fmt(s.pct_slope_under_10deg)}%</b></div>
        </div>`).join("")}</div>`;
  } catch (err) {
    $("#marsBox").innerHTML = `<p class="loading">Failed to load (${esc(err.message)})</p>`;
  }
}

/* ------------------------------------------------------------- methodology */
async function initMethodology() {
  if (state.methodologyLoaded) return;
  state.methodologyLoaded = true;
  try {
    const r = await fetch("/api/methodology");
    $("#methodologyBody").innerHTML = await r.text();
  } catch (err) {
    $("#methodologyBody").innerHTML = `<p>Failed to load methodology (${esc(err.message)})</p>`;
  }
}

/* ------------------------------------------------------------------- boot */
loadOverview().then(route);
route();
