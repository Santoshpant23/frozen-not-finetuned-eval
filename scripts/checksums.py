#!/usr/bin/env python
"""Canonical-artifact checksums (reproducibility / staleness guard).

Writes SHA-256 for every canonical result + key provenance file to
`data/results/CHECKSUMS.sha256`. In --verify mode, recomputes and FAILS
(exit 1) on any mismatch or missing file — so a reviewer (or CI, or
`reproduce_all`) can detect stale/edited artifacts.

Canonical set = data/results/*_chip.json (excluding archive_preaudit/) +
paired_significance.json + ftw_proxy_sensitivity_*.json + docs/RESULTS.md +
requirements.lock + data/chips/manifest_*.jsonl + data/index/*.jsonl.

    python scripts/checksums.py            # write CHECKSUMS.sha256
    python scripts/checksums.py --verify   # check, exit 1 on drift
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "results" / "CHECKSUMS.sha256"


def canonical_files() -> list[Path]:
    fs: list[Path] = []
    res = ROOT / "data" / "results"
    fs += [p for p in sorted(res.glob("*_chip.json"))]
    for extra in ("paired_significance.json",):
        if (res / extra).exists():
            fs.append(res / extra)
    fs += sorted(res.glob("ftw_proxy_sensitivity_*.json"))
    fs += sorted(res.glob("xseason_*.json"))
    fs += sorted(res.glob("cross_region_*.json"))
    for p in [ROOT / "docs" / "RESULTS.md", ROOT / "requirements.lock"]:
        if p.exists():
            fs.append(p)
    fs += sorted((ROOT / "data" / "chips").glob("manifest_*.jsonl"))
    fs += sorted((ROOT / "data" / "index").glob("*.jsonl"))
    fs += sorted(res.glob("ftw_*.json"))  # FTW controlled/bootstrap/tilesplit/coverage/edge artifacts
    fs = list(dict.fromkeys(fs))  # dedupe (ftw_*_chip.json also matched *_chip.json)
    # never include the archive
    return [p for p in fs if "archive_preaudit" not in p.parts]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def rel(p: Path) -> str:
    return str(p.relative_to(ROOT)).replace("\\", "/")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()

    files = canonical_files()
    current = {rel(p): sha256(p) for p in files}

    if not args.verify:
        OUT.write_text("".join(f"{h}  {f}\n" for f, h in sorted(current.items())))
        print(f"wrote {rel(OUT)} ({len(current)} files)")
        return 0

    if not OUT.exists():
        print(f"[ERROR] {rel(OUT)} missing — run without --verify first")
        return 1
    recorded = {}
    for line in OUT.read_text().splitlines():
        if line.strip():
            h, f = line.split(None, 1)
            recorded[f.strip()] = h
    drift = []
    for f, h in current.items():
        if f not in recorded:
            drift.append(f"NEW (uncommitted): {f}")
        elif recorded[f] != h:
            drift.append(f"CHANGED: {f}")
    for f in recorded:
        if f not in current:
            drift.append(f"MISSING: {f}")
    if drift:
        print(f"[FAIL] {len(drift)} checksum drift(s):")
        for d in drift:
            print("  " + d)
        return 1
    print(f"[OK] {len(current)} canonical artifacts match CHECKSUMS.sha256")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
