import sys
sys.path.insert(0, ".")

import numpy as np
from src.dryeeg.io_standardize import standardize_raw 
import matplotlib.pyplot as plt

raw, rep = standardize_raw(r"C:\EEG_Dissertation\raw\sub-006\ses-01\eyes-closed\UnicornRawDataRecorder_12_03_2026_13_43_34.bdf")

raw.filter(l_freq=1, h_freq=30)
raw.plot(duration=30, n_channels=8, scalings=dict(eeg=50e-6))
plt.show(block=True)
