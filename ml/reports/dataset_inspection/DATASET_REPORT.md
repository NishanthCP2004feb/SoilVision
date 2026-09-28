# Dataset Inspection Report

Generated: 2026-08-10T17:01:09.798880+00:00

## Summary

- Dataset root: `Orignal-Dataset`
- Valid images: 1189
- Corrupted or unsupported files: 0
- Classes: 7
- Pixel dimensions: 140–3888 wide × 101–2592 high

## Class distribution

| Class | Images | Share |
| --- | ---: | ---: |
| Alluvial_Soil | 52 | 4.4% |
| Arid_Soil | 284 | 23.9% |
| Black_Soil | 255 | 21.4% |
| Laterite_Soil | 219 | 18.4% |
| Mountain_Soil | 201 | 16.9% |
| Red_Soil | 109 | 9.2% |
| Yellow_Soil | 69 | 5.8% |

## Leakage and cleaning findings

- Exact-duplicate pairs: 50
- Near-duplicate pairs (pHash distance ≤ 6): 47
- Cross-class duplicate/near-duplicate pairs requiring label review: 4
- Related-image groups that must not cross train/validation/test boundaries: 82
- The dataset is materially imbalanced; class-weighted loss and macro-F1 are required for model selection.
- Do not remove or split the original files in place. A later split must operate from the generated manifest and preserve every related-image group.

## Scientific label availability

The dataset contains image files arranged by soil class only. It contains no image-level pH, N, P, K, moisture, organic-carbon, EC, weather, or location labels. This release therefore supports soil-type classification only; soil-property regression must remain unavailable until ground-truth measurements are supplied.

## Generated artifacts

- `dataset_report.json`: machine-readable audit
- `image_manifest.csv`: image metadata and hashes
- `duplicate_pairs.json`: records to group/review before splitting
- `representative_samples.jpg`: deterministic visual sample sheet
