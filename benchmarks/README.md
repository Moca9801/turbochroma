# Benchmarks

Reproducible performance and accuracy measurements for `turbochroma`.

## Planned scripts (land in subsequent commits)

| Script | Purpose |
|---|---|
| `synthetic_mae.py` | MAE / compression ratio on synthetic L2-normalized vectors. Port of Minervia's `benchmark_turbo.py`, extended with CLI flags and JSON output. |
| `beir_nfcorpus.py` | Recall@10 and MRR@10 on BEIR NFCorpus, comparing Chroma vanilla (float32) vs `turbochroma` SQ8 vs FAISS SQ8 (baseline). |
| `memory_footprint.py` | RAM peak measurement for 100k / 1M chunks, BGE-M3 1024d. |

## Install extras

```bash
pip install -e ".[bench]"
```

## Output convention

All benchmarks emit a `benchmarks/outputs/<script>_<timestamp>.json` file
(gitignored) plus a short markdown summary to stdout. CI consumers can parse
the JSON for regression tracking.
