# src/dryeeg/io_standardize.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import mne

from . import settings as S


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


def _apply_scaling_eeg_only(raw: mne.io.BaseRaw, divisor: float) -> None:
    raw.load_data()
    picks = mne.pick_types(raw.info, eeg=True, exclude=[])
    if len(picks) == 0:
        raise RuntimeError("No EEG channels found to scale.")
    raw._data[picks, :] = raw._data[picks, :] / float(divisor)


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

    # Set channel types explicitly to EEG for our 8 channels
    set_types = {v: "eeg" for v in S.CH_RENAME.values() if v in raw.ch_names}
    raw.set_channel_types(set_types)

    # Apply fixed scaling (EEG only)
    _apply_scaling_eeg_only(raw, S.SCALING_DIVISOR)

    # Set montage
    montage = mne.channels.make_standard_montage(S.MONTAGE_NAME)
    raw.set_montage(montage, match_case=False, on_missing="warn", verbose="ERROR")

    # Fixed segment crop (fair comparison)
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
        segment_start_s=float(S.SEGMENT_START_S),
        segment_dur_s=float(S.SEGMENT_DUR_S),
        rms_uv_by_ch=rms_uv_by_ch,
        rms_uv_warn_low=float(S.RMS_UV_WARN_LOW),
        rms_uv_warn_high=float(S.RMS_UV_WARN_HIGH),
        warnings=warnings,
    )
    return raw, rep
