#!/usr/bin/env python3
"""
Download script for MiniMax-H3 models required by the ComfyUI workflow.
Optimized for high-speed transfer using hf_transfer / huggingface_hub on cloud environments like SaladCloud.
"""

import os
import sys
import shutil
from pathlib import Path

# Enable ultra-fast rust-based parallel download
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"

try:
    from huggingface_hub import hf_hub_download
except ImportError:
    print("[ERROR] huggingface_hub is not installed! Run: pip install huggingface-hub[hf_transfer]")
    sys.exit(1)

MODELS_BASE_DIR = Path(os.environ.get("COMFY_MODELS_DIR", "/workspace/ComfyUI/models"))
HF_TOKEN = os.environ.get("HF_TOKEN", None)

# List of models specified in the workflow:
# (repo_id, remote_subpath, local_subdir, local_filename, min_size_gb)
MODELS_TO_DOWNLOAD = [
    {
        "repo_id": "Comfy-Org/MiniMax-H3",
        "filename": "vae/minimax_h3_audio_vae_fp32.safetensors",
        "target_dir": MODELS_BASE_DIR / "vae",
        "target_name": "minimax_h3_audio_vae_fp32.safetensors",
        "min_size_gb": 0.5,
    },
    {
        "repo_id": "Comfy-Org/MiniMax-H3",
        "filename": "vae/minimax_h3_video_vae_fp16.safetensors",
        "target_dir": MODELS_BASE_DIR / "vae",
        "target_name": "minimax_h3_video_vae_fp16.safetensors",
        "min_size_gb": 4.5,
    },
    {
        "repo_id": "Comfy-Org/MiniMax-H3",
        "filename": "loras/minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors",
        "target_dir": MODELS_BASE_DIR / "loras",
        "target_name": "minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors",
        "min_size_gb": 2.0,
    },
    {
        "repo_id": "Comfy-Org/MiniMax-H3",
        "filename": "text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors",
        "target_dir": MODELS_BASE_DIR / "text_encoders",
        "target_name": "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors",
        "min_size_gb": 14.0,
    },
    {
        "repo_id": "Comfy-Org/MiniMax-H3",
        "filename": "diffusion_models/minimax_h3_ref2va_pruned_int8_convrot.safetensors",
        "target_dir": MODELS_BASE_DIR / "diffusion_models",
        "target_name": "minimax_h3_ref2va_pruned_int8_convrot.safetensors",
        "min_size_gb": 30.0,
    },
]

def check_file_valid(file_path: Path, min_size_gb: float) -> bool:
    if not file_path.exists():
        return False
    size_gb = file_path.stat().st_size / (1024 ** 3)
    if size_gb >= min_size_gb:
        print(f"  [OK] {file_path.name} exists ({size_gb:.2f} GB). Skipping download.")
        return True
    else:
        print(f"  [WARN] {file_path.name} is incomplete ({size_gb:.2f} GB < {min_size_gb:.2f} GB). Re-downloading...")
        return False

def main():
    print("=" * 60)
    print("  MiniMax-H3 Model Downloader for SaladCloud (RTX 3090)")
    print(f"  Target Directory: {MODELS_BASE_DIR}")
    print(f"  HF_HUB_ENABLE_HF_TRANSFER: {os.environ.get('HF_HUB_ENABLE_HF_TRANSFER')}")
    print("=" * 60)

    total_models = len(MODELS_TO_DOWNLOAD)
    for idx, item in enumerate(MODELS_TO_DOWNLOAD, 1):
        target_dir: Path = item["target_dir"]
        target_file: Path = target_dir / item["target_name"]
        min_size = item["min_size_gb"]

        print(f"\n[{idx}/{total_models}] Checking: {item['target_name']}")
        target_dir.mkdir(parents=True, exist_ok=True)

        if check_file_valid(target_file, min_size):
            continue

        print(f"  Downloading {item['filename']} from {item['repo_id']}...")
        try:
            downloaded_path = hf_hub_download(
                repo_id=item["repo_id"],
                filename=item["filename"],
                token=HF_TOKEN,
                local_dir=str(target_dir),
                local_dir_use_symlinks=False,
            )
            # If the remote filename had subdirectories, ensure it's in target_file
            if Path(downloaded_path) != target_file and Path(downloaded_path).exists():
                shutil.move(downloaded_path, target_file)

            final_size_gb = target_file.stat().st_size / (1024 ** 3)
            print(f"  [SUCCESS] Downloaded {item['target_name']} ({final_size_gb:.2f} GB)")

        except Exception as e:
            print(f"  [ERROR] Failed to download {item['filename']}: {e}")
            sys.exit(1)

    print("\n" + "=" * 60)
    print("  All MiniMax-H3 models verified and ready!")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()

