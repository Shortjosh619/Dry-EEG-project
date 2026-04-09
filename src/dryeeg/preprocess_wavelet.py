from pywt import wavedec, threshold, waverec
import numpy as np 
import pandas as pd 
from mne.io import RawArray
import logging

logger = logging.getLogger(__name__)

def apply_wavelet(raw):

    data = raw.get_data()

    results = []

    logger.info("Starting wavelet pipeline")

    for ch in data:
        wave_fam = 'sym4' 

        coeffs = wavedec(data=ch, wavelet=wave_fam,  level=4)

        logger.info(f"Wavelet family used: {wave_fam}")

        cA4, cD4, cD3, cD2, cD1 = coeffs
        noise_esti = np.median(np.abs(cD1))/0.6745
        thresh = noise_esti * np.sqrt((2*np.log(len(ch))))
        thresh_coeffs= [cA4, cD4, threshold(data=cD3, value=thresh, mode='soft'),
                         threshold(data=cD2, value=thresh, mode='soft'), threshold(data=cD1, value=thresh, mode='soft')]
        rec_coeffs = waverec(coeffs=thresh_coeffs, wavelet=wave_fam)

        
        results.append(rec_coeffs)

    results_array = np.array(results)
    raw_cleaned = RawArray(results_array, info=raw.info)
    
    logger.info("Wavelet denoising complete.")


    return raw_cleaned


