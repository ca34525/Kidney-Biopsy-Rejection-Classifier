"""Compatibility entry point for the shared batch prediction command.

Run: uv run python experiments/rejection_public/predict.py --geo-validation
"""
from kidney_biopsy.cli import main


if __name__ == "__main__":
    main()
