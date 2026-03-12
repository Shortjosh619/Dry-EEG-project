from src.dryeeg.settings import ASR_CUTOFF
import asrpy
import logging

logger = logging.getLogger(__name__)


def apply_asr(raw):

    asr = asrpy.ASR(sfreq=raw.info["sfreq"], cutoff=ASR_CUTOFF)
    asr.fit(raw)
    raw_cleaned = asr.transform(raw)

    logger.info(f"ASR being fitted with cutoff: {ASR_CUTOFF}")

    return raw_cleaned
