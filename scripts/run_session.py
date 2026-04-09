r"""
Run one pipeline for both conditions of a single session.

Usage (CMD):
    py scripts\run_session.py --session_dir raw\sub-001\ses-01 --pipeline baseline --results Y

Expected session_dir layout:
    ses-01\
        eyes-open\   <any single .bdf>
        eyes-closed\ <any single .bdf>
"""

import sys
from pathlib import Path

# Make project root importable regardless of where i call from
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
import logging

from src.dryeeg.pipeline_runner import run_pipeline
from src.dryeeg.preprocess_asr import apply_asr      
from src.dryeeg.preprocess_ica import apply_ica
from src.dryeeg.preprocess_wavelet import apply_wavelet

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

def apply_asr_then_ica(raw):
    return apply_ica(apply_asr(raw))

def apply_ica_then_wavelet(raw):
    return apply_wavelet(apply_ica(apply_asr(raw)))

PIPELINE_REGISTRY = {
    "baseline": None,
    "asr": apply_asr,
    "ica": apply_asr_then_ica,
    "wavelet": apply_ica_then_wavelet,
}

CONDITIONS = ["eyes-open", "eyes-closed"]


def find_bdf(session_dir: Path, condition: str) -> Path:
    condition_dir = session_dir / condition
    bdfs = list(condition_dir.glob("*.bdf"))
    if len(bdfs) == 0:
        raise FileNotFoundError(f"No .bdf found in {condition_dir}")
    if len(bdfs) > 1:
        raise ValueError(f"Multiple .bdf files in {condition_dir} - expected one: {bdfs}")
    return bdfs[0]


def main():
    parser = argparse.ArgumentParser(description="Run one pipeline for a full session.")
    parser.add_argument("--session_dir", required=True, help=r"e.g. raw\sub-001\ses-01")
    parser.add_argument("--pipeline",    required=True, choices=list(PIPELINE_REGISTRY.keys()))
    parser.add_argument("--results",     choices=["Y", "N"], default="N",
                        help="Also save clean outputs to results/ (default: N)")
    args = parser.parse_args()

    session_dir = Path(args.session_dir)
    extra_fn    = PIPELINE_REGISTRY[args.pipeline]

    results = {}
    for condition in CONDITIONS:
        bdf_path = find_bdf(session_dir, condition)
        logger.info(f"Processing {condition} → {bdf_path.name}")
        results[condition] = run_pipeline(
            bdf_path, condition, args.pipeline, extra_fn,
            save_results=(args.results == "Y"),
        )

    logger.info("Session complete.")
    for cond, manifest in results.items():
        logger.info(f"  {cond}: run_id={manifest['run_id']}")


if __name__ == "__main__":
    main()
