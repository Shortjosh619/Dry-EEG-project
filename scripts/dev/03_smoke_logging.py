import sys
sys.path.insert(0, ".")

from src.dryeeg.logging_utils import (
    generate_run_id,
    compute_file_hash,
    collect_environment,
    derive_output_paths,
    create_manifest, 
    save_manifest,
    get_logger
)

# Test generate_run_id
run_id = generate_run_id()
print(f"Run ID: {run_id}")

# Test compute_file_hash
test_file = r"C:\EEG_Dissertation\raw\pilot\eyes-open\Dry-EEG_29_01_2026_13_43_00.bdf"
file_hash = compute_file_hash(test_file)
print(f"File hash (first 16 chars): {file_hash[:16]}...")

# Test collect_environment
env = collect_environment()
print(f"Environment: {env}")

# Test derive_output_paths
paths = derive_output_paths(
    source_path=test_file,
    pipeline_name="pipeline1",
    run_id=run_id,
    derivatives_root=r"C:\EEG_Dissertation\derivatives"
)
print(f"Output paths:")
for key, val in paths.items():
    print(f"  {key}: {val}")

# Test create_manifest
manifest = create_manifest(
    source_path=test_file,
    condition="eyes-open",
    pipeline_name="pipeline1",
    run_id=run_id,
    parameters={"bandpass": {"l_freq": 1, "h_freq": 30}, "scaling_divisor": 1e9},
    decisions={"base_preprocess_report": {"notch_applied": False}},
    qc_summary={"rms_uv_mean": 25.3},
    output_paths=paths
)

save_manifest(manifest, paths["manifest_path"])
print(f"\nManifest saved to: {paths['manifest_path']}")

# Test get_logger
logger = get_logger(run_id, paths["output_dir"] / "logs")
logger.info("Smoke test log entry")
print(f"Log file created at: {paths['log_path']}")
print("Done.")