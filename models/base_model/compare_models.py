"""Evaluate all baseline models and select the representative model."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from ultralytics import YOLO

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from models.base_model.common import evaluate_model, load_config, resolve_dataset_yaml, validate_dataset

ROOT = Path(__file__).resolve().parents[2]
MODEL_NAMES = ("yolov8n", "yolov8s", "yolov8m")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/baseline.yaml")
    parser.add_argument("--dataset-yaml", type=Path, help="Override dataset YAML from config")
    parser.add_argument("--split", choices=("val", "test"), help="Override evaluation split")
    parser.add_argument("--models", nargs="+", choices=MODEL_NAMES, default=list(MODEL_NAMES))
    args = parser.parse_args()

    config = load_config(args.config)
    dataset_yaml = (args.dataset_yaml or resolve_dataset_yaml(config, args.config)).resolve()
    split = args.split or config.get("evaluation_split", "test")
    validate_dataset(dataset_yaml, split)

    results = []
    for model_name in args.models:
        weights = ROOT / config["output_dir"] / model_name / "weights" / "best.pt"
        if not weights.is_file():
            raise FileNotFoundError(f"Missing weights for {model_name}: {weights}")
        output_dir = ROOT / config["output_dir"] / model_name / f"evaluation_{split}"
        evaluation_config = {**config, "model_name": model_name, "weights": str(weights), "evaluation_split": split}
        results.append(evaluate_model(YOLO(str(weights)), dataset_yaml, output_dir, evaluation_config))

    comparison_path = ROOT / config.get("comparison_csv", "outputs/baseline/model_comparison.csv")
    comparison_path.parent.mkdir(parents=True, exist_ok=True)
    columns = sorted({key for result in results for key in result})
    with comparison_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(results)

    representative = max(results, key=lambda result: (result["map50_95"], result["map50"], result["recall"]))
    selection_path = comparison_path.with_name("baseline_representative.json")
    with selection_path.open("w", encoding="utf-8") as file:
        json.dump({"model": representative["model"], "selection_metric": "map50_95", "result": representative}, file, indent=2, ensure_ascii=True)
    print(f"Comparison CSV: {comparison_path}")
    print(f"Representative model: {representative['model']} (mAP50-95={representative['map50_95']:.4f})")


if __name__ == "__main__":
    main()
