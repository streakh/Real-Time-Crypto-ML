# Selected-base

This handoff uses the Logistic Regression pipeline in `handoff/models/artifacts/lr_pipeline.pkl` as the selected-base model. The shipped artifact is a **composite**: the Logistic Regression algorithm is paired with the feature set chosen by a teammate-led ablation study in the EDA notebook, not simply the first feature list that produced a working model.

## Composite Model Rationale

The "composite" here refers to how the two halves of the model were chosen independently and then combined:

- **Algorithm half — Logistic Regression.** Selected for operational reasons: fast to train, easy to serve, transparent coefficients, and it is the model family the current project runtime (`models/train.py`, `models/infer.py`) expects.
- **Feature half — Variant B from the ablation study.** Selected empirically by a structured feature-ablation experiment a team member ran in the EDA, not by intuition. The ablation compared four feature variants under **identical LR hyperparameters** (`C=0.1`, `class_weight="balanced"`, `solver="lbfgs"`, `max_iter=1000`), with the operating threshold chosen on validation best-F1 and the winner picked by **validation PR-AUC**.

### Ablation Variants Compared

| Variant | # Features | Description |
|---|---|---|
| A | 6 | Baseline: `log_return`, `spread_bps`, `vol_60s`, `mean_return_60s`, `trade_intensity_60s`, `n_ticks_60s` |
| **B (winner)** | **7** | **A + `spread_mean_60s`** (smoothed liquidity signal) |
| C | 8 | B + `price_range_60s` (full candidate set) |
| D | 7 | C minus `n_ticks_60s` [^1] |

[^1]: The `ablation_results.json` rationale for Variant D literally says *"C minus `spread_abs` and `n_ticks_60s`"*, but `spread_abs` is not part of Variant C's feature list, so dropping it from C is a no-op. The only operative drop between C and D is `n_ticks_60s`. `spread_abs` was flagged as redundant by the correlation analysis in the EDA (separate from the ablation run), which is why it never entered the variant candidate set in the first place — it was not dropped from C.

Full per-variant metrics are recorded in `reports/ablation_results.json`, and the analysis and decision narrative live in `notebooks/eda.ipynb` under the "Feature Ablation Study" section.

### Why Variant B Won

- **Highest validation PR-AUC.** B edges out the 6-feature baseline (A) because adding `spread_mean_60s` contributes a smoothed liquidity signal the baseline was missing.
- **Adding more features did not help.** Variant C (B + `price_range_60s`) scored slightly lower on validation PR-AUC than B, so `price_range_60s` was not adopted.
- **C and D produced identical metrics** (same `val_pr_auc`, `val_f1`, `tau`, etc.), confirming that `n_ticks_60s` is redundant with `trade_intensity_60s` / `price_range_60s` already in the model rather than adding new signal. `spread_abs` had already been flagged as redundant in the EDA correlation analysis and was not part of the ablation variant set.
- **The val-to-test PR-AUC gap is roughly constant across all four variants**, which points to temporal regime drift between splits rather than overfitting to any specific feature set — so the decision was not distorted by one variant being lucky on the held-out window.

Decision recorded in the EDA: **adopt Variant B (baseline + `spread_mean_60s`) as the production feature set.** The shipped LR pipeline in `lr_pipeline.pkl` is trained on exactly this 7-feature set, with the saved threshold `bundle["tau"]` (currently `0.7015`).

## Exact Steps

1. Create and activate a Python 3.11 virtual environment, then install `handoff/requirements.txt`.
2. Copy `handoff/.env.example` to `.env` from the repo root.
3. Start the services with `docker compose -f handoff/docker/compose.yaml up -d`.
4. Load `handoff/models/artifacts/lr_pipeline.pkl`, read the saved threshold from `bundle["tau"]` (currently `0.7015`), and score `handoff/data_sample/features_slice.parquet` or another compatible Parquet features file.

## Why This Is The Base

- It is the same model family the current project runtime expects.
- It slightly outperforms the z-score baseline on both validation and held-out test PR-AUC under the current chronological split.
- Its feature set is the empirical winner of a documented ablation study (Variant B), not an ad-hoc choice.
- The handoff package includes the matching artifact checksum, metadata, evaluation PDF, Evidently report, ablation results JSON, and predictions file.
