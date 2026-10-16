# Block missingness in non-laboratory HbA1c screening (NHANES)

Code, locked protocol and results for the study:

> *Block-masking augmentation versus reduced-feature pattern submodels for missing blocks of non-laboratory inputs in a machine-learning screening tool for elevated HbA1c: a protocol-locked temporal validation in NHANES* (manuscript in preparation for submission; this repository was first described under the working title "One model or many? ...").

Author: Phuc Dinh Truong (ORCID [0009-0008-2149-478X](https://orcid.org/0009-0008-2149-478X)), independent researcher, Khanh Hoa, Viet Nam. Archived copy of version 1.0 on Zenodo: [10.5281/zenodo.23413197](https://doi.org/10.5281/zenodo.23413197) (all versions: [10.5281/zenodo.23413196](https://doi.org/10.5281/zenodo.23413196)).

- **Development:** NHANES 2017–March 2020.
- **Temporal validation:** NHANES August 2021–August 2023.
- **Outcome:** HbA1c ≥6.5% in adults without diagnosed diabetes.
- **Primary comparison:** block-masking augmentation (M-AUG, one model) vs reduced-feature pattern submodels (M-PS, one model per missingness pattern), with a model not trained for block missingness (M-BASE) as reference.
- **Primary measure:** survey-weighted Brier skill, with design-based (JK2) confidence intervals.

## Study integrity

| Item | File |
|---|---|
| Protocol that was locked | `protocol_v0.4.md` (inherits `protocol_v0.3.md`) |
| All design decisions made before the lock | `decision_log.md` (D-01 to D-45) |
| Lock file (SHA-256 of protocol, decision log, code and trained models) | `LOCK_protocol_v0.4.json` |
| Events after the lock (single run on validation data, post hoc analyses) | `decision_log_postlock.md` |

Verify that the locked files are unchanged:

```bash
python -c "import sys; sys.path.insert(0,'src'); import final_pipeline as fp; from pathlib import Path; fp.verify_lock(Path('.'), Path('LOCK_protocol_v0.4.json')); print('LOCK OK')"
```

The `.gitattributes` file (`* -text`) keeps file bytes identical across operating systems, so the hashes remain verifiable after cloning.

## Repository layout

| Path | Content |
|---|---|
| `src/nhanes_audit.py` | Download, merge, cleaning and cohort construction (the same function for both cycles) |
| `src/dev_pipeline.py` | Development-only pilot (fixed LightGBM) |
| `src/final_pipeline.py` | Locked pipeline: models, metrics, JK2 inference, lock utilities |
| `notebooks/01_data_audit.py` / `.ipynb` | Data audit (downloads public NHANES files from CDC) |
| `notebooks/02_dev_P_only.py`, `02b_dev_LR_P_only.py` | Development-data pilots (no validation data) |
| `notebooks/03a_train_P.py` | Stage A: tuning and training on development data |
| `notebooks/04_make_lock.py` | Creates the lock file |
| `notebooks/03b_evaluate_L.py` | Stage B: single evaluation on validation data (refuses to run without a valid lock or if predictions already exist; `DRYRUN=1` tests on development data) |
| `notebooks/05_posthoc.py` | Post hoc analyses (labelled as such) |
| `notebooks/08_posthoc_review.py` | Post hoc round 2 (seed spread, paired AUROC against the Bang score, questionnaire-only submodel, per-scenario equivalence) |
| `notebooks/10a_posthoc_label57_by_scenario.py`, `10b_posthoc_all_patterns.py` | Post hoc round 3: outcome HbA1c ≥5.7% by scenario; all 15 block-missing patterns (reduced-feature submodels for 16 patterns; augmentation over 15 patterns). Plan: `addendum_posthoc_round3_20261014.md` |
| `notebooks/10c_posthoc_C_grid_extension.py` | Post hoc round 4: extension of the regularization grid in the development data only. Plan and results: `addendum_posthoc_round4_20261014.md` |
| `notebooks/06_figures*.py`, `07_figures_hiss.py` | Figures (`07_figures_hiss.py` writes `manuscript/figures/`, which is not in this repository) |
| `audit_out/`, `dev_out/`, `final_out/`, `posthoc_out/` | Numerical outputs |
| `RESULTS_protocol_v0.4.md`, `POSTHOC_REPORT.md` | Result reports |
| `integration_A4.md`, `literature_extraction.md`, `search_log.md` | Evidence integration and literature search log |

## Reproducing

```bash
pip install -r requirements.txt
python notebooks/01_data_audit.py      # downloads about 20 public .xpt files into data/raw/
python notebooks/03a_train_P.py        # stage A (development data only)
python notebooks/03b_evaluate_L.py     # stage B: needs the lock; refuses to overwrite existing predictions
python notebooks/05_posthoc.py         # post hoc (also downloads P_WHQ / WHQ_L)
python notebooks/08_posthoc_review.py  # post hoc round 2
python notebooks/10a_posthoc_label57_by_scenario.py   # post hoc round 3A
python notebooks/10b_posthoc_all_patterns.py          # post hoc round 3B (a few minutes)
python notebooks/10c_posthoc_C_grid_extension.py      # post hoc round 4 (development data only)
```

Run all scripts from the repository root.

Retraining on another machine may give tiny numerical differences, and the retrained model file will not match the hash in the lock. The locked `final_out/models_P.pkl` and `final_out/L_predictions.csv` are therefore included so that the reported results can be checked directly.

## Data

NHANES public-use files are available from the National Center for Health Statistics: <https://wwwn.cdc.gov/nchs/nhanes/>. Raw data are not redistributed here.

## Use of AI tools

Claude (Anthropic) assisted with literature searching, protocol drafting, code writing, running the analyses and drafting reports, under the authors' direction. See the Methods of the manuscript.

## License

Code (`src/`, `notebooks/`): MIT licence (see `LICENSE`). Result files and documentation (`*_out/`, `*.md`): CC BY 4.0. NHANES data are not redistributed and remain subject to the National Center for Health Statistics terms.

## How to cite

See `CITATION.cff`. The study is reported in the manuscript named at the top of this file; once it is published, please cite the article.
