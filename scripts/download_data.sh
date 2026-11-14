#!/bin/bash
# ATLAS — download every dataset the pipeline uses (all public, no login).
# Layout produced under ./data :
#   data/moon/terrain_s, terrain_n   LOLA LDEM/LDSM/LDRM (IMG+LBL), both poles
#   data/moon/psr                    LPSR masks, both poles
#   data/moon/illum                  PGDA-69 AVGVISIB solar + Earth visibility
#   data/moon/temperature            Diviner PCP tables pols + poln
#   data/earth/terrain               Copernicus DEM GLO-30 tiles for the 14 novel sites
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

for t in N30_00_E058_00 N37_00_E094_00 N40_00_E102_00 S19_00_E016_00 S30_00_W066_00 S78_00_E167_00 S63_00_W061_00 N56_00_E160_00 S19_00_E144_00 N33_00_E126_00 N70_00_E068_00 N67_00_E172_00 N19_00_E076_00 N22_00_W011_00; do
  curl -L -C - -o "data/earth/terrain/Copernicus_DSM_COG_10_${t}_DEM.tif" \
    "https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_${t}_DEM/Copernicus_DSM_COG_10_${t}_DEM.tif"
done
echo "All ATLAS data downloaded into ./data"
