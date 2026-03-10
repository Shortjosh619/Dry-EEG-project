import sys
sys.path.insert(0, ".")

from src.dryeeg import settings
from src.dryeeg.io_standardize import standardize_raw
from src.dryeeg.preprocess_base import base_preprocess
from src.dryeeg.logging_utils import generate_run_id, derive_output_paths
from src.dryeeg.qc import generate_qc_report

# Load and preprocess pilot data
test_file = r"C:\EEG_Dissertation\raw\sub-001\ses-01\eyes-closed\Dry-EEG_09_02_2026_18_03_17.bdf"
raw, report = standardize_raw(test_file)

if report.warnings:
    print("\n[standardize_raw warnings]")
    for w in report.warnings:
        print(" -", w)

raw, preproc_report = base_preprocess(raw)

# Generate output paths
run_id = generate_run_id()
output_paths = derive_output_paths(
    source_path=test_file,
    pipeline_name="pipeline1",
    run_id=run_id,
    derivatives_root=r"C:\EEG_Dissertation\derivatives"
)

print(f"Run ID: {run_id}")
print(f"Output dir: {output_paths['output_dir']}")

# Run QC
qc_summary = generate_qc_report(raw, output_paths, settings)

print("\nQC Summary:")
for key, val in qc_summary.items():
    print(f"  {key}: {val}")

print(f"\nPSD plot saved to: {output_paths['psd_plot_path']}")
print(f"Bandpower CSV saved to: {output_paths['bandpower_csv_path']}")
print("Done.")