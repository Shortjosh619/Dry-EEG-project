from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import mne
from mne.io.constants import FIFF

from src.dryeeg import settings as S


@dataclass
class StandardizeReport:
    input_path: str
    dropped: List[str]
    renamed: Dict[str, str]
    scaling_divisor: float
    segment_start_s: float
    segment_dur_s: float
    rms_uv_by_ch: Dict[str, float]
    rms_uv_warn_low: float
    rms_uv_warn_high: float
    warnings: List[str]


def read_bdf(path: str, preload: bool = True) -> mne.io.BaseRaw:
    raw = mne.io.read_raw_bdf(path, preload=preload, verbose="ERROR")
    return raw


def _rms_uv(raw: mne.io.BaseRaw) -> Dict[str, float]:
    data = raw.get_data()  # assumed in Volts-like after scaling
    rms_v = np.sqrt(np.mean(data**2, axis=1))
    rms_uv = rms_v * 1e6
    return {ch: float(val) for ch, val in zip(raw.ch_names, rms_uv)}


def _apply_scaling_eeg_only(raw: mne.io.BaseRaw, divisor: float) -> mne.io.BaseRaw:
    """Scale EEG channels to Volts (in-place) using MNE public API."""
    raw.load_data()

    picks = mne.pick_types(raw.info, eeg=True, exclude=[])
    if len(picks) == 0:
        return raw

    div = float(divisor)

    # In-place scaling via public API rather than the hard coding i was initially doing
    raw.apply_function(lambda x: x / div, picks=picks, channel_wise=False)

    for p in picks:
        ch = raw.info["chs"][p]
        ch["unit"] = FIFF.FIFF_UNIT_V
        ch["unit_mul"] = FIFF.FIFF_UNITM_NONE
        ch["cal"] = 1.0
        ch["range"] = 1.0

    return raw

def bandpower(psd, freqs, low, high):
    mask = (freqs >= low) & (freqs <= high)
    if not np.any(mask):
        return np.full(psd.shape[0], np.nan)
    return np.trapezoid(psd[:, mask], freqs[mask], axis=1)

#This entire function takes the best 2 mins of my raw EEG data based on the scoring that i specified in it.
#I split the raw eeg into windows and essentially slide the window along the entire bdf file with whatever step was specified at input
#if i want to change it i just edit the settings file to tweak some parameters like step_s when i call the constant

def choose_best_2min_start(raw, dur_s, step_s):
    raw.load_data()
    eeg_picks = mne.pick_types(raw.info, eeg=True, exclude=[])
    sfreq = float(raw.info["sfreq"])
    n = raw.n_times

    window = int(round(dur_s * sfreq))
    step = int(round(step_s * sfreq))
    if window <= 0 or n <= window:
        return 0.0, {"reason": "too_short"}
    

    #Fliter once for scoring
    raw_filter = raw.copy().filter(S.BANDPASS_L_HZ, S.BANDPASS_H_HZ, verbose="ERROR")
    data_v = raw_filter.get_data(picks=eeg_picks) 
    data_uv = data_v * 1e6 

    best_t0 = 0.0
    best_score = np.inf
    best_diagnostics_set = {"reason": "init"}

    for start in range(0, n - window + 1, step):
        x_uv = data_uv[:, start:start+window]
        x_v = data_v[:, start:start+window]

        rms_uv = np.sqrt(np.mean(x_uv **2, axis=1))
        med_rms = float(np.median(rms_uv))
        if med_rms < S.SELECT_MIN_RMS_UV or med_rms > S.SELECT_MAX_RMS_UV:
            continue

        spike_fraction = float(np.mean(np.abs(x_uv) > S.SELECT_SPIKE_UV))

        psd, freqs = mne.time_frequency.psd_array_welch(x_v,sfreq=sfreq,fmin=S.BANDPASS_L_HZ, fmax=S.BANDPASS_H_HZ, verbose="ERROR")
        psd = np.asarray(psd)
        freqs = np.asarray(freqs)

    # If somehow PSD is in dB/log units, bring it back to linear because the plots were having negative/log units
        if np.nanmin(psd) < 0:
            psd = 10 ** (psd / 10.0)

        power_total = bandpower(psd, freqs, 1.0, 30.0)
        p_high_freqs = bandpower(psd, freqs, 20.0, 30.0)
        p_low_freqs = bandpower(psd, freqs, 1.0, 3.0)

        power_total_floor = np.maximum(power_total, 1e-30)
        high_freqs_fraction = float(np.median(p_high_freqs / power_total_floor))
        low_freqs_fraction = float(np.median(p_low_freqs / power_total_floor))

        #Scoring
        score = (
            (50.0 * spike_fraction) +
              (3.0 * high_freqs_fraction) +
                (1.0 * low_freqs_fraction)  - 0.6 * np.log(max(med_rms, 1e-6))
        )

        if score < best_score: 
            best_score = score 
            best_t0 = start / sfreq 
            best_diagnostics_set = {
                "best_score": float(best_score),
                "med_rms_uv": med_rms,
                "spike_fraction": spike_fraction,
                "high_frequency_fraction": high_freqs_fraction,
                "low_frequency_fraction": low_freqs_fraction,
            }

    if not np.isfinite(best_score):
        return 0.0, {"reason": "no_window_passed"}
    
    return float(best_t0), best_diagnostics_set



