import sys
import json

# import from current working directory. I will apply this to all my smoke tests from now on
sys.path.insert(0, ".")

from src.dryeeg.io_standardize import standardize_raw

EO = r"C:\EEG_Dissertation\raw\Dry-EEG_29_01_2026_13_43_00.bdf"
EC = r"C:\EEG_Dissertation\raw\Dry-EEG_29_01_2026_13_59_01.bdf"

for label, path in [("EO", EO), ("EC", EC)]:
    raw, rep = standardize_raw(path)
    print("\n====", label, "====")
    print("ch_names:", raw.ch_names)
    print("sfreq:", raw.info["sfreq"])
    print("dur_s:", raw.times[-1])
    print("montage_set:", raw.get_montage() is not None)
    print("warnings:", rep.warnings)
    print("rms_uv_by_ch:")
    print(json.dumps(rep.rms_uv_by_ch, indent=2))
