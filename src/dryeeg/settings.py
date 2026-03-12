# src/dryeeg/settings.py
from __future__ import annotations

# ---------- Project identity ----------
PROJECT_ROOT = r"C:\EEG_Dissertation"
DERIVATIVES_DIRNAME = "derivatives"
SUBJECT_ID = "sub-001"
SESSION_ID = "ses-pilot"

# ---------- Inputs ----------
DROP_CHS = ["VALID", "DT", "Status"]

CH_RENAME = {
    "EEG 1": "Fz",
    "EEG 2": "C3",
    "EEG 3": "Cz",
    "EEG 4": "C4",
    "EEG 5": "Pz",
    "EEG 6": "PO7",
    "EEG 7": "Oz",
    "EEG 8": "PO8",
}

MONTAGE_NAME = "standard_1020"

# Scaling (single constant)
# divide by 1e6 gives ~200 µV RMS scale.
SCALING_DIVISOR = 1_000_000.0  # divide EEG channels by this

# Post-scale RMS plausibility warnings (µV). Warnings only, never changes scaling.
RMS_UV_WARN_LOW = 0.05
RMS_UV_WARN_HIGH = 1_000_000.0

# Pilot segment selection 
SEGMENT_SELECT_MODE = "best"
SEGMENT_START_S = 0.0
SEGMENT_DUR_S = 120.0
SEGMENT_STEP_S = 1.0

SELECT_MIN_RMS_UV = 1.0
SELECT_MAX_RMS_UV = 200.0
SELECT_SPIKE_UV = 150.0

# Base preprocessing (Pipeline 1 shared)
# Keep QC denominator consistent with cleaning: 1–30 Hz.
BANDPASS_L_HZ = 1.0
BANDPASS_H_HZ = 30.0

# If notch freqs are above BANDPASS_H_HZ, skip notch and log "skipped"
NOTCH_FREQS_HZ = [50.0, 100.0]

REREF_POLICY = "average"  # fixed across all pipelines

# ---------- QC settings ----------
PSD_FMIN = 1.0
PSD_FMAX = 30.0

BANDS = {
    "delta": (1.0, 4.0),
    "theta": (4.0, 8.0),
    "alpha": (8.0, 13.0),
    "beta":  (13.0, 30.0),
}
REL_ALPHA_DENOM = (1.0, 30.0)
ALPHA_PEAK_RANGE = (8.0, 13.0)

FRONTAL = ["Fz"]
OCCIPITAL = ["PO7", "Oz", "PO8"]

ASR_CUTOFF = 15 
RANDOM_STATE = 9 
N_COMPONENTS = 7