def standardize_raw(path: str) -> Tuple[mne.io.BaseRaw, StandardizeReport]:
    warnings: List[str] = []
    raw = read_bdf(path, preload=True)

    # Drop non-EEG
    dropped = []
    existing_drop = [ch for ch in S.DROP_CHS if ch in raw.ch_names]
    if existing_drop:
        raw.drop_channels(existing_drop)
        dropped = existing_drop

    # Rename EEG channels -> 10-20 labels
    rename_map = {k: v for k, v in S.CH_RENAME.items() if k in raw.ch_names}
    missing = [k for k in S.CH_RENAME.keys() if k not in raw.ch_names]
    if missing:
        warnings.append(f"Missing expected channels in file: {missing}")
    raw.rename_channels(rename_map)

    # Set channel types explicitly to EEG for the 8 channels
    set_types = {v: "eeg" for v in S.CH_RENAME.values() if v in raw.ch_names}
    raw.set_channel_types(set_types)

    # Apply fixed scaling (EEG only)
    raw = _apply_scaling_eeg_only(raw, S.SCALING_DIVISOR)

    # Set montage
    montage = mne.channels.make_standard_montage(S.MONTAGE_NAME)
    raw.set_montage(montage, match_case=False, on_missing="warn", verbose="ERROR")

    # Fixed segment crop. fairest way to compare between my pipelines
    if getattr(S, "SEGMENT_SELECT_MODE", "fixed") == "best":
        t0, diag = choose_best_2min_start(raw, dur_s=float(S.SEGMENT_DUR_S), step_s=float(S.SEGMENT_STEP_S))
        warnings.append(f"Auto-selected segment t0={t0:.2f}s | diagnostic={diag}")
    else:
        t0 = float(S.SEGMENT_START_S)

    t1 = t0 + float(S.SEGMENT_DUR_S)
    # Ensure within bounds
    if raw.times[-1] < t1:
        warnings.append(
            f"Requested segment ends at {t1:.2f}s but file ends at {raw.times[-1]:.2f}s. Cropping to available length."
        )
        t1 = float(raw.times[-1])
    raw.crop(tmin=t0, tmax=t1, include_tmax=False)

    # Diagnostics: RMS in µV after scaling
    rms_uv_by_ch = _rms_uv(raw)
    for ch, val in rms_uv_by_ch.items():
        if val < S.RMS_UV_WARN_LOW or val > S.RMS_UV_WARN_HIGH:
            warnings.append(
                f"RMS plausibility warning: {ch} rms={val:.2f}µV outside [{S.RMS_UV_WARN_LOW}, {S.RMS_UV_WARN_HIGH}]"
            )

    rep = StandardizeReport(
        input_path=path,
        dropped=dropped,
        renamed=rename_map,
        scaling_divisor=float(S.SCALING_DIVISOR),
        segment_start_s=float(t0),
        segment_dur_s=float(S.SEGMENT_DUR_S),
        rms_uv_by_ch=rms_uv_by_ch,
        rms_uv_warn_low=float(S.RMS_UV_WARN_LOW),
        rms_uv_warn_high=float(S.RMS_UV_WARN_HIGH),
        warnings=warnings,
    )
    return raw, rep
