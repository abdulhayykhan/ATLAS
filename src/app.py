"""ATLAS — Analog Terrain & Lunar Alignment System (Streamlit app).

Team Binary Knights, NASA Space Apps Challenge 2026.
Run:  streamlit run src/app.py
Reads only the small CSV/PNG outputs produced by src/preprocess_*.py and
src/model.py — the app never touches the multi-GB raw rasters.
"""
import os

import pandas as pd
import streamlit as st

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "outputs")

st.set_page_config(page_title="ATLAS — Lunar Analog Finder", page_icon="🌕", layout="wide")


@st.cache_data
def load(name):
    p = os.path.join(OUT, name)
    return pd.read_csv(p) if os.path.exists(p) else None


moon = load("moon_profiles.csv")
earth = load("earth_profiles.csv")
scores = load("scores_ranking.csv")
mars = load("mars_profiles.csv")

st.sidebar.title("🌕 ATLAS")
st.sidebar.caption("Analog Terrain & Lunar Alignment System\nTeam Binary Knights — NASA Space Apps 2026")
page = st.sidebar.radio("Page", ["Home", "Moon Bases", "Earth Analog Finder", "Compare", "Mars", "Methodology & Sources"])

if moon is None or earth is None or scores is None:
    st.error("Output data not found. Run: python src/preprocess_moon.py, python src/preprocess_earth.py, "
             "python src/preprocess_mars.py, then python src/model.py")
    st.stop()

if page == "Home":
    st.title("Which places on Earth are most like the Moon's future base sites?")
    st.write(
        "NASA plans permanent bases at four lunar polar craters — **Peary, Shackleton, de Gerlache and Amundsen** — "
        "chosen for water ice in permanently shadowed regions, sunlight for power, and a direct view of Earth for "
        "communication. Before hardware and crews go there, they must be tested somewhere on Earth that behaves "
        "the same way. ATLAS measures all four bases from real NASA LRO data, profiles candidate Earth sites from "
        "Copernicus, NASA POWER and SoilGrids data, and ranks every Earth site against every base with a "
        "transparent, weighted dissimilarity score."
    )
    c = st.columns(4)
    for i, (_, b) in enumerate(moon.iterrows()):
        with c[i]:
            st.metric(b["base_name"], f"{b['lat']}, {b['lon']}")
            st.caption(f"{'North' if b['pole']=='N' else 'South'} Pole · Sun {b['sun_visibility_pct']}% · "
                       f"Earth view {b['earth_visibility_pct']}% · PSR {b['psr_pct']}%")
    st.subheader("Top Earth match for each base")
    top = scores[scores["rank_for_base"] == 1][["moon_base", "earth_site", "analog_score"]]
    st.dataframe(top, width="stretch", hide_index=True)
    st.caption("Scores come from real measurements — see Methodology & Sources for data, formula, weights and limitations.")

elif page == "Moon Bases":
    st.title("The four Moon bases — measured, not guessed")
    for _, b in moon.iterrows():
        st.subheader(f"{b['base_name']} ({b['lat']}, {b['lon']}) — {b['crater_diameter_km']} km crater, {b['roi_radius_km']} km study area")
        col1, col2 = st.columns([2, 1])
        with col1:
            st.dataframe(pd.DataFrame({
                "Measure": ["Mean elevation (m)", "Mean slope (°)", "Area flatter than 10° (%)",
                            "Surface roughness, mean (m)", "Permanently shadowed area (%)",
                            "Sun visibility (%)", "Earth visibility (%)",
                            "Mean temperature, seasonal (°C)", "Winter cold level, 1st percentile (K)"],
                "Value": [b["elev_mean_m"], b["slope_mean_deg"], b["pct_slope_under_10deg"],
                          b["roughness_mean_m"], b["psr_pct"], b["sun_visibility_pct"],
                          b["earth_visibility_pct"], b["temp_seasonal_mean_c"], b["temp_winter_cold_p1_k"]],
            }), width="stretch", hide_index=True)
            st.caption("Sources: " + b["sources"])
        with col2:
            img = os.path.join(OUT, f"hillshade_{b['base_name'].replace(' ', '').lower()}.png")
            if os.path.exists(img):
                st.image(img, caption=f"Shaded relief (LOLA DEM) — {b['base_name']}")
    st.info("Peary is at the North Pole — earlier drafts of this project covered only the South Pole. "
            "ATLAS processes both poles: LDEM/LDSM/LDRM 80N-75N and Diviner poln tables included.")

