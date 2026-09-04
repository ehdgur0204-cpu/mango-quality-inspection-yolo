"""Train YOLOv8n/s/m under identical baseline conditions.

Examples:
    python models/base_model/train_baseline.py --model all
    python models/base_model/train_baseline.py --model yolov8n --config configs/baseline.yaml
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch
from ultralytics import YOLO

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from models.base_model.common import load_config, resolve_dataset_yaml, validate_dataset


ROOT = Path(__file__).resolve().parents[2]
MODEL_WEIGHTS = {"yolov8n": "yolov8n.pt", "yolov8s": "yolov8s.pt", "yolov8m": "yolov8m.pt"}


def train_model(model_name: str, config: dict, dataset_yaml: Path) -> Path:
    output_dir = ROOT / config["output_dir"] / model_name
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    weights = config.get("weights", MODEL_WEIGHTS[model_name])
    model = YOLO(weights)
    model.train(
        data=str(dataset_yaml),
        epochs=config["epochs"],
        imgsz=config["imgsz"],
        batch=config["batch"],
        pretrained=config.get("pretrained", True),
        seed=config["seed"],
        device=config.get("device", "cpu"),
        workers=config.get("workers", 0),
        optimizer=config.get("optimizer", "auto"),
        project=str(output_dir.parent),
        name=output_dir.name,
        exist_ok=True,
        plots=True,
        **config.get("augmentation", {}),
    )
    best_weights = output_dir / "weights" / "best.pt"
    if not best_weights.exists():
        raise FileNotFoundError(f"Training finished but best weights were not found: {best_weights}")
    return best_weights


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/baseline.yaml")
    parser.add_argument("--model", choices=[*MODEL_WEIGHTS, "all"], default="all")
    parser.add_argument("--dataset-yaml", type=Path, help="Override dataset YAML from config")
    args = parser.parse_args()

    config = load_config(args.config)
    device = config.get("device", "cpu")
    if str(device) != "cpu" and not torch.cuda.is_available():
        raise RuntimeError(
            "GPU training was requested with device="
            f"{device}, but CUDA is not available. Install an NVIDIA driver and "
            "CUDA-enabled PyTorch, then restart the kernel."
        )
    if args.dataset_yaml:
        dataset_yaml = args.dataset_yaml.resolve()
    else:
        dataset_yaml = resolve_dataset_yaml(config, args.config)
    validate_dataset(dataset_yaml, config.get("evaluation_split", "test"))

    model_names = MODEL_WEIGHTS if args.model == "all" else {args.model: MODEL_WEIGHTS[args.model]}
    for model_name in model_names:
        model_config = {**config, "model_name": model_name}
        print(f"Training {model_name} on {dataset_yaml}")
        best_weights = train_model(model_name, model_config, dataset_yaml)
        print(f"Best weights: {best_weights}")


if __name__ == "__main__":
    main()
