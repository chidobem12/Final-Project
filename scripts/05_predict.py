"""Run CSV inference using saved artifacts and print a preview of predictions."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.predictor import predict_from_csv


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Predict threats from a CSV file.")
    parser.add_argument("input_csv", type=Path, help="Path to input CSV file")
    parser.add_argument("--model", default="random_forest", help="Model to use")
    args = parser.parse_args()

    output_df = predict_from_csv(args.input_csv, args.model)
    print(output_df.head())
