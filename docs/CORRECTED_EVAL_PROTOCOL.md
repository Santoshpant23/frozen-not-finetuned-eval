# A corrected-evaluation protocol for geospatial foundation models on field-level tasks

*Draft methods contribution / reusable checklist. Distilled from the failures and controls in this benchmark; pairs with `docs/FTW_LABEL_VALIDITY_RESULTS.md`. lead with **evaluation validity**, not model superiority.*

## Why a protocol

Across this project, the headline conclusion about geospatial foundation models (GeoFMs) flipped **five separate times** — under label source, preprocessing, pooling operator, split design, and metric — each a defensible-looking choice. The same swap that makes a GeoFM look dominant can make a 30-dimensional spectral random forest look competitive. The contribution is therefore a **protocol that pins down those choices** so a reported GeoFM-vs-baseline verdict is reproducible and means what it claims.

## The 10-point checklist

**Labels**
1. **Evaluate field-level tasks against true field boundaries, not a land-cover proxy.** WorldCover-"cropland" tiles ~66% of a scene while true FTW fields tile ~11–18%; the proxy turns "is this a field?" into "is this managed land?", which a spectral baseline solves. (`ftw_proxy_mismatch_coverage.json`.) If only a proxy is available, *say so* and treat all model rankings as provisional.
2. **Make the label comparison same-pixel paired.** Hold one shared pixel set per chip and score it under both label definitions (e.g. `ftw_field_membership` vs `worldcover_cropland`); do not let each label resample its own pixels. Report `n_pixels` (identical for both arms) and `chip_overlap=0`.

**Splits & leakage**
3. **Group the train/test split by chip** (all pixels of a 256-px chip on one side). Pixel-level splits leak via spatial autocorrelation and over-state every model.
4. **Add a scene-disjoint robustness split** (group by Sentinel-2 tile / MGRS) for geographically-concentrated datasets, and report it alongside the chip-grouped numbers. Absolute scores are spatially optimistic when test chips border training chips of the same scene; the *paired* contrast is common-mode and survives, but say which you are reporting.

**Baselines & parity**
5. **Always report a per-pixel spectral baseline** (random forest on raw bands). It is the control that exposes label/protocol artifacts — under a land-cover proxy it can match or beat GeoFMs.
6. **Give the baseline and the FM byte-identical evaluation:** same chips, same split, same valid-mask, same metric. Split-then-mask (not mask-then-split) so the partitions match exactly.

**Preprocessing**
7. **Use each FM's own input normalization** (DN scaling + per-band mean/std). Feeding unnormalized reflectance silently degrades some models (this flipped a ranking here for two of four FMs). Exclude sensor no-data/zero pixels from sampling.

**Statistics**
8. **Cluster uncertainty at the chip, not the pixel.** Report chip-clustered bootstrap CIs on every metric and on the paired model-vs-baseline deltas; apply a multiple-comparison correction (Holm/BH) across regions × deltas.

**Interpretation controls**
9. **Run an edge-vs-interior control before claiming "boundary understanding."** Restricting the test set to boundary-zone pixels collapsed *all* models (FMs included) to ≈chance here — the FM advantage is within-field interior context, not boundary delineation. Scope claims accordingly.
10. **Report across field-size regimes.** The FM-over-baseline advantage is real but has a field-size gradient (largest for smallholder, shrinking as fields grow); a single region cannot support a general claim.

## Reproducibility / hosting (submission gate)
- Provenance block in every results doc; all metric JSONs checksummed (`scripts/checksums.py --verify`); end-to-end commands in `docs/FTW_REPRODUCE.md`.
- Deposit the chip+feature+label bundle (Zenodo/HF) with **Croissant + RAI metadata** and record the dataset URL — required for dataset/evaluation-track submission; non-compliance risks desk rejection.

## What this protocol demonstrated (one line)
On identical pixels and features, swapping a land-cover proxy for true field boundaries inverts the GeoFM-vs-spectral-baseline verdict in all five tested regions — so a reported verdict is a statement about the **evaluation design**, not just the models.