elif page == "Earth Analog Finder":
    st.title("Earth analog sites, ranked per Moon base")
    base = st.selectbox("Choose a Moon base", moon["base_name"].tolist())
    sub = scores[scores["moon_base"] == base].merge(earth, left_on="earth_site", right_on="site_name")
    try:
        import folium
        from streamlit_folium import st_folium
        m = folium.Map(location=[20, 0], zoom_start=2)
        brow = moon[moon["base_name"] == base].iloc[0]
        for _, r in sub.iterrows():
            color = "green" if r["rank_for_base"] == 1 else "blue" if r["rank_for_base"] <= 3 else "gray"
            folium.CircleMarker([r["lat"], r["lon"]], radius=8, color=color, fill=True,
                                popup=f"<b>{r['earth_site']}</b> ({r['country']})<br>{r['site_type']}<br>"
                                      f"Analog Score: {r['analog_score']}<br>Mean slope: {r['slope_mean_deg']}°<br>"
                                      f"Mean temp: {r['temp_mean_c']}°C").add_to(m)
        st_folium(m, width=None, height=480)
    except Exception as e:
        st.warning(f"Map unavailable ({e}); table below has the same data.")
    st.dataframe(sub[["rank_for_base", "earth_site", "country", "site_type", "analog_score",
                      "slope_mean_deg", "pct_slope_under_10deg", "temp_mean_c", "sand_pct",
                      "clay_pct", "coarse_fragments_pct"]],
                 width="stretch", hide_index=True)
    st.download_button("Download full ranking (CSV)", scores.to_csv(index=False), "atlas_scores_ranking.csv", "text/csv")
    st.download_button("Download Earth profiles (CSV)", earth.to_csv(index=False), "atlas_earth_profiles.csv", "text/csv")
    st.download_button("Download Moon profiles (CSV)", moon.to_csv(index=False), "atlas_moon_profiles.csv", "text/csv")

elif page == "Compare":
    st.title("Head-to-head: Moon base vs its best Earth match")
    base = st.selectbox("Moon base", moon["base_name"].tolist())
    site = st.selectbox("Earth site", earth["site_name"].tolist())
    b = moon[moon["base_name"] == base].iloc[0]
    e = earth[earth["site_name"] == site].iloc[0]
    s = scores[(scores["moon_base"] == base) & (scores["earth_site"] == site)].iloc[0]
    st.metric(f"Analog Score — {site} for {base}", s["analog_score"], f"Rank #{int(s['rank_for_base'])} of {len(earth)} for this base")
    st.dataframe(pd.DataFrame({
        "Measure": ["Mean slope (°)", "Area flatter than 10° (%)", "Mean temperature (°C)",
                    "Relief — elevation std (m)", "Mean elevation (m)"],
        base: [b["slope_mean_deg"], b["pct_slope_under_10deg"], b["temp_seasonal_mean_c"], b["elev_std_m"], b["elev_mean_m"]],
        site: [e["slope_mean_deg"], e["pct_slope_under_10deg"], e["temp_mean_c"], e["elev_std_m"], e["elev_mean_m"]],
    }), width="stretch", hide_index=True)
    radar = os.path.join(OUT, f"radar_{base.replace(' ', '').lower()}.png")
    top_site = scores[(scores["moon_base"] == base) & (scores["rank_for_base"] == 1)].iloc[0]["earth_site"]
    if site == top_site and os.path.exists(radar):
        st.image(radar, caption=f"Per-factor similarity, {base} vs {site} (1 = identical)")
    st.caption("Sun visibility and Earth visibility are deliberately not scored — Earth has no counterpart for them. "
               "They are mission context on the Moon Bases page.")

elif page == "Mars":
    st.title("And Mars?")
    st.write("The same terrain method runs on Mars data. Below is Jezero Crater (Perseverance's home), "
             "measured from NASA's MOLA instrument exactly the way the Moon bases were measured.")
    if mars is not None:
        st.dataframe(mars, width="stretch", hide_index=True)
        m = mars.iloc[0]
        e = earth.copy()
        e["slope_gap_vs_jezero"] = (e["slope_mean_deg"] - m["slope_mean_deg"]).abs()
        st.subheader("Which Earth sites move most like Jezero?")
        st.dataframe(e.nsmallest(3, "slope_gap_vs_jezero")[["site_name", "country", "slope_mean_deg", "pct_slope_under_10deg"]],
                     width="stretch", hide_index=True)
        st.caption(f"Jezero reference: mean slope {m['slope_mean_deg']}°, {m['pct_slope_under_10deg']}% of area flatter than 10°.")
    st.write("Extending ATLAS to a full Mars ranking (MOLA + THEMIS temperature) is the roadmap item after this challenge.")

elif page == "Methodology & Sources":
    st.title("Methodology & Sources")
    md = os.path.join(OUT, "methodology.md")
    if os.path.exists(md):
        st.markdown(open(md).read())
    else:
        st.write("Methodology file not found — it is generated with the project outputs (outputs/methodology.md).")
