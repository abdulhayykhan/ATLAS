"""ATLAS Phase 3 — Analog scoring engine.

Combines outputs/moon_profiles.csv and outputs/earth_profiles.csv.

Method (full write-up in outputs/methodology.md):
  * Every shared variable is min-max normalised to 0-1 across the Moon bases
    and Earth sites TOGETHER, so distances are on one common scale.
  * Dissimilarity = weighted Euclidean distance. Weights agreed by the team:
    slope 30%, flat area (slope < 10 deg) 20%, temperature 20%,
    soil/regolith proxy 15%, relief (elevation std) 15%.
  * Analog Score = 100 * exp(-D)  (100 = identical, lower = less similar).
  * Sun % and Earth % are NOT scored: Earth has no counterpart for them.
    They are shown in the app as mission context for each base.
  * Soil has no direct lunar percentage dataset, so the soil pillar is an
    Earth-side regolith-likeness index (coarse fragments + sand - clay),
    identical for every base and clearly labelled a proxy.
  * Temperature is compared in absolute degrees C. No Earth site is anywhere
    near lunar polar temperatures; this pillar therefore compresses scores
    and is the project's #1 stated limitation, not a hidden fudge.

Outputs: outputs/scores_ranking.csv, outputs/radar_<base>.png (Top-1 match).
"""
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "outputs")

WEIGHTS = {"slope": 0.30, "flat": 0.20, "temperature": 0.20, "soil": 0.15, "relief": 0.15}


def minmax(s):
    lo, hi = s.min(), s.max()
    return (s - lo) / (hi - lo) if hi > lo else s * 0.0


