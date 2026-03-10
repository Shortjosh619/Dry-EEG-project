"""This function must take in an MNE Raw object of standardised raw data e.g. 8 channels, scaled, montage set and cropped (raw),
and return the baseline preprocessed raw EEG using bandpass 1-30hz, notch only applied if if within range, reference set to average so it is identical across all pipelines and line_freq=50 (raw_out)
and generate a report giving the exact configs used e.g. notch applied

If notch outside low-pass, it will be logged in the report as skipped

Base preprocessing should not alter scaling or channel set
"""

from src.dryeeg.settings import REREF_POLICY, NOTCH_FREQS_HZ, BANDPASS_H_HZ, BANDPASS_L_HZ
 
def base_preprocess(raw):
    raw_out = raw.copy()
    report = {}
    
    #Report Metrics
    report['line_freq'] = 50
    report['bandpass'] = {"l_freq": BANDPASS_L_HZ, "h_freq": BANDPASS_H_HZ}
    report['notch'] = {"requested": NOTCH_FREQS_HZ}
    report['reref_policy']= {"policy": REREF_POLICY}
    
   
    requested = NOTCH_FREQS_HZ
    h = BANDPASS_H_HZ
    
    eligible = [f for f in requested if f < h]
    report['notch']['eligible'] = eligible

    applied = len(eligible) > 0
    report['notch']['applied']= applied

    reason = "outside_lowpass" if applied is False else None
    report['notch']['reason'] = reason

    raw_out.info['line_freq'] = 50
    raw_out.filter(l_freq=BANDPASS_L_HZ, h_freq=BANDPASS_H_HZ)
    print(f"After bandpass - std: {raw_out.get_data().std()}")  # ADD THIS
    
    if applied:
        raw_out.notch_filter(freqs=eligible)
        print(f"After notch - std: {raw_out.get_data().std()}")  # ADD THIS
    
    raw_out.set_eeg_reference(ref_channels=REREF_POLICY)
    print(f"After reref - std: {raw_out.get_data().std()}") 

    return raw_out, report




