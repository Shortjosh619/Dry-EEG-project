import logging
from mne.preprocessing import ICA
from src.dryeeg.settings import RANDOM_STATE, N_COMPONENTS, FRONTAL

logger = logging.getLogger(__name__)


def apply_ica(raw):

    ica = ICA(n_components=N_COMPONENTS, random_state=RANDOM_STATE, max_iter="auto", method="picard")
    ica.fit(raw)
    eog_inds, scores = ica.find_bads_eog(raw, ch_name=FRONTAL, measure="correlation", threshold=0.9)
    exclude = [eog_inds[0]] if len(eog_inds) > 0 else []
    raw_cleaned = ica.apply(raw, exclude=exclude)

    # Log ICA details
    logger.info(f"ICA fitted with {N_COMPONENTS} components")
    logger.info(f"Proxy used was {FRONTAL}")
    logger.info(f"EOG components found: {eog_inds}")
    logger.info(f"EOG scores: {scores}")
    logger.info(f"Components excluded: {exclude}")

    return raw_cleaned
