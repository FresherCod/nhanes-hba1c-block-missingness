# Abstract draft (TRIPOD+AI structure) — needs author review

**Title (working):** Handling missing blocks of non-laboratory information in screening for elevated HbA1c: block-masking augmentation versus pattern submodels, with temporal validation in NHANES 2021–2023

**Background.** Non-laboratory risk tools for undiagnosed dysglycemia are often used when whole groups of inputs, such as body measurements or questionnaire sections, are unavailable. How to handle such block missingness at deployment has not been compared for this use case.

**Methods.**
- *Design and prespecification.* Protocol prespecified and locked (hash-verified) before the temporal validation data were analysed.
- *Participants and outcome.* Adults ≥20 years without self-reported diabetes, not taking glucose-lowering pills, and not pregnant. Outcome: HbA1c ≥6.5%.
- *Data.* Development: NHANES 2017–March 2020 (n = 6,644; 237 events). Temporal validation: NHANES August 2021–August 2023 (n = 4,826; 128 events).
- *Predictors.* Four maskable blocks: anthropometry, measured blood pressure, medical history, and lifestyle/socioeconomic factors; plus age, sex and race/ethnicity.
- *Models compared.* Penalized spline logistic regression trained with random block-masking augmentation (one model) versus pattern submodels (one model per missingness pattern) versus no missing-data handling.
- *Evaluation.* Primary estimand: difference in survey-weighted Brier skill, averaged over five block-missing scenarios, with a prespecified equivalence margin of ±0.005. Confidence intervals by design-based jackknife (15 strata).

**Results.**
- *Primary comparison.* Augmentation and pattern submodels were equivalent: Δ Brier skill −0.0006 (95% CI −0.0023 to 0.0012). Augmentation was non-inferior with complete data. Equivalence held in all prespecified logistic-regression sensitivity analyses (alternative HbA1c cut-offs, excluding borderline diabetes, missing-at-random masking, an unseen pattern, survey-weighted training). With gradient boosting (secondary learner, lower overall skill), augmentation outperformed pattern submodels (+0.012, 0.008 to 0.017).
- *Value of any missing-data strategy.* Both strategies outperformed no handling (Δ +0.009, 0.006 to 0.012). Without handling, missing anthropometry caused marked miscalibration (O/E 0.60) and referral of 55% of adults for testing, versus 32% with augmentation.
- *Performance with complete data.* AUROC 0.816 (0.769–0.862). At a threshold prespecified for 80% sensitivity: sensitivity 0.81, referral 32%. The Bang/ADA score (≥5) reached sensitivity 0.69 with 35% referral.
- *Exploratory post hoc analyses.*
  - Anthropometry accounted for about two-thirds of predictive skill.
  - Self-reported weight and height recovered 91% of the skill lost without anthropometry (AUROC 0.795 vs 0.811 measured).
  - For HbA1c ≥5.7% (1,474 events): AUROC 0.775 vs 0.727 for the Bang score. At an equal referral rate, sensitivity was 4.6 percentage points higher (2.1 to 7.1), and net benefit was higher across thresholds of 10–40%.

**Conclusions.** A single model trained with block-masking augmentation performs as well as a set of pattern submodels when blocks of non-laboratory information are missing at use, and both clearly outperform unhandled missingness. Body size information is the critical input; self-reported weight and height appear sufficient. This supports questionnaire-only screening tools that refer adults for HbA1c testing. External validation outside the US is needed.

**Limitations to state.**
- Single temporal validation with 128 events.
- Missingness was simulated.
- One HbA1c measurement is not a diagnosis.
- Development-data–informed choice of learner and margin, made before the validation data were analysed.
