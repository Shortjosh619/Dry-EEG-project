"""
Shared pipeline runner.
Usage:
    result = run_pipeline(raw_path, condition, pipeline_name, extra_step_fn=None)
"""

import logging
from pathlib import Path

from src.dryeeg import settings as S
from src.dryeeg.logging_utils import (
    generate_run_id,
    derive_output_paths,
    get_logger,
    create_manifest,
    save_manifest,
)
from src.dryeeg.io_standardize import standardize_raw
from src.dryeeg.preprocess_base import base_preprocess
from src.dryeeg.qc import generate_qc_report

logger = logging.getLogger(__name__)


def run_pipeline(
    raw_path,
    condition: str,
    pipeline_name: str,
    extra_step_fn=None,
) -> dict:
    """
    Standardised pipeline runner.

    Parameters
    ----------
    raw_path      : Path to input .bdf file.
    condition     : Recording condition label (e.g. "eyes-open", "eyes-closed").
    pipeline_name : String key identifying this pipeline (used for output paths).
    extra_step_fn : Optional callable applied AFTER baseline preprocessing.
                    Signature: extra_step_fn(raw: mne.io.Raw) -> mne.io.Raw
                    Pass None for Pipeline 1 (baseline only).

    Returns
    -------
    dict with keys: run_id, output_paths, qc_summary
    """
    raw_path = Path(raw_path)
    run_id = generate_run_id()
    derivatives_root = str(Path(S.PROJECT_ROOT) / S.DERIVATIVES_DIRNAME)

    output_paths = derive_output_paths(str(raw_path), pipeline_name, run_id, derivatives_root)
    file_logger = get_logger(run_id, output_paths["output_dir"] / "logs")
    file_logger.info(f"Starting pipeline '{pipeline_name}' | {raw_path.name} | {condition}")

    # 1. Load & standardise
    raw, std_report = standardize_raw(str(raw_path))

    # 2. Baseline preprocessing (bandpass, notch, avg ref)
    raw, preproc_report = base_preprocess(raw)

    # 3. Optional pipeline-specific step (ASR / ICA / wavelet)
    if extra_step_fn is not None:
        file_logger.info(f"Applying extra step: {extra_step_fn.__name__}")
        raw = extra_step_fn(raw)

    # 4. Save cleaned .fif
    output_paths["cleaned_fif_path"].parent.mkdir(parents=True, exist_ok=True)
    raw.save(str(output_paths["cleaned_fif_path"]), overwrite=True)
    file_logger.info(f"Saved preprocessed data -> {output_paths['cleaned_fif_path']}")

    # 5. QC report
    qc_summary = generate_qc_report(raw, output_paths, S)

    # 6. Build and save manifest
    parameters = {
        "bandpass": preproc_report["bandpass"],
        "notch": preproc_report["notch"],
        "reref_policy": preproc_report["reref_policy"],
        "scaling_divisor": S.SCALING_DIVISOR,
        "asr_cutoff": S.ASR_CUTOFF
    }
    decisions = {
        "segment_start_s": std_report.segment_start_s,
        "segment_dur_s": std_report.segment_dur_s,
        "standardize_warnings": std_report.warnings,
    }
    manifest = create_manifest(
        str(raw_path), condition, pipeline_name, run_id,
        parameters, decisions, qc_summary, output_paths,
    )
    save_manifest(manifest, output_paths["manifest_path"])
    file_logger.info(f"Pipeline complete. Manifest -> {output_paths['manifest_path']}")

    return {"run_id": run_id, "output_paths": output_paths, "qc_summary": qc_summary}
