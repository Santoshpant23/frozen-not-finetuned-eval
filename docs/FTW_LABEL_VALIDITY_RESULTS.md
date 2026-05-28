# Label validity: do GeoFM conclusions depend on the label source? (FTW true fields vs WorldCover proxy)

**Regions:** India (India, 2016), Kenya (2017), Vietnam (2021), France (2020), and Netherlands (2022) — the last two large-field European controls — over Fields of The World (FTW) footprints. The headline below is India; the four replications, the field-size gradient, and a scene-disjoint robustness check are in the cross-region section.
**Question:** Smallholder-cropland studies almost always train/evaluate against an automatic land-cover proxy (here ESA WorldCover "cropland", class 40), because true field boundaries are scarce. **Does the choice of label change which model wins, and by how much?**

We answer it the only way that removes confounds: hold the **evaluation pixels and the model features fixed**, and vary **only the target label**. The verdict flips.

> **Provenance.** All numbers below are produced by the scripts in `scripts/ftw_*` and recorded in `data/results/ftw_*.json` (checksummed in `data/results/CHECKSUMS.sha256`; verify with `python scripts/checksums.py --verify`). End-to-end reproduction steps are in `docs/FTW_REPRODUCE.md`. The headline is the **controlled same-pixel** comparison (`ftw_controlled_label_comparison*.json`): one shared pixel set per region scored under both labels — *not* the separate "standalone" runs, which sample each label's own pixels and are reported only as a realistic-deployment cross-check.

---

## Headline (controlled, same-pixel, zero confound)

213,611 FTW-India pixels; chip-grouped split (525 train / 175 test chips, **chip overlap = 0**); identical per-pixel FM features and identical raw-S2 features for the spectral baseline. We change **only** the target:

- **TRUE** = pixel lies inside an FTW true field-boundary polygon (a *field-membership* task).
- **PROXY** = pixel is WorldCover-cropland (a *land-cover-detection* task).

| Model (linear probe; RF for spectral) | TRUE field — AUROC / F1 | WC-cropland proxy — AUROC / F1 |
|---|---|---|
| Prithvi-EO-2.0-300M | **0.983 / 0.908** | 0.864 / 0.864 |
| TerraMind v1 base   | **0.967 / 0.881** | 0.878 / 0.875 |
| AnySat (dense)      | **0.939 / 0.852** | 0.760 / 0.813 |
| Clay v1             | 0.577 / 0.444 | 0.696 / 0.740 |
| **RF / spectral (12-band S2)** | **0.574 / 0.079** | **0.786 / 0.887** |

*Artifact: `data/results/ftw_controlled_label_comparison.json`. Reproduce: `python scripts/ftw_controlled_label_comparison.py` (reuses cached TRUE-mode features; no GPU re-extraction).*

**What flips (metric-precise).** On the *identical* pixels and features, swapping true field boundaries for the standard proxy takes the spectral random-forest baseline from **F1 = 0.08 (last place, at chance)** to **F1 = 0.89 (the best F1 of any model)** — a **full inversion on the F1 metric**. On AUROC the same swap lifts the RF from 0.57 (chance) to 0.79 while cutting the strongest FM from 0.98 to 0.86, **collapsing a 0.41 AUROC gap to 0.07**; here the inversion is partial — the two strongest FMs keep a narrow edge, but Clay and AnySat fall behind the baseline. Either metric tells the same story: changing *only the label* moves the verdict from "three FMs dominate, baseline at chance" to "the baseline is the best model (F1) or near-parity with it (AUROC)." A study reporting WorldCover F1 — the common practice — would crown a 30-dimensional random forest the single best model; the same pixels with true boundaries put it dead last.

**Why this is real, not a leak (anti-leak control).** Under the TRUE label, **Clay v1 stays at AUROC 0.577 on the exact pixels where Prithvi reaches 0.983.** A label leak or spatial-autocorrelation shortcut would lift *all* models equally; a selective effect that helps Prithvi/TerraMind/AnySat but not Clay or the RF is incompatible with leakage and consistent with a genuine representational difference. Chip overlap between train and test is exactly 0 (recorded in every result JSON).

