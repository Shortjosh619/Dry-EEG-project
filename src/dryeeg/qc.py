import mne, numpy as np
from pathlib import Path

def compute_rms_per_channel(raw):
    data = raw.get_data()
    names = raw.ch_names

    rms = np.sqrt(np.mean(data**2, axis=1)) * 1e6

    return dict(zip(names, rms))

def compute_psd(raw, fmin, fmax):
    
    spectrum = raw.compute_psd(fmin=fmin, fmax=fmax)
    psd, freqs = spectrum.get_data(return_freqs=True)
    psd_uv  = psd * 1e12

    return spectrum, psd_uv, freqs

def compute_bandpower(psd, freqs, band_definitions):
    bandpower_dict = {}

    for band_name, (low, high) in band_definitions.items():
        mask = (freqs >= low) & (freqs <= high)
        band_power = np.trapezoid(psd[:, mask], freqs[mask], axis=1)
        bandpower_dict[band_name] = band_power

    return bandpower_dict 

def compute_relative_bandpower(bandpower_dict, psd, freqs, denom_range):
    low, high = denom_range
    mask = (freqs >= low) & (freqs <= high)
    total_power = np.trapezoid(psd[:, mask], freqs[mask], axis=1)
    total_floor = np.maximum(total_power, 1e-30)
    return {band: power / total_floor for band, power in bandpower_dict.items()}

def find_alpha_peak(psd, freqs, alpha_range):
    low, high = alpha_range #alpha range is a tuple (8-13) so just unoack it and use the variables for the mask instead of hard coding 8-13

    mask = (freqs >= low ) & (high >= freqs)
    alpha_freqs = freqs[mask]
    alpha_psd = psd[:, mask]
    alpha_indicies = np.argmax(alpha_psd, axis=1)
    alpha_peak = alpha_freqs[alpha_indicies]

    return alpha_peak 

def compute_alpha_ratio_occ_frontal(bandpower, ch_names, occipital_chs, frontal_chs):
    alpha_power = bandpower["alpha"]
    indicies_occ = [ch_names.index(channel) for channel in occipital_chs]
    indicies_frontal = [ch_names.index(channel) for channel in frontal_chs]
    
    alpha_occ = np.mean(alpha_power[indicies_occ])
    alpha_frontal = np.mean(alpha_power[indicies_frontal])

    return alpha_occ / alpha_frontal

def plot_psd(spectrum, output_path):
    """
    Plot PSD with alpha band highlighted and save to file.

    """
    import matplotlib.pyplot as plt
    
    fig = spectrum.plot(show=False)
    
    # Shade alpha band 
    ax = fig.axes[0]
    ax.axvspan(8, 13, alpha=0.3, color='green', label='Alpha (8-13 Hz)')
    ax.legend()
    ax.set_title('Power Spectral Density')
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)

def save_topomap_alpha(bandpower_dict, raw_info, output_path):
    import matplotlib.pyplot as plt
    import mne

    alpha_values = bandpower_dict["alpha"]
    fig, ax = plt.subplots(figsize=(4, 4))
    mne.viz.plot_topomap(alpha_values, raw_info, axes=ax, show=False, contours=4)
    ax.set_title("Alpha Power (8–13 Hz)")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def generate_qc_report(raw, output_paths, settings, results_paths=None):
    """
    Run all QC metrics and save outputs.
    
    Returns
    dict : QC summary for manifest
    """
    import pandas as pd 
    
    ch_names = raw.ch_names
    
    # Compute metrics from all the functions i made above
    rms = compute_rms_per_channel(raw)
    spectrum, psd, freqs = compute_psd(raw, settings.PSD_FMIN, settings.PSD_FMAX)
    bandpower = compute_bandpower(psd, freqs, settings.BANDS)
    rel_bandpower = compute_relative_bandpower(bandpower, psd, freqs, settings.REL_ALPHA_DENOM)
    alpha_peak = find_alpha_peak(psd, freqs, settings.ALPHA_PEAK_RANGE)
    alpha_ratio = compute_alpha_ratio_occ_frontal(
        bandpower, ch_names, settings.OCCIPITAL, settings.FRONTAL
    )
    
    plot_psd(spectrum, output_paths["psd_plot_path"])
    
    # build dataframe for csv saving
    df = pd.DataFrame(bandpower, index=ch_names)
    for band, values in rel_bandpower.items():
        df[f"rel_{band}"] = values
    df["alpha_peak_hz"] = alpha_peak
    df["rms_uv"] = [rms[ch] for ch in ch_names]
    
    Path(output_paths["bandpower_csv_path"]).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_paths["bandpower_csv_path"])
    
    if results_paths is not None:
        Path(results_paths["bandpower_csv_path"]).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(results_paths["bandpower_csv_path"])
        plot_psd(spectrum, results_paths["psd_plot_path"])
        save_topomap_alpha(bandpower, raw.info, results_paths["topomap_alpha_path"])

    # Return summary for manifest
    return {
        "rms_uv_per_channel": rms,
        "alpha_ratio_occ_frontal": float(alpha_ratio),
        "alpha_peak_hz_mean": float(np.mean(alpha_peak)),
        "rel_bandpower": {band: values.tolist() for band, values in rel_bandpower.items()},
        "bandpower_csv_saved": True,
        "psd_plot_saved": True
    }