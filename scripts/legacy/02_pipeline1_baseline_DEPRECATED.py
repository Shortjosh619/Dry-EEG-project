#DEPRACATED- Do not use this for analysis
#This file contains auto resclaing which isnt comparable across my pipelines
#did not delete as already committed when i first made this repo
#Replaced this by shared framework in later baseline script

import numpy as np 
import mne 
import matplotlib.pyplot as plt
from mne.io import RawArray

raw_ec = mne.io.read_raw_bdf(r"C:\EEG_Dissertation\raw\Dry-EEG_29_01_2026_13_59_01.bdf", preload=True)

raw_ec.drop_channels(['VALID', 'DT', 'Status'])
raw_ec.rename_channels({'EEG 1': 'Fz', 
                        'EEG 2': 'C3', 
                        'EEG 3': 'Cz',
                        'EEG 4': 'C4',
                        'EEG 5': 'Pz',
                        'EEG 6': 'PO7',
                        'EEG 7': 'Oz',
                        'EEG 8': 'PO8'})

print(f"Sampling Rate: {raw_ec.info['sfreq']} Hz")
print(f"Channel Names: {raw_ec.ch_names}")
print(f"Channel Types: {raw_ec.get_channel_types()}")
print(f"Duration: {raw_ec.times[-1]} s")

raw_ec.plot(duration= 20, n_channels= 8, scalings='auto')
plt.show() 

data = raw_ec.get_data()
data_centered = data - data.mean(axis=1, keepdims=True)
rescaled_data = data_centered * (50e-6/data_centered.std())
raw_ec_rescaled = RawArray(rescaled_data, raw_ec.info)

#Pipeline 1
raw_filt = raw_ec_rescaled.copy()
raw_filt.filter(l_freq=0.5, h_freq=30)
raw_filt.notch_filter(freqs=50)

spectrum = raw_filt.compute_psd(fmin=0.5, fmax=60)
spectrum.plot()
raw_filt.plot(duration=20, n_channels= 8, scalings='auto')
plt.show()