"""Project directory layout shared by every script."""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
MODELS_DIR = os.path.join(BASE_DIR, "models")
PLOTS_DIR = os.path.join(BASE_DIR, "notebooks", "eval_plots")


def ensure_dirs(*dirs):
    for directory in dirs:
        os.makedirs(directory, exist_ok=True)
