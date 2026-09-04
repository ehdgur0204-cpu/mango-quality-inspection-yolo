"""Shared helpers for repeatable YOLO baseline experiments."""

from __future__ import annotations

import json
import shutil
import time
from pathlib import Path
from typing import Any

import yaml


DEFAULT_NAMES = {0: "Alternaria", 1: "Anthracnose", 2: "Healthy", 3: "Scab"}


def load_config(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as file:
        config = yaml.safe_load(file) or {}
    return config


def resolve_dataset_yaml(config: dict[str, Any], config_path: Path) -> Path:
    dataset_yaml = Path(config["dataset_yaml"])
    if not dataset_yaml.is_absolute():
        dataset_yaml = (config_path.parent / dataset_yaml).resolve()
    if not dataset_yaml.is_file() and config.get("source_root"):
        source_root = Path(config["source_root"])
        if not source_root.is_absolute():
            source_root = (config_path.parent / source_root).resolve()
        staging_root = Path(config.get("staging_dir", "outputs/temp/yolo_dataset"))
        if not staging_root.is_absolute():
            staging_root = (config_path.parent / staging_root).resolve()
        prepare_flat_dataset(source_root, staging_root)
        write_dataset_yaml(staging_root, dataset_yaml)
    if not dataset_yaml.is_file():
        raise FileNotFoundError(
            f"Dataset YAML not found: {dataset_yaml}. "
            "Create it from configs/data.example.yaml or run with --dataset-yaml."
        )
    return dataset_yaml


def prepare_flat_dataset(source_root: Path, staging_root: Path) -> None:
    """Stage flat *_images/*_labels folders in Ultralytics' standard layout."""
    for split in ("train", "val", "test"):
        source_images = source_root / f"{split}_images"
        source_labels = source_root / f"{split}_labels"
        if not source_images.is_dir() or not source_labels.is_dir():
            raise FileNotFoundError(
                f"Expected flat split folders: {source_images} and {source_labels}"
            )
        for source_dir, target_dir in (
            (source_images, staging_root / "images" / split),
            (source_labels, staging_root / "labels" / split),
        ):
            target_dir.mkdir(parents=True, exist_ok=True)
            for source_file in source_dir.iterdir():
                if source_file.is_file():
                    target_file = target_dir / source_file.name
                    if not target_file.exists() or source_file.stat().st_mtime > target_file.stat().st_mtime:
                        shutil.copy2(source_file, target_file)


def validate_dataset(dataset_yaml: Path, split: str = "test") -> dict[str, Any]:
    data = load_config(dataset_yaml)
    if not data.get("path"):
        raise ValueError(f"Dataset YAML must define 'path': {dataset_yaml}")
    root = Path(data["path"])
    if not root.is_absolute():
        root = (dataset_yaml.parent / root).resolve()

    for required_split in ("train", "val", split):
        split_path = Path(data.get(required_split, ""))
        if not split_path:
            raise ValueError(f"Dataset YAML must define '{required_split}'")
        if not split_path.is_absolute():
            split_path = root / split_path
        if not split_path.exists():
            raise FileNotFoundError(
                f"Dataset split '{required_split}' does not exist: {split_path}"
            )

    names = data.get("names", DEFAULT_NAMES)
    if isinstance(names, list):
        names = {index: name for index, name in enumerate(names)}
    data["path"] = str(root)
    data["names"] = names
    return data


def write_dataset_yaml(dataset_root: Path, output_path: Path) -> Path:
    """Create a standard YAML when a downloaded dataset has no data.yaml."""
    data = {
        "path": str(dataset_root.resolve()),
        "train": "images/train",
        "val": "images/val",
        "test": "images/test",
        "names": DEFAULT_NAMES,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        yaml.safe_dump(data, file, allow_unicode=False, sort_keys=False)
    return output_path


def metric_value(metrics: Any, name: str) -> float:
    value = getattr(metrics, name, None)
    if value is None and hasattr(metrics, "results_dict"):
        value = metrics.results_dict.get(name)
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def evaluate_model(model: Any, dataset_yaml: Path, output_dir: Path, config: dict[str, Any]) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    split = config.get("evaluation_split", "test")
    started = time.perf_counter()
    metrics = model.val(
        data=str(dataset_yaml),
        split=split,
        imgsz=config["imgsz"],
        batch=config["batch"],
        device=config.get("device", "cpu"),
        workers=config.get("workers", 0),
        project=str(output_dir.parent),
        name=output_dir.name,
        exist_ok=True,
        plots=True,
        verbose=False,
    )
    evaluation_seconds = time.perf_counter() - started

    dataset = validate_dataset(dataset_yaml, split)
    split_path = Path(dataset[split])
    if not split_path.is_absolute():
        split_path = Path(dataset["path"]) / split_path
    model.predict(
        source=str(split_path),
        imgsz=config["imgsz"],
        device=config.get("device", "cpu"),
        project=str(output_dir),
        name="val_predictions",
        exist_ok=True,
        save=True,
        save_conf=True,
        verbose=False,
    )

    speed = getattr(metrics, "speed", {}) or {}
    result = {
        "model": config["model_name"],
        "weights": str(config["weights"]),
        "dataset": config.get("dataset_name", "raw"),
        "split": split,
        "precision": metric_value(metrics.box, "mp"),
        "recall": metric_value(metrics.box, "mr"),
        "map50": metric_value(metrics.box, "map50"),
        "map50_95": metric_value(metrics.box, "map"),
        "inference_ms_per_image": float(speed.get("inference", float("nan"))),
        "evaluation_seconds": evaluation_seconds,
        "model_size_mb": Path(config["weights"]).stat().st_size / (1024 * 1024),
    }

    box_metrics = getattr(metrics, "box", None)
    names = dataset["names"]
    for class_id, average_precision in enumerate(getattr(box_metrics, "maps", [])):
        class_name = names.get(class_id, str(class_id))
        result[f"precision_{class_name}"] = float(box_metrics.p[class_id])
        result[f"recall_{class_name}"] = float(box_metrics.r[class_id])
        result[f"ap50_{class_name}"] = float(box_metrics.ap50[class_id])
        result[f"ap_{class_name}"] = float(average_precision)
    with (output_dir / "metrics.json").open("w", encoding="utf-8") as file:
        json.dump(result, file, indent=2, ensure_ascii=True, allow_nan=True)
    return result