def main():
    moon = pd.read_csv(os.path.join(OUT, "moon_profiles.csv"))
    earth = pd.read_csv(os.path.join(OUT, "earth_profiles.csv"))

    moon_f = pd.DataFrame({
        "name": moon["base_name"],
        "slope": moon["slope_mean_deg"],
        "flat": moon["pct_slope_under_10deg"],
        "temperature": moon["temp_seasonal_mean_c"],
        "relief": moon["elev_std_m"],
    })
    earth_f = pd.DataFrame({
        "name": earth["site_name"],
        "slope": earth["slope_mean_deg"],
        "flat": earth["pct_slope_under_10deg"],
        "temperature": earth["temp_mean_c"],
        "relief": earth["elev_std_m"],
    })
    both = pd.concat([moon_f, earth_f], ignore_index=True)
    for col in ["slope", "flat", "temperature", "relief"]:
        both[col + "_n"] = minmax(both[col])
    moon_n = both.iloc[: len(moon_f)].reset_index(drop=True)
    earth_n = both.iloc[len(moon_f):].reset_index(drop=True)

    # Earth regolith-likeness (0-1): coarse fragments and sand raise it, clay lowers it.
    # SoilGrids does not cover Antarctica, so Antarctic sites have no soil values: for
    # such sites the soil pillar is dropped and the remaining weights are
    # renormalised — missing data must never act as a penalty score.
    reg = (earth["coarse_fragments_pct"] + earth["sand_pct"] - earth["clay_pct"])
    reg_n = minmax(reg.fillna(reg.mean()))

    rows = []
    for i, mb in moon_n.iterrows():
        for j, es in earth_n.iterrows():
            comp = {}
            comp["slope"] = (mb["slope_n"] - es["slope_n"]) ** 2
            comp["flat"] = (mb["flat_n"] - es["flat_n"]) ** 2
            comp["temperature"] = (mb["temperature_n"] - es["temperature_n"]) ** 2
            comp["relief"] = (mb["relief_n"] - es["relief_n"]) ** 2
            w = dict(WEIGHTS)
            if pd.isna(reg.iloc[j]):
                comp["soil"] = np.nan
                w["soil"] = 0.0
            else:
                # Soil proxy: distance of the site from an ideal regolith (index = 1)
                comp["soil"] = (1.0 - float(reg_n.iloc[j])) ** 2
            wsum = sum(w.values())
            d = float(np.sqrt(sum(w[k] * comp[k] for k in w if not pd.isna(comp[k])) / wsum))
            rows.append({
                "moon_base": mb["name"], "earth_site": es["name"],
                "dissimilarity": round(d, 3),
                "analog_score": round(100 * float(np.exp(-d)), 1),
                **{f"dist_{k}": round(float(np.sqrt(v)), 3) for k, v in comp.items()},
            })
    df = pd.DataFrame(rows)
    df["rank_for_base"] = df.groupby("moon_base")["dissimilarity"].rank(method="min").astype(int)
    for base, g in df.groupby("moon_base"):
        top = g.nsmallest(1, "dissimilarity").iloc[0]
        weak = max(["slope", "flat", "temperature", "relief"], key=lambda k: top[f"dist_{k}"])
        strong = min(["slope", "flat", "temperature", "relief"], key=lambda k: top[f"dist_{k}"])
        df.loc[top.name, "top_match_factor"] = strong
        df.loc[top.name, "weakest_factor"] = weak
    df = df.sort_values(["moon_base", "rank_for_base"])
    df.to_csv(os.path.join(OUT, "scores_ranking.csv"), index=False)
    print(df.to_string())

    # --- Site-regime clustering (Challenge Guide Objective 4 mentions
    # clustering explicitly): K-Means (k=3) over the normalised Earth-site
    # features groups the novel sites into environmental regimes. Cluster
    # names are assigned from centroid character, not by hand per site.
    try:
        from sklearn.cluster import KMeans
        feats = earth_n[["slope_n", "flat_n", "temperature_n", "relief_n"]].copy()
        feats["regolith_n"] = reg_n.values
        km = KMeans(n_clusters=3, n_init=10, random_state=42).fit(feats)
        cent = pd.DataFrame(km.cluster_centers_, columns=feats.columns)
        # Regime names are derived mechanically: cold/hot from each cluster's
        # mean Earth temperature in raw degrees, slope word from the centroid.
        mean_temp = earth.assign(_c=km.labels_).groupby("_c")["temp_mean_c"].mean()
        rank = {int(c): i + 1 for i, c in enumerate(mean_temp.sort_values().index)}
        names = {}
        for c in range(3):
            s = cent.loc[c, "slope_n"]
            word = "rugged" if s > 0.6 else "flat" if s < 0.25 else "mixed"
            names[c] = (f"Regime {rank[c]} · {word} "
                        f"(cluster mean {mean_temp.loc[c]:.0f} °C)")
        earth_out = earth.copy()
        earth_out["regime"] = [names[c] for c in km.labels_]
        earth_out.to_csv(os.path.join(OUT, "earth_profiles.csv"), index=False)
        print("regimes:", earth_out[["site_name", "regime"]].to_string())
    except Exception as e:
        print("clustering skipped:", e)

    # Radar plots: per-feature similarity (1 - normalised distance) for each base's Top-1 site
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        labels = ["Slope", "Flat area", "Temperature", "Relief", "Soil proxy"]
        for base, g in df.groupby("moon_base"):
            top = g.nsmallest(1, "dissimilarity").iloc[0]
            vals = [1 - top[f"dist_{k}"] for k in ["slope", "flat", "temperature", "relief", "soil"]]
            vals = [0.5 if pd.isna(v) else v for v in vals]  # neutral if a pillar was not scored
            vals += vals[:1]
            ang = np.linspace(0, 2 * np.pi, len(labels) + 1)
            fig, ax = plt.subplots(subplot_kw={"polar": True}, figsize=(5, 5))
            ax.plot(ang, vals, "o-", linewidth=2)
            ax.fill(ang, vals, alpha=0.25)
            ax.set_xticks(ang[:-1]); ax.set_xticklabels(labels, fontsize=9)
            ax.set_ylim(0, 1)
            ax.set_title(f"{base} vs {top['earth_site']}\nAnalog Score {top['analog_score']}", fontsize=11)
            fig.tight_layout()
            fig.savefig(os.path.join(OUT, f"radar_{base.replace(' ', '').lower()}.png"), dpi=150)
            plt.close(fig)
        print("radar plots saved")
    except Exception as e:
        print("radar plots skipped:", e)


if __name__ == "__main__":
    main()