**Mechanism.** WorldCover-cropland is a spectrally separable target — "is this pixel crop-like reflectance?" — which a random forest on raw bands solves directly (F1 0.89). True field-*membership* requires spatial/contextual structure that raw per-pixel spectra do not carry (RF F1 0.08); only the spatially-pretrained FMs supply it. A boundary-zone control (see Limitations) localizes this to **within-field interior context**, not boundary delineation: at field edges every model drops to ≈0.58. The proxy therefore rewards the *wrong* capability for smallholder field mapping.

---

## Realistic-deployment view (standalone runs, natural class balance)

The controlled table above changes only the label on one fixed pixel set. In practice each label also induces its **own** sampled pixels (positives drawn from that label's mask). Re-running the full per-pixel harness separately for each label — with the corrected harness (split-then-mask parity between FM and RF; chip-overlap recorded; S2 no-data excluded) — gives:

| Model | TRUE — AUROC / F1 | PROXY — AUROC / F1 |
|---|---|---|
| Prithvi-EO-2.0-300M | 0.983 / 0.912 | 0.820 / 0.742 |
| TerraMind v1 base   | 0.968 / 0.880 | 0.844 / 0.764 |
| AnySat (dense)      | 0.935 / 0.848 | 0.749 / 0.680 |
| Clay v1             | 0.576 / 0.438 | 0.499 / 0.506 |
| **RF / spectral**   | **0.616 / 0.101** | **0.798 / 0.726** |

*Artifacts: `data/results/eval_per_pixel_ftw_india_{true,proxy}_chip.json`, `_{true,proxy}_anysat_chip.json`, `_{true,proxy}_nonfm_rf_chip.json`. Each `dataset` block now records `split`, `n_train_chips`, `n_test_chips`, `chip_overlap`.*

Same direction, partial magnitude: under true labels the RF is dead last (AUROC 0.616, F1 0.101); under the proxy it jumps to **AUROC 0.798 / F1 0.726**, overtaking Clay and AnySat and closing to within 0.02–0.05 AUROC of the two strongest FMs (Prithvi 0.820, TerraMind 0.844). The proxy does **not** fully invert the ranking in this standalone view — the top two FMs keep a narrow edge — but it collapses an FM advantage that true labels show to be decisive (≈0.37 AUROC over the RF) down to near-parity. (Each standalone label also resamples its own pixels, so the RF's true-label score here, 0.616, differs from the fixed-pixel controlled value, 0.574; this is expected, not a contradiction.)

---

## Replication across regions (Kenya muted, Vietnam strong)

### Second region: Kenya (direction-confirming, magnitude-attenuated)

We repeated the entire pipeline on FTW-Kenya (2017; 335 chips pulled, 209 carrying true-field polygons — an even more smallholder set: 94 fields <0.1 ha). Controlled, same-pixel (49,686 px, chip overlap = 0):

| Model | TRUE — AUROC / F1 | WC-proxy — AUROC / F1 |
|---|---|---|
| AnySat (dense) | **0.853 / 0.546** | 0.859 / 0.774 |
| Prithvi-EO-2.0-300M | 0.766 / 0.315 | 0.786 / 0.684 |
| TerraMind v1 base | 0.745 / 0.263 | 0.803 / 0.694 |
| Clay v1 | 0.556 / 0.226 | 0.670 / 0.573 |
| **RF / spectral** | **0.651 / 0.074** | **0.806 / 0.660** |

Standalone (true: 155 train / 52 test chips; proxy: 251 / 84):

| Model | TRUE — AUROC / F1 | WC-proxy — AUROC / F1 |
|---|---|---|
| AnySat (dense) | 0.853 / 0.546 | 0.799 / 0.728 |
| Prithvi-EO-2.0-300M | 0.766 / 0.315 | 0.742 / 0.689 |
| TerraMind v1 base | 0.745 / 0.263 | 0.752 / 0.696 |
| Clay v1 | 0.556 / 0.226 | 0.504 / 0.491 |
| **RF / spectral** | **0.687 / 0.076** | **0.791 / 0.717** |

*Artifacts: `data/results/ftw_controlled_label_comparison_kenya.json`, `eval_per_pixel_ftw_kenya_*`.*

**What replicates, what doesn't (honest read).**
- **Replicates (direction):** the proxy again inflates the spectral baseline to FM-competitive-or-better. Under true labels the RF has the **worst F1 in both regions** (India 0.08, Kenya 0.074–0.076); under the proxy it jumps to FM parity — in Kenya's *standalone* run (251/84 chips) the RF's proxy AUROC (0.79) **out-ranks three of the four FMs** and its proxy F1 (0.72) beats Prithvi/TerraMind (in the controlled same-pixel run the RF reaches 0.806 AUROC, still above three FMs). The core claim — *the standard proxy makes a per-pixel spectral baseline look as good as foundation models* — holds in both countries.
- **Does NOT replicate (magnitude):** India's *dramatic* FM advantage on true fields (0.97–0.98 vs 0.57) is **muted** in Kenya — the best model on true fields is AnySat at 0.853, with the RF at 0.65–0.69 (not at chance). So "true labels expose a large FM advantage" is an India-specific magnitude, not a universal one.
- **Model ranking is itself region-dependent:** Prithvi/TerraMind dominate India's true-field task; **AnySat is the clear leader in Kenya** (and Prithvi/TerraMind drop to 0.75). Which GeoFM "wins" depends on the region — another way label/region choices drive conclusions.

**Caveats for Kenya specifically:** smaller and noisier than India (155 vs 525 train chips; 8,286 true-positive pixels; true pos-rate 0.167), and East-African smallholder mosaics (intercropping, irregular plots) are intrinsically harder. We therefore present Kenya as **direction-confirming, magnitude-attenuated**, not as a clean replication.

### Third region: Vietnam — strong replication (dense, regular paddy)

FTW-Vietnam (2021; 288 chips, **103.7k** true-field polygons — dense, regular Mekong/Red-River paddy). Controlled, same-pixel (114,000 px, chip overlap 0; **independently verified — every cell reproduced from the raw arrays**):

| Model | TRUE — AUROC / F1 | WC-proxy — AUROC / F1 |
|---|---|---|
| Prithvi-EO-2.0-300M | **0.929 / 0.883** | 0.885 / 0.851 |
| TerraMind v1 base | 0.916 / 0.866 | 0.900 / 0.871 |
| AnySat (dense) | 0.897 / 0.836 | 0.912 / 0.883 |
| Clay v1 | 0.503 / 0.493 | 0.607 / 0.634 |
| **RF / spectral** | **0.643 / 0.610** | **0.911 / 0.923** |

*Artifacts: `ftw_controlled_label_comparison_vietnam.json`, `eval_per_pixel_ftw_vietnam_*`, `ftw_bootstrap_ci_vietnam.json`.*

Vietnam **strongly replicates India**: under true labels the FMs lead decisively (Prithvi 0.929 vs RF 0.643; paired bestFM−RF true AUROC **+0.286 [0.266, 0.305]**), and the proxy lifts the RF to **AUROC 0.911 / F1 0.923 — tied-best of all models** (paired RF proxy−true F1 **+0.313 [0.294, 0.332]**). On AUROC the verdict flips exactly as in India.

Two honest notes (both surfaced by the independent audit):
- **Compare regions on AUROC, not F1.** Vietnam's evaluation pos-rate is exactly 0.50 *not* because paddy covers half the landscape (true in-field coverage ≈ 11%) but because the balanced sampler always fills its 200-positive-per-chip quota in these dense chips, whereas India/Kenya chips often cannot (giving their lower pos-rates). The RF's higher *true* F1 here (0.61 vs India's 0.08) is that balanced eval set, not a stronger baseline — its true AUROC is still only 0.643.
- **Spatially adjacent train/test tiles.** Unlike India (test chips well separated, 0/175 adjacent), 69/72 Vietnam test chips — and 34/52 Kenya — border a *train* chip from the same Sentinel-2 scene, so their **absolute** scores are spatially optimistic. This bias is common-mode across the true and proxy arms, so it **cancels in the paired contrasts** the headline rests on; the **scene-disjoint robustness check below** confirms the flip survives a tile-held-out split (with the caveats noted there).

### Fourth region: France — the "negative control" that wasn't (large fields, flip persists)

We added FTW-France (2020; 800 chips, 71k polygons, **69% of fields > 1 ha**) as an intended **large-field negative control** — the hypothesis being that for big regular fields WorldCover ≈ true boundaries, so the flip should vanish. **It did not.** Controlled, same-pixel (282,547 px, chip overlap 0; independently verified as a real finding, not a bug):

| Model | TRUE — AUROC / F1 | WC-proxy — AUROC / F1 |
|---|---|---|
| Prithvi-EO-2.0-300M | **0.961 / 0.910** | 0.949 / 0.914 |
| TerraMind v1 base | 0.951 / 0.894 | 0.951 / 0.915 |
| AnySat (dense) | 0.943 / 0.884 | 0.967 / 0.939 |
| Clay v1 | 0.501 / 0.485 | 0.707 / 0.722 |
| **RF / spectral** | **0.695 / 0.666** | **0.959 / 0.946** |

*Artifacts: `ftw_controlled_label_comparison_france.json`, `eval_per_pixel_ftw_france_*`, `ftw_bootstrap_ci_france.json`.*

The flip **persists**: the proxy lifts the RF from AUROC 0.695 → 0.959 (paired RF proxy−true F1 **+0.279 [0.266, 0.293]**) while the FMs still beat it on true (paired bestFM−RF true AUROC **+0.266 [0.248, 0.285]**). **Why the negative control failed — the key mechanistic insight:** even in big-field France, FTW true fields tile only **~11%** of the scene while WorldCover labels **~66%** as cropland, so **~62% of true-*negative* pixels are WC-"cropland"** (`ftw_proxy_mismatch_coverage.json`). The proxy therefore still hands the spectral RF an easy "is this managed/vegetated land?" task instead of true field-membership, *regardless of field size*. So the conclusion-flip is **a general property of the proxy, not a smallholder quirk** — a broader and more defensible claim than we set out to test.

### Fifth region: Netherlands — the large-field endpoint (the flip nearly closes)

FTW-Netherlands (2022; 800 chips, 56k polygons, 54% > 1 ha) is a **second large-field control**, and the most extreme. Controlled, same-pixel (273,657 px, chip overlap 0; double-checked — recomputed exactly from raw arrays):

| Model | TRUE — AUROC / F1 | WC-proxy — AUROC / F1 |
|---|---|---|
| AnySat (dense) | **0.961 / 0.891** | 0.945 / 0.863 |
| Prithvi-EO-2.0-300M | 0.955 / 0.889 | 0.901 / 0.802 |
| TerraMind v1 base | 0.943 / 0.868 | 0.901 / 0.801 |
| Clay v1 | 0.498 / 0.486 | 0.583 / 0.523 |
| **RF / spectral** | **0.815 / 0.756** | **0.928 / 0.840** |

*Artifacts: `ftw_controlled_label_comparison_netherlands.json`, `eval_per_pixel_ftw_netherlands_*`, `ftw_bootstrap_ci_netherlands.json`.*

Netherlands is the **weakest flip of all five regions**: the spectral RF is already strong on *true* field-membership (AUROC 0.815 — Dutch fields are huge and spectrally homogeneous), so the best-FM−RF gap is the smallest (paired AnySat−RF true AUROC **+0.146 [0.133, 0.161]**) and the proxy inflates it least (paired RF proxy−true F1 **+0.084 [0.066, 0.102]**). The scene-disjoint check confirms this is not spatial autocorrelation: under a tile-held-out split RF-true holds at 0.797 and Prithvi-true at 0.955. **Caveat (independent audit):** NL differs from the cropland-saturated regions on *two* axes, not just field size — its landscape is grassland-dominated (WorldCover class-40/cropland ≈ 22% of pixels; proxy pos-rate 0.44, like Kenya, vs ~0.78 in the cropland-saturated India/Vietnam/France), so its weaker flip partly reflects a different, less cropland-confounded proxy as well as larger fields. NL anchors the large-field end of the gradient but is not a pure field-size manipulation.

### Cross-region synthesis (five regions)

The **direction is universal**: in all five countries — including the two large-field European controls (France, Netherlands) — the WorldCover proxy inflates the spectral baseline while true labels expose a significant FM advantage (every paired RF-proxy−true and bestFM−RF delta excludes 0; see significance table). The proxy fails everywhere because FTW true fields tile only a fraction of each scene while WorldCover calls most of it cropland/managed land, so the proxy rewards spectral land-cover detection rather than field membership.

But the **FM advantage on true field-membership has a clean field-size gradient** (read on AUROC): the spectral RF gets steadily *better* at true fields as fields grow — India 0.574 → Vietnam 0.643 → France 0.695 → **Netherlands 0.815** — and the best-FM−RF gap *shrinks* monotonically: **+0.41 → +0.29 → +0.27 → +0.15**. In plain terms, **foundation models help most where fields are smallest**; for large regular fields a per-pixel spectral baseline closes most of the gap on the true task. Crucially, **India, Vietnam, and France are all cropland-saturated** (proxy pos-rate ~0.77–0.80), so the India→France size contrast (**+0.41 → +0.27**) is a like-for-like field-size effect, *not* a land-cover confound; Netherlands then extends the trend to a large-field *grassland* landscape (and weakens it further, +0.15). (Two honest wrinkles: Kenya is an outlier — smallest fields but a muted +0.20 — because its sparse fragmented mosaic and small/noisy sample dominate; and Netherlands shifts land-cover composition alongside field size, so it is a supporting endpoint rather than a pure size manipulation.) Which GeoFM "wins" also flips by region (Prithvi/TerraMind in India/Vietnam/France, AnySat in Kenya/Netherlands).

### Scene-disjoint robustness (spatial-adjacency control)

The chip-grouped split leaves train/test chips spatially adjacent in the geographically-concentrated regions (Vietnam, Kenya, France span few Sentinel-2 tiles). We therefore re-ran the controlled comparison with the split **grouped by MGRS tile** (`--group-by tile`; `*_tilesplit.json`), so no test tile shares a scene with training:

| Region (tiles) | RF true→proxy AUROC, chip-split | RF true→proxy AUROC, **tile-split** | Prithvi true (chip → tile) |
|---|---|---|---|
| India (244) | 0.574 → 0.786 | 0.592 → 0.771 | 0.983 → 0.984 |
| Vietnam (16) | 0.643 → 0.911 | 0.616 → 0.849 | 0.929 → 0.922 |
| France (6) | 0.695 → 0.959 | 0.691 → 0.903 | 0.961 → 0.959 |
| Netherlands (7) | 0.815 → 0.928 | 0.797 → 0.915 | 0.955 → 0.955 |
| Kenya (6) | 0.651 → 0.806 | 0.552 → 0.591 | 0.766 → 0.761 |

**The flip survives scene-disjoint splitting** in India (decisive — 244 tiles, numbers essentially unchanged), Vietnam, France, and Netherlands: the transformer FMs (Prithvi/TerraMind) stay at 0.92–0.98 on true and the proxy still inflates the RF; importantly, the **elevated large-field RF-true is *not* a spatial-autocorrelation artifact** (NL RF-true 0.815→0.797, France 0.695→0.691 under tile-split). Two honest caveats: (1) **AnySat's true-field advantage does *not* survive** the tile split (Vietnam 0.897→0.645, France 0.943→0.605, NL 0.961→0.893) — it leans on within-tile spatial adjacency more than the transformer FMs, so the *robust* FM winners are **Prithvi/TerraMind**; (2) **Kenya/France/Netherlands have only 6–7 MGRS tiles**, so their tile-split is coarse and higher-variance (Kenya's becomes uninformative) — India, with 244 tiles, is the decisive robustness case.

## Statistical significance (chip-clustered bootstrap)

95% CIs from a bootstrap that resamples **test chips** with replacement (B = 1000), so uncertainty is clustered at the chip level (the unit of independence), not the pixel. Trained models are held fixed; the same chip resamples are used for the paired differences. Artifacts: `data/results/ftw_bootstrap_ci_{india,kenya,vietnam,france,netherlands}.json`.

| Quantity | India | Kenya | Vietnam | France | Netherlands |
|---|---|---|---|---|---|
| RF — TRUE F1 | 0.079 [.058,.102] | 0.074 [.046,.105] | 0.610 [.589,.631] | 0.666 [.654,.679] | 0.756 [.738,.773] |
| RF — PROXY F1 | 0.887 [.871,.901] | 0.660 [.587,.723] | 0.923 [.911,.934] | 0.946 [.939,.952] | 0.840 [.827,.851] |
| **Paired RF (proxy − true) F1** | **+0.808 [.781,.833]** | **+0.586 [.519,.641]** | **+0.313 [.294,.332]** | **+0.279 [.266,.293]** | **+0.084 [.066,.102]** |
| **Paired best-FM − RF, TRUE AUROC** | **+0.409 [.381,.44]** (Pr) | **+0.202 [.146,.267]** (An) | **+0.286 [.266,.305]** (Pr) | **+0.266 [.248,.285]** (Pr) | **+0.146 [.133,.161]** (An) |

(Pr = Prithvi, An = AnySat is the best FM in that region.) Both paired differences exclude 0 in all five regions: **the proxy's inflation of the spectral baseline, and the best FM's advantage on true fields, are statistically significant in all five regions.** The magnitudes follow the field-size gradient — largest for smallholder India, monotonically smaller toward large-field Netherlands (paired best-FM−RF true AUROC +0.41 → +0.15) — consistent with the synthesis above. **Multiple-comparison correction:** across all 10 paired tests (5 regions × 2 deltas), every delta survives both Benjamini-Hochberg (FDR 0.05) and Holm (0.05) — the corrections do not bite because the smallest effect (Kenya best-FM−RF, +0.20) is still ~6.5 SEs from 0 (`ftw_multiple_comparison.json`). (Vietnam's RF *true* F1 of 0.61 is high only because of its balanced eval set — see the Vietnam note; on AUROC the gap is clear.) **Caveat for Kenya:** only **AnySat** clearly separates from the RF on true-label AUROC (0.853 [0.825, 0.881] vs RF 0.651 [0.576, 0.719]); Prithvi's and TerraMind's true-AUROC CIs **overlap** the RF's, so in Kenya the "FMs beat the baseline on true fields" claim is carried by AnySat alone (on F1, the RF is decisively worst in both regions — CIs disjoint from every FM).

## What we do NOT claim (framing discipline)

These caveats were raised by two independent verification passes and are honored here:

1. **TRUE and PROXY are different tasks**, not two measurements of one task. TRUE measures *field membership* (which the FMs solve via within-field interior context, not edge resolution — see control below); PROXY measures *cropland detection*. The claim is **"foundation models supply spatial structure for field mapping that per-pixel spectral features lack,"** *not* "foundation models detect cropland better" — under the proxy they do not pull away: the spectral RF is competitive with them (best F1 in the controlled run; within ~0.05 AUROC of the leaders in the standalone run).
2. **No precise size-recall slope.** The proxy cannot even *populate* the smallest field-size bins — under WorldCover labels the smallest bin (<0.1 ha) collapses from **n = 1325 (true) to n = 50 (proxy)**, a ~26× depopulation, and >96% of proxy-positive mass lands in the largest bin plus `uncovered_target`. Any "recall vs field size" gradient on proxy labels therefore rides on tens of pixels and is statistically fragile. We report this as **"the proxy cannot measure smallholder fields,"** not as a clean gradient comparison. (Counts: per-pixel `<0.1ha` bin, `*_chip.json` per-size blocks.)
3. **Clay collapses on true fields too** (0.577). The discriminating signal is a property of *some* FMs (Prithvi/TerraMind/AnySat), not "FMs" monolithically.
4. **The FM advantage is within-field interior context, NOT boundary delineation** (resolved by the boundary-zone control in Limitations: at field edges all models, FMs included, drop to ≈0.58 AUROC). The strong FMs win on the true-field task because they pool spatial context a per-pixel RF cannot — interior homogeneity, not edge semantics. We never claim they resolve field boundaries.

## Limitations & the open control

- **Within-field interior context vs boundary delineation (control RUN — important).** A chip-grouped split removes train↔test *chip* leakage (overlap = 0), but not the advantage a context-pooling FM gets from neighbouring *test* pixels that share a label inside the same field. We ran the discriminating control: re-extract the India TRUE features at **boundary-zone pixels only** (within 3 px of a field edge, both classes balanced; `--boundary-zone-px 3`) and re-evaluate. If the FM advantage were boundary delineation it would survive; if it were within-field interior context it would vanish.

  | Model | TRUE, **all** pixels (AUROC) | TRUE, **boundary-zone** (AUROC / F1) |
  |---|---|---|
  | Prithvi | 0.983 | 0.576 / 0.46 |
  | TerraMind | 0.967 | 0.584 / 0.47 |
  | AnySat | 0.939 | 0.582 / 0.46 |
  | Clay | 0.577 | 0.571 / 0.46 |
  | RF / spectral | 0.574 | 0.586 / 0.16 |

  *Artifact: `data/results/ftw_edge_zone_eval_india.json` (203,864 boundary-zone px, pos-rate 0.37, overlap 0).* **Result: every model — FMs included — collapses to ≈0.58 AUROC at boundaries** (the RF is marginally highest). So the strong FMs' true-field advantage comes entirely from pixels *far* from boundaries (field interior vs non-field interior), **not** from resolving field edges. At 10 m, where boundary pixels are spectrally mixed and the label is ambiguous, no model wins. **This is the honest scope of the finding: FMs exploit within-field interior context that per-pixel spectra lack — they do not delineate field boundaries.** It does *not* weaken the conclusion-flip (which is about the full-pixel proxy-vs-true verdict), but it forbids any "FMs understand field boundaries" reading.
- **Five regions, one sensor.** India India + Kenya + Vietnam + France + Netherlands, Sentinel-2 L2A only. The proxy-inflation flip is seen in all five (incl. two large-field European controls), and the FM advantage shows a clean monotonic field-size gradient. Remaining gaps: the gradient mixes field size with land-cover composition at the Netherlands endpoint (its proxy is less cropland-confounded), and Kenya is an unresolved outlier; more countries at intermediate field sizes would sharpen the curve.
- **Spatial adjacency in the chip-grouped split (region-dependent), addressed by a scene-disjoint check.** Chip-grouping eliminates same-chip leakage (overlap = 0 everywhere), but the geographically-concentrated regions (France 6 tiles, Kenya 6, Vietnam 16) have adjacent train/test chips, so their *absolute* chip-split scores are spatially optimistic; India (244 tiles) is clean. The scene-disjoint (`--group-by tile`) robustness check confirms the flip survives in India/Vietnam/France; its limits (AnySat fragility; Kenya/France too few tiles) are reported in that section. The headline rests on **paired** within-split contrasts, which are common-mode to this bias.
- **2016 imagery** matched to FTW's India acquisition window; cloud-screened least-cloud scene per chip.
- **Proxy positives are inherently coarser**, so the two label sets differ in class balance (true pos-rate 0.35 vs proxy 0.78); the *controlled* table neutralizes this by fixing the pixels, which is why it is the headline.

## Methodology / provenance

- **True labels:** FTW instance masks → field polygons (`scripts/ftw_to_polygons.py`), re-keyed to our pulled-S2 chip IDs (`polygons_ftw_india_keyed.parquet`). Area in true local UTM.
- **Proxy labels:** ESA WorldCover class 40 (cropland) over the same chips.
- **Features:** per-pixel FM token upsampled to pixel grid (`scripts/extract_features_per_pixel.py`, `--positive-from-polygons` for TRUE mode); spectral baseline = 30-d hand-crafted S2 features (`scripts/eval_nonfm_baseline_per_pixel.py`).
- **Splits:** chip-grouped `GroupShuffleSplit` (seed 20260514), so all pixels of a 256-px chip fall in one side — no *cross-chip* leakage (overlap = 0, recorded in JSON). Within-chip autocorrelation is not removed by this; see the open control above.
- **Harness fixes applied this round:** (a) FM eval records split/chip-overlap in JSON; (b) spectral-RF eval switched to split-then-mask so its chip partition is byte-identical to the FM eval; (c) extractor excludes S2 no-data/all-zero pixels from the negative pool.
