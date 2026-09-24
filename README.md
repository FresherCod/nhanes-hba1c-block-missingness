# Block missingness in non-laboratory HbA1c screening (NHANES)

Code, locked protocol and results for the study:

> *One model or many? Handling missing blocks of non-laboratory information in a machine-learning screening tool for elevated HbA1c: a protocol-locked temporal validation in NHANES* (manuscript in preparation).

- **Development:** NHANES 2017–March 2020.
- **Temporal validation:** NHANES August 2021–August 2023.
- **Outcome:** HbA1c ≥6.5% in adults without diagnosed diabetes.
- **Primary comparison:** block-masking augmentation (one model) vs pattern submodels (one model per missingness pattern).
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
| `notebooks/06_figures*.py`, `07_figures_hiss.py` | Figures |
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
```

Run all scripts from the repository root.

Retraining on another machine may give tiny numerical differences, and the retrained model file will not match the hash in the lock. The locked `final_out/models_P.pkl` and `final_out/L_predictions.csv` are therefore included so that the reported results can be checked directly.

## Data

NHANES public-use files are available from the National Center for Health Statistics: <https://wwwn.cdc.gov/nchs/nhanes/>. Raw data are not redistributed here.

## Use of AI tools

Claude (Anthropic) assisted with literature searching, protocol drafting, code writing, running the analyses and drafting reports, under the authors' direction. See the Methods of the manuscript.

## License

Not yet specified (private repository).
