#!/bin/bash
# ATLAS — download every dataset the pipeline uses (all public, no login).
# Layout produced under ./data :
#   data/moon/terrain_s, terrain_n   LOLA LDEM/LDSM/LDRM (IMG+LBL), both poles
#   data/moon/psr                    LPSR masks, both poles
#   data/moon/illum                  PGDA-69 AVGVISIB solar + Earth visibility
#   data/moon/temperature            Diviner PCP tables pols + poln
#   data/earth/terrain               Copernicus DEM GLO-30 tiles for the 8 sites
# Total ~2.3 GB. SoilGrids and NASA POWER are streamed by the pipeline itself.
set -eu
cd "$(dirname "$0")/.."
PDS=https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx
DIV=https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/data_derived_pcp/diurnal/slon
IMB=http://imbrium.mit.edu/EXTRAS/ILLUMINATION/IMG
mkdir -p data/moon/{terrain_s,terrain_n,psr,illum,temperature} data/earth/terrain

for s in s n; do
  for f in "ldem_80${s}_80m" "ldsm_75${s}_240m" "ldrm_75${s}_240m"; do
    curl -L -C - -o "data/moon/terrain_${s}/${f}.img" "$PDS/data/lola_gdr/polar/img/${f}.img"
    curl -L -C - -o "data/moon/terrain_${s}/${f}.lbl" "$PDS/data/lola_gdr/polar/img/${f}.lbl"
  done
  curl -L -C - -o "data/moon/psr/lpsr_81${s}_240m.img" "$PDS/extras/illumination/release_2011/img/lpsr_81${s}_240m.img"
  curl -L -C - -o "data/moon/psr/lpsr_81${s}_240m.lbl" "$PDS/extras/illumination/release_2011/img/lpsr_81${s}_240m.lbl"
done

for f in AVGVISIB_85S_060M_201608 AVGVISIB_85S_060M_201608_EARTH AVGVISIB_75S_120M_201608 \
         AVGVISIB_75S_120M_201608_EARTH AVGVISIB_85N_060M_201608 AVGVISIB_85N_060M_201608_EARTH; do
  curl -L -C - -o "data/moon/illum/${f}.IMG" "$IMB/${f}.IMG"
  curl -L -C - -o "data/moon/illum/${f}.LBL" "$IMB/${f}.LBL"
done

for p in pols poln; do
  for sl in slon01 slon48; do
    curl -L -C - -o "data/moon/temperature/pcp_avg_tbol_${p}_win_${sl}_240.tab" "$DIV/${p}/pcp_avg_tbol_${p}_win_${sl}_240.tab"
    curl -L -C - -o "data/moon/temperature/pcp_avg_tbol_${p}_win_${sl}_240.lbl" "$DIV/${p}/pcp_avg_tbol_${p}_win_${sl}_240.lbl"
  done
done

for t in S24_00_W070_00 N19_00_W156_00 S78_00_E162_00 N75_00_W090_00 N64_00_W020_00 N35_00_W112_00 N37_00_W007_00 N78_00_E015_00; do
  curl -L -C - -o "data/earth/terrain/Copernicus_DSM_COG_10_${t}_DEM.tif" \
    "https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_${t}_DEM/Copernicus_DSM_COG_10_${t}_DEM.tif"
done
echo "All ATLAS data downloaded into ./data"
