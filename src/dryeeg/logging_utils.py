import datetime, secrets, hashlib as hash, json, logging, platform, sys
from pathlib import Path
import mne, numpy as np 


def generate_run_id():
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
    suffix = secrets.token_hex(2)

    return f"{timestamp}_{suffix}"

def compute_file_hash(filepath):
    hasher = hash.sha256()

    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536) 
            if not chunk:
                break
            hasher.update(chunk)

    return hasher.hexdigest()

def collect_environment():
    return {
        "python_version": sys.version,
        "mne_version": mne.__version__,
        "numpy_version": np.__version__,
        "os_platform": platform.platform(),
        "hostname": platform.node()

    }

def derive_output_paths(source_path, pipeline_name, run_id, derivatives_root):
    parts = Path(source_path).parts

    #Find index of "raw" in parts
    raw_idx = parts.index("raw")

    #Grab everything after raw except for the filename itself
    relative_parts = parts[raw_idx +1 : -1]
    # This means that for any numbered subject case, it would be as follows: "sub-00n", "ses-0n", "eyes-open")
    #for the pilot data it would handle by doing: ("pilot", "eyes-open")

    #Build output directory
    output_dir = Path(derivatives_root) / pipeline_name
    for part in relative_parts:
        output_dir = output_dir / part

    
    return {
        "output_dir": output_dir,
        "cleaned_fif_path": output_dir / "data" / f"{run_id}_eeg.fif",
        "psd_plot_path": output_dir / "qc" / f"{run_id}_psd.png",
        "bandpower_csv_path": output_dir / "qc" / f"{run_id}_bandpower.csv",
        "manifest_path": output_dir / "logs" / f"{run_id}_manifest.json",
        "log_path": output_dir / "logs" / f"{run_id}_processing.log"
    }

def create_manifest(source_path, condition, pipeline_name, run_id, 
                    parameters, decisions, qc_summary, output_paths):
    return {
        "manifest_version": "1.0",
        "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),

        "source":{
            "input_path": str(source_path),
            "file_hash_sha256": compute_file_hash(source_path),
            "file_size_bytes": Path(source_path).stat().st_size
        }, 
        
        "session": {
            "condition_label": condition,
            "pipeline_name": pipeline_name,
            "run_id": run_id
        },

        "parameters": parameters,
        "decisions": decisions,
        "qc_summary": qc_summary,

        "outputs": {k: str(v) for k, v in output_paths.items()},

        "environment": collect_environment()

        }
    

def save_manifest(manifest_dict, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(manifest_dict, f, indent=2, default=str)

def get_logger(run_id, log_dir):
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    log_path = log_dir / f"{run_id}_processing.log"

    logger = logging.getLogger(run_id)
    logger.setLevel(logging.INFO)

    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("(%asctime)s | %(levelname)s | %(message)s"))

    logger.addHandler(handler)

    return logger
