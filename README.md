# frozen-not-finetuned-eval

### Frozen, Not Fine-tuned — A Controlled Evaluation of Geospatial Foundation Models for Agricultural Field Mapping

How good are geospatial foundation models (GeoFMs) at mapping agricultural fields from
satellite imagery — *really*? This repository shows that the answer reported by common
benchmarks is distorted by **two evaluation choices**, and provides a controlled,
same-pixel apparatus to measure the effect across six countries.

> **One-line takeaway:** evaluate GeoFMs against *true field labels* and a *strong
> supervised baseline*, and the popular "foundation models win" story largely collapses —
> a **frozen** backbone matches fine-tuning in-region and transfers better out-of-region,
> while a from-scratch U-Net is competitive in most regions.

---

## The problem

Most GeoFM field-mapping benchmarks make two convenient choices that both flatter the
foundation model:

1. **Proxy labels.** Instead of true field boundaries, they use a land-cover *cropland mask*
   (e.g. ESA WorldCover) as the target. This is an easier, smoother label that inflates weak
   baselines and changes which model "wins."
2. **Weak baselines.** They compare GeoFMs against per-pixel classifiers (e.g. a random
   forest on spectral bands) rather than a strong supervised segmentation model, exaggerating
   the apparent GeoFM advantage.

We isolate each effect by evaluating every model on the **same pixels**, swapping only the
label source (true [Fields of The World](https://fieldsofthe.world) boundaries vs. the
WorldCover cropland proxy) and the baseline strength.

## Headline results

In-region test AUROC (mean over 3 seeds), per country:

| Country     | RF (true labels) | RF (proxy labels) | U-Net (scratch) | Prithvi-2.0 (fine-tuned) | Frozen GeoFM | Verdict     |
|-------------|:----------------:|:-----------------:|:---------------:|:------------------------:|:------------:|-------------|
| India       | 0.574            | **0.786**         | 0.909           | 0.983                    | 0.983        | FM          |
| Cambodia    | 0.550            | **0.900**         | 0.948           | 0.949                    | 0.924        | tie         |
| Vietnam     | 0.643            | **0.911**         | 0.962           | 0.951                    | 0.929        | tie         |
| Kenya       | 0.651            | **0.806**         | 0.887           | 0.763                    | 0.853        | **U-Net**   |
| France      | 0.695            | **0.959**         | 0.977           | 0.978                    | 0.961        | tie         |
| Netherlands | 0.815            | **0.928**         | 0.981           | 0.959                    | 0.961        | tie         |

Read across one row and three things jump out:

- **Flaw 1 (proxy labels):** the random forest's score leaps (e.g. India 0.574 → 0.786) just
  by switching to the proxy label — *the same model, the same pixels*. Proxy labels reward the
  weak baseline and shrink the gap the benchmark is trying to measure.
- **Flaw 2 (weak baselines):** a properly-trained from-scratch **U-Net is competitive with, or
  beats, fine-tuned GeoFMs** in most regions — the "huge FM lead" is largely an artifact of the
  baseline being a per-pixel classifier.
- **Boundary condition:** under extreme label sparsity (Kenya, ~0.1% positive pixels) the
  supervised U-Net wins outright.

And the central practical finding — **frozen, not fine-tuned**:

- A **frozen** GeoFM backbone with a trainable decoder *matches* full end-to-end fine-tuning
  in-region (5 of 6 regions, for both Prithvi-EO-2.0 and TerraMind).
- Fine-tuning **hurts cross-region transfer** — consistent with
  [Kumar et al. (2022)](https://arxiv.org/abs/2202.10054): fine-tuning distorts pretrained
  features out-of-distribution.
- The frozen route trains **~110× fewer parameters** at matched accuracy.

## What's in this repository

```
paper/            LaTeX sources + compiled PDFs (TMLR style),
                  croissant.json (machine-readable + Responsible-AI metadata), ARTIFACT.md
scripts/          Pipeline: label prep, canonical split, controlled same-pixel comparison,
                  supervised U-Net, GeoFM fine-tune/probe, cross-region transfer, integrity checks
src/ftw_eval/   Importable package (model zoo: Clay, Prithvi-EO-2.0, TerraMind, AnySat; data utils)
data/results/     All derived metric JSONs (committed + SHA-256 checksummed)
docs/             Per-country reproduction guide, corrected-evaluation protocol, label-validity results
tests/            Unit tests
```

Raw imagery (Sentinel-2, ESA WorldCover, FTW polygons) is **not redistributed** — it is pulled
from its open sources by the scripts. See [`docs/FTW_REPRODUCE.md`](docs/FTW_REPRODUCE.md).

## Quickstart

```bash
pip install -e .                      # Python 3.11
python scripts/checksums.py --verify  # confirm released metric artifacts are intact
```

Reproduce a single country end-to-end (GEE auth required for the data pull):

```bash
C=india
bash   scripts/prep_ftw_country.sh $C                 # FTW labels + polygons
bash   scripts/run_ftw_country.sh  $C                 # Sentinel-2 + WorldCover pull, features
python scripts/ftw_export_split.py --country $C       # canonical chip-grouped split
python scripts/ftw_controlled_label_comparison.py --country $C   # true vs proxy, same pixels
python scripts/ftw_unet_baseline.py --robust $C       # strong supervised baseline
python scripts/ftw_finetune_fm.py --model prithvi --freeze backbone $C   # frozen probe
python scripts/ftw_finetune_fm.py --model prithvi $C                     # full fine-tune
```

Full pipeline, per-model recipes, and verification steps are in
[`paper/ARTIFACT.md`](paper/ARTIFACT.md).

## Data & licenses

- **Fields of The World** (field boundaries) — CC-BY-4.0
- **ESA WorldCover** 10 m v200 (cropland proxy) — CC-BY-4.0
- **Sentinel-2** L2A — Copernicus, free & open
- **This repository:** code under [Apache-2.0](LICENSE); derived metrics & documentation under CC-BY-4.0.

## Citation

This work is under peer review. A BibTeX entry will be added on publication; in the meantime
please cite the paper title above and link to this repository.
