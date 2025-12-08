# -*- coding: utf-8 -*-
"""
Adapter để load data từ dataset/nlu.jsonl cho Intent Classification
Compatible với train_intent.py
"""

import json
from pathlib import Path
from typing import List, Dict


def load_nlu_data(file_path: str = "dataset/nlu.jsonl") -> List[Dict]:
    """Load data từ file JSONL mới"""
    data = []

    if not Path(file_path).exists():
        raise FileNotFoundError(f"Không tìm thấy file: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                # Convert format: {"text": ..., "intent": ..., "entities": [...]}
                # → {"text": ..., "label": ...}
                data.append({"text": item["text"], "label": item["intent"]})

    return data


def get_data() -> List[Dict]:
    """
    Main function được gọi bởi train_intent.py
    Returns: List[{"text": str, "label": str, "split": str}]
    """
    print("[INFO] Loading data from dataset/nlu.jsonl...")

    # Try to load split files first (if exist)
    train_file = Path("dataset/nlu_train.jsonl")
    val_file = Path("dataset/nlu_validation.jsonl")

    if train_file.exists() and val_file.exists():
        print(
            "[INFO] Found split files: using nlu_train.jsonl and nlu_validation.jsonl"
        )

        train_data = load_nlu_data(str(train_file))
        val_data = load_nlu_data(str(val_file))

        # Add split marker
        for item in train_data:
            item["split"] = "train"
        for item in val_data:
            item["split"] = "val"

        all_data = train_data + val_data

    else:
        print(
            "[INFO] Split files not found. Using full nlu.jsonl (will auto-split 80/20)"
        )

        all_data = load_nlu_data("dataset/nlu.jsonl")

        # Auto split 80/20
        import random

        random.seed(42)
        random.shuffle(all_data)

        split_idx = int(len(all_data) * 0.8)

        for i, item in enumerate(all_data):
            item["split"] = "train" if i < split_idx else "val"

    # Statistics
    train_count = sum(1 for x in all_data if x["split"] == "train")
    val_count = sum(1 for x in all_data if x["split"] == "val")
    intent_counts = {}
    for item in all_data:
        label = item["label"]
        intent_counts[label] = intent_counts.get(label, 0) + 1

    print(f"[INFO] Loaded {len(all_data)} samples:")
    print(f"       - Train: {train_count} samples")
    print(f"       - Val:   {val_count} samples")
    print(f"[INFO] Intent distribution:")
    for intent, count in sorted(intent_counts.items()):
        print(f"       - {intent:20s}: {count:5d} samples")

    return all_data


# Backward compatibility - nếu code cũ gọi TRAIN/VAL trực tiếp
def _get_split_data():
    """Helper to get train/val separately"""
    data = get_data()
    train = [x for x in data if x.get("split", "train") == "train"]
    val = [x for x in data if x.get("split", "train") == "val"]
    return train, val


# Export variables for backward compatibility
TRAIN, VAL = _get_split_data()
DATA = get_data()


if __name__ == "__main__":
    # Test loading
    print("=" * 70)
    print("Testing data loading...")
    print("=" * 70)

    data = get_data()

    print(f"\n📊 Sample data (first 5):")
    for i, sample in enumerate(data[:5], 1):
        print(f"\n{i}. Split: {sample['split']}")
        print(f"   Label: {sample['label']}")
        print(f"   Text:  {sample['text']}")

    print("\n" + "=" * 70)
    print("✅ Data loading test successful!")
    print("=" * 70)
