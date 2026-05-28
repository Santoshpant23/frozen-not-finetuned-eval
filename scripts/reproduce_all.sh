#!/usr/bin/env bash
# Reproduce released metric artifacts (per country).
set -e
PY=python
for C in india cambodia vietnam kenya france netherlands; do
  $PY scripts/ftw_export_split.py --country "$C"
  $PY scripts/ftw_controlled_label_comparison.py --country "$C"
  $PY scripts/ftw_unet_baseline.py --robust "$C"
  $PY scripts/ftw_finetune_fm.py --model prithvi --freeze backbone "$C"
  $PY scripts/ftw_finetune_fm.py --model prithvi "$C"
done
$PY scripts/checksums.py --verify
echo "Reproduce complete."
