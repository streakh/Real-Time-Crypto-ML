# Drift Summary — Train vs Test

Source report: [`handoff/reports/train_vs_test.html`](../handoff/reports/train_vs_test.html) (Evidently 0.4.33).

## Setup

- **Reference dataset:** training-period feature rows (chronological train split).
- **Current dataset:** held-out test split (later in time, no overlap with reference).
- **Statistical tests:** Wasserstein distance (normed) for numeric features; Jensen-Shannon distance for the binary `vol_spike` label.
- **Drift threshold:** Evidently default — flag when test statistic exceeds the per-test threshold (Wasserstein default 0.1).

## Per-feature drift scores

| Feature | Test | Score | Interpretation |
|---|---|---:|---|
| `trade_intensity_60s` | Wasserstein | **0.4191** | **Drifted** — large shift in tick-arrival rate between train and test windows |
| `n_ticks_60s` | Wasserstein | **0.4191** | **Drifted** — same underlying signal as `trade_intensity_60s` (perfect correlation), explains the identical score |
| `spread_mean_60s` | Wasserstein | **0.1918** | **Drifted** — liquidity regime changed; bid-ask spreads tightened/widened relative to training period |
| `vol_spike` (target) | Jensen-Shannon | 0.0974 | Borderline — class balance shifted modestly between periods |
| `spread_bps` | Wasserstein | 0.0116 | Stable |
| `vol_60s` | Wasserstein | 0.0041 | Stable |
| `log_return` | Wasserstein | 0.0010 | Stable |
| `mean_return_60s` | Wasserstein | 0.0001 | Stable |

## Top-line findings

1. **The two highest-drift features (`trade_intensity_60s`, `n_ticks_60s`) are the same signal** — both count ticks per second over a 60 s window, just expressed differently. The 0.42 Wasserstein score indicates BTC trading activity in the test window is materially different from the training window (likely a different market regime: weekend/weekday split, a US-vs-Asia session shift, or a volatility cluster in one period not the other).
2. **`spread_mean_60s` drifted moderately (0.19)** — consistent with the liquidity-regime hypothesis above.
3. **Returns and volatility themselves did not drift** — `log_return`, `mean_return_60s`, and `vol_60s` are all near zero. Price-action distribution is stable; what changed is *how busy* the order book was.
4. **The label (`vol_spike`) shows mild drift (0.097)** — class balance moved slightly, which is the expected downstream effect of the activity shift but small enough not to require relabeling.

## Implications for the served model

- The LR pipeline uses `trade_intensity_60s`, `n_ticks_60s`, and `spread_mean_60s` as features, so test-time predictions are extrapolating into a region of feature space the model saw less of during training. This is the most plausible explanation for the modest val→test PR-AUC gap noted in `handoff/SELECTED_BASE_NOTE.md`.
- No immediate action needed — the model still beats the z-score baseline on test PR-AUC (0.146 vs 0.134). But this is the canonical signal to **retrain on a more recent window** before promoting to production.

## How to regenerate

```bash
# Compares the reference (training feature slice) against whatever the live
# featurizer has written to data/processed/features.parquet.
python scripts/drift_report.py \
  --reference handoff/data_sample/features_slice.csv \
  --current   data/processed/features.parquet \
  --out       reports/drift_$(date +%Y%m%d).html
```

The script reuses the same Evidently version pinned in `handoff/requirements.txt` so output is byte-comparable to the original report.
