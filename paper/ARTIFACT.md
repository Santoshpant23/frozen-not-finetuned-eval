# frozen-not-finetuned-eval — Artifact & Reproduction

Evaluation artifact for *"Frozen, Not Fine-tuned: A Controlled Evaluation of Geospatial
Foundation Models for Agricultural Field Mapping."* This repository releases the
controlled-evaluation **apparatus** (code) and all derived **metrics**. It does **not**
redistribute raw satellite imagery — Sentinel-2 (Copernicus), ESA WorldCover, and Fields of
The World (FTW) are pulled from their open sources by the scripts below.

Machine-readable metadata (incl. Responsible-AI fields) is in `paper/croissant.json`.

## What's released
- **6 regions**: India, Cambodia, Vietnam, Kenya, France, Netherlands (FTW true field
  boundaries + ESA WorldCover cropland proxy, on identical pixels).
- **Model ladder**: per-pixel random forest, 5×5 windowed RF, supervised U-Net (from scratch),
  frozen GeoFM + probe, and end-to-end fine-tuned GeoFMs (Prithvi-EO-2.0, TerraMind; Clay,
  AnySat for breadth).
- **Result JSONs** (`data/results/`, checksummed):
  - `ftw_master_results.json` — in-region AUROC (RF true/proxy, U-Net, frozen-FM, fine-tuned-FM).
  - `ftw_transfer_strengthened.json` — 10 directed cross-region transfers.
  - `ftw_probe_inregion.json` — apples-to-apples frozen-backbone+decoder vs. full fine-tune.
  - `ftw_probes_summary.json`, `ftw_transfer_probe_multi.json`, `ftw_india_wilcoxon.json`,
    `ftw_windowed_rf_control.json`, `ftw_unet_perpixel_ablation.json`,
    `ftw_partial_label_sensitivity.json` — controls & statistics.

## Environment
Python 3.11 (tested; `.python-version` pins 3.11). Install with `pip install -e .`. A GPU
(A6000-class) is used for U-Net / GeoFM training; CPU suffices for the RF and frozen-probe
analyses. GeoFM weights load from Hugging Face / `terratorch`.

## Reproduce (per country `$C`)
```bash
# 1. labels + S2/WorldCover pull (GEE auth required)
bash scripts/prep_ftw_country.sh $C            # FTW label download + polygon extraction
python scripts/build_ftw_index.py --country $C --limit 800 --out data/index/ftw_$C.jsonl
bash scripts/run_ftw_country.sh $C             # S2 + WorldCover pull, manifest, feature extraction

# 2. canonical split (identical pixels for every model)
python scripts/ftw_export_split.py --country $C

# 3. Flaw 1 + Flaw 2: controlled same-pixel comparison (RF + frozen-FM probes, true vs proxy)
python scripts/ftw_controlled_label_comparison.py --country $C

# 4. strong supervised baseline + GeoFM fine-tuning (the "frozen vs fine-tuned" spine)
python scripts/ftw_unet_baseline.py --robust $C
python scripts/ftw_finetune_fm.py --model prithvi $C            # full fine-tune
python scripts/ftw_finetune_fm.py --model prithvi --freeze backbone $C   # frozen backbone + decoder

# 5. cross-region transfer (train $C, evaluate elsewhere)
python scripts/ftw_finetune_fm.py --model prithvi --eval-country <B> $C
python scripts/ftw_transfer_probe.py                            # frozen-FM + RF transfer (all pairs)
```
Multi-seed runs pass `--seed {0,1,2}`; low-data uses `--frac {0.1,0.25,0.5}`.

## Verification (already performed; re-runnable)
- **Label↔imagery alignment / CRS**: FTW field polygons are reprojected to each chip's local
  UTM zone at pull time (`scripts/ftw_to_polygons.py`); every stored positive pixel falls inside
  an FTW field polygon and every negative outside it, in all 6 regions (100%). This geometry
  check is the CRS-correctness guarantee for the FTW pixels.
- **Artifact integrity**: `python scripts/checksums.py --verify` recomputes SHA-256 over every
  released metric JSON and fails on any drift. A `.gitattributes` forces LF line endings so the
  checksums match byte-for-byte on every OS (including Windows).
- **Reproducibility**: all headline numbers recompute from raw rasters/features to 3 decimals.
- **Controls**: a per-pixel (1×1-conv) ablation collapses to ≈RF; a 5×5 windowed RF gains
  ~0.01; an edge-pixel control localizes the advantage to within-field interior; an FTW
  partial-labeling sensitivity test leaves the GeoFM AUROC essentially unchanged.

## Data sources & licenses
- Fields of The World (CC-BY-4.0), ESA WorldCover 10m v200 (CC-BY-4.0), Sentinel-2 L2A
  (Copernicus, free & open). Released code: Apache-2.0; derived metrics & docs: CC-BY-4.0.

## Note
This artifact contains aggregate evaluation metrics and code over public Earth-observation
data; it includes no personal or sensitive information.
