# -*- coding: utf-8 -*-
"""
Adapter để load data từ dataset/nlu.jsonl cho NER Training
Compatible với train_ner.py
"""

import json
from pathlib import Path
from typing import List, Tuple, Dict


def load_nlu_data_for_ner(
    file_path: str = "dataset/nlu.jsonl",
) -> List[Tuple[str, Dict]]:
    """
    Load data từ file JSONL và convert sang format NER

    Format đầu vào: {"text": "...", "intent": "...", "entities": [{"start": 0, "end": 5, "entity": "FILE", "value": "..."}]}
    Format đầu ra: [("text", {"entities": [(start, end, label), ...]}), ...]
    """
    ner_data = []

    if not Path(file_path).exists():
        raise FileNotFoundError(f"Không tìm thấy file: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                item = json.loads(line)

                text = item["text"]
                entities = item.get("entities", [])

                # Convert entities format
                # From: [{"start": 0, "end": 5, "entity": "FILE", "value": "..."}]
                # To: [(0, 5, "FILE"), ...]
                ner_entities = []
                for ent in entities:
                    start = ent["start"]
                    end = ent["end"]
                    label = ent["entity"]  # FILE, APP, QUERY, etc.

                    ner_entities.append((start, end, label))

                # spaCy format
                ner_data.append((text, {"entities": ner_entities}))

    return ner_data


def get_train_data() -> List[Tuple[str, Dict]]:
    """
    Main function được gọi bởi train_ner.py
    Returns: List[(text, {"entities": [(start, end, label), ...]})]
    """
    print("[INFO] Loading NER data from dataset/nlu.jsonl...")

    # Try to load split files first
    train_file = Path("dataset/nlu_train.jsonl")
    val_file = Path("dataset/nlu_validation.jsonl")

    if train_file.exists() and val_file.exists():
        print(
            "[INFO] Found split files: using nlu_train.jsonl and nlu_validation.jsonl"
        )

        train_data = load_nlu_data_for_ner(str(train_file))
        val_data = load_nlu_data_for_ner(str(val_file))

        all_data = train_data + val_data

    else:
        print(
            "[INFO] Split files not found. Using full nlu.jsonl (will auto-split in train_ner.py)"
        )
        all_data = load_nlu_data_for_ner("dataset/nlu.jsonl")

    # Statistics
    entity_counts = {}
    samples_with_entities = 0

    for text, annotations in all_data:
        entities = annotations.get("entities", [])
        if entities:
            samples_with_entities += 1

        for start, end, label in entities:
            entity_counts[label] = entity_counts.get(label, 0) + 1

    print(f"[INFO] Loaded {len(all_data)} samples:")
    print(
        f"       - Samples with entities: {samples_with_entities} ({samples_with_entities/len(all_data)*100:.1f}%)"
    )
    print(f"[INFO] Entity type distribution:")
    for entity_type, count in sorted(entity_counts.items()):
        print(f"       - {entity_type:15s}: {count:5d} occurrences")

    return all_data


# Main export for train_ner.py
TRAIN_DATA = get_train_data()
DATA = TRAIN_DATA  # Backward compatibility


def validate_data(data: List[Tuple[str, Dict]], max_samples: int = 5):
    """Validate và hiển thị mẫu data"""
    print("\n[INFO] Validating data...")

    errors = 0

    for i, (text, annotations) in enumerate(data):
        entities = annotations.get("entities", [])

        for start, end, label in entities:
            # Check boundaries
            if start < 0 or end > len(text) or start >= end:
                print(
                    f"[ERROR] Invalid entity at sample {i}: [{start}:{end}] in text of length {len(text)}"
                )
                errors += 1
                continue

            # Check text match
            entity_text = text[start:end]
            if not entity_text.strip():
                print(f"[WARN] Empty entity at sample {i}: '{entity_text}'")

    if errors > 0:
        print(f"[WARN] Found {errors} validation errors!")
    else:
        print(f"[INFO] ✅ All entities are valid!")

    # Show samples
    print(f"\n[INFO] Sample data (first {min(max_samples, len(data))}):")
    for i, (text, annotations) in enumerate(data[:max_samples], 1):
        entities = annotations.get("entities", [])
        print(f"\n{i}. Text: {text}")
        if entities:
            print(f"   Entities:")
            for start, end, label in entities:
                entity_value = text[start:end]
                print(f"     - {label:10s} [{start:3d}:{end:3d}] = '{entity_value}'")
        else:
            print(f"   Entities: (none)")


if __name__ == "__main__":
    # Test loading
    print("=" * 70)
    print("Testing NER data loading...")
    print("=" * 70)

    data = get_train_data()

    # Validate
    validate_data(data, max_samples=10)

    print("\n" + "=" * 70)
    print("✅ NER data loading test successful!")
    print("=" * 70)
