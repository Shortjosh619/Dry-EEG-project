"""Test script for base preprocessing file. Ensured it was determinsitic and shared across pipelines,
 confirmed by console output when ran"""

import sys 

sys.path.append("src")

from dryeeg.io_standardize import standardize_raw
from dryeeg.preprocess_base import base_preprocess

#Used data from first subject
EO_path = r"C:\EEG_Dissertation\raw\sub-001\Session 1\Eyes-Open\Dry-EEG_09_02_2026_17_15_47.bdf"
EC_path = r"C:\EEG_Dissertation\raw\sub-001\Session 1\Eyes Closed\Dry-EEG_09_02_2026_18_03_17.bdf"

#list of tuples for the for loop below
cases = [("Eyes-Open", EO_path) ,("Eyes-Closed", EC_path)]

for label, path in cases:
    raw_std, rep_std = standardize_raw(path)

    print(label)
    print(f"channel names:{raw_std.ch_names}")
    print(f"duration:{raw_std.times[-1]}s")

    raw_bp, rep_bp = base_preprocess(raw_std)

    print(f"channel names: {raw_bp.ch_names}")
    print(f"duration:{raw_bp.times[-1]}s")
    print(rep_bp["bandpass"])
    print(rep_bp["notch"])
    print(rep_bp["reref_policy"])
    print(raw_bp.info["line_freq"])
    print(raw_bp.info.get("custom_ref_applied")) 







