# Dry-EEG-project

**Evaluating the Effect of Cumulative EEG Preprocessing on the Test-Retest Reliability of Resting-State Alpha-Band Power Using a Dry-Electrode System**

BSc Psychology with Cognitive Neuroscience — University of Leicester, 2025–26  
Author: Joshua Ajemiri | Supervisor: Dr. Qadeer Arshad

---

## Overview

This repository contains all preprocessing and analysis scripts for an undergraduate dissertation examining whether cumulative EEG preprocessing pipelines improve the test-retest reliability of resting-state alpha-band power (8–13 Hz) recorded with the Unicorn Hybrid Black 8-channel dry-EEG system.

Reliability was assessed using ICC(2,1) (absolute agreement) and Bland–Altman analysis across four cumulative preprocessing pipelines, two conditions (eyes-open, eyes-closed), and two metrics (absolute and relative alpha power). N = 16 participants, two sessions each (minimum 48-hour separation).

---

## Repository Structure

```
scripts/
├── dev/                                         # Development and testing scripts
│   ├── base_preprocess_test.py                  # Early preprocessing tests
│   ├── inspect_raw.py                           # Raw data inspection utility
│   ├── logging_test.py                          # Logging framework tests
│   ├── qc_test.py                               # Quality control pipeline tests
│   └── standardize_test.py                      # Standardisation tests
├── legacy/
│   └── 02_pipeline1_baseline_DEPRECATED.py      # Superseded baseline script
├── calculate_icc.py                             # ICC(2,1) and ICC(3,1) + Bland–Altman analysis
├── icc_sample_size.R                            # Power analysis (ICC.Sample.Size package)
└── run_session.py                               # Main pipeline entry point (all four pipelines)

src/dryeeg/                                      # Core package — preprocessing and spectral functions
```

Raw data are not included. Participant recordings were stored locally in accordance with ethical approval conditions.

---

## Pipelines

Four cumulative preprocessing pipelines were evaluated. Each pipeline builds on the previous:

| Pipeline   | Steps applied                                                                   |
|------------|---------------------------------------------------------------------------------|
| Baseline   | Bandpass filter (0.5–30 Hz) + 50 Hz notch                                       |
| + ASR      | Baseline + Artifact Subspace Reconstruction (cutoff = 15 SD)                    |
| + ICA      | ASR + Picard ICA (7 components, Fz as EOG proxy, ρ ≥ 0.90)                     |
| + Wavelet  | ICA + db4 wavelet denoising (4-level, soft universal threshold, D1–D3 only)     |

---

## Spectral Analysis

- **Method:** Welch PSD — `n_fft=1024`, `n_overlap=512`, frequency resolution = 0.244 Hz
- **Alpha band:** 8–13 Hz
- **Channels:** PO7, Oz, PO8 (occipital average)
- **Metrics:** Absolute alpha power (µV²) and relative alpha power (alpha / broadband)

---

## Reliability Analysis

- **Primary:** ICC(2,1) — two-way random effects, absolute agreement (Shrout & Fleiss, 1979)
- **Secondary:** ICC(3,1) — two-way mixed effects, consistency
- **Benchmarks:** Koo & Li (2016) — poor (<0.50), moderate (0.50–0.75), good (0.75–0.90), excellent (>0.90)
- **Supplementary:** Bland–Altman analysis (bias and limits of agreement across sessions)

Power analysis conducted in R using the `ICC.Sample.Size` package (Rathbone et al., 2015); N = 16 exceeds the minimum required (N = 15) at ICC = 0.75, power = 0.95, α = 0.05.

---

## Dependencies

**Python**
- MNE-Python 1.10.2
- asrpy (with numpy 2.x compatibility patch applied to `asr_utils.py`)
- pywt, pingouin, scipy, numpy, matplotlib

**R**
- `ICC.Sample.Size`

---

## Notes

- The `legacy/` folder contains an earlier version of the baseline pipeline that was superseded when preprocessing was refactored into the `src/dryeeg` package.
- The `dev/` folder contains exploratory scripts written during pipeline development; these are not part of the main analysis.
- All final analysis is run via `run_session.py` and `calculate_icc.py`.
