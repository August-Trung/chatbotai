"""PhoBERT NER training with GPU support and visualization for Vietnamese."""

import os, sys, json, random
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
    Trainer,
    TrainingArguments,
    DataCollatorForTokenClassification,
    TrainerCallback,
)
from seqeval.metrics import (
    classification_report,
    f1_score,
    precision_score,
    recall_score,
)
from dataclasses import dataclass
import matplotlib.pyplot as plt
import matplotlib

matplotlib.use("Agg")  # Non-GUI backend
from sklearn.metrics import confusion_matrix
import seaborn as sns


def _import_data_module():
    try:
        import importlib

        return importlib.import_module("train_ner_data_fixed")
    except Exception as e:
        print(f"[ERROR] Cannot import train_ner_data_fixed.py: {e}", file=sys.stderr)
        sys.exit(1)


def load_and_prepare_data():
    """Load NER data and convert to token classification format."""
    m = _import_data_module()
    raw = getattr(m, "TRAIN_DATA", None) or getattr(m, "DATA", None)
    if raw is None:
        raise RuntimeError("Expected TRAIN_DATA or DATA")

    # Extract all labels
    all_labels = set()
    for text, ann in raw:
        for _, _, label in ann.get("entities", []):
            all_labels.add(f"B-{label}")
            all_labels.add(f"I-{label}")
    all_labels.add("O")

    label_list = sorted(all_labels)
    label2id = {l: i for i, l in enumerate(label_list)}
    id2label = {i: l for l, i in label2id.items()}

    return raw, label_list, label2id, id2label


def convert_to_bio(text, entities, tokenizer, label2id):
    """Convert span annotations to BIO token labels."""
    encoding = tokenizer(text, truncation=True, max_length=128)

    # Get tokens and reconstruct character positions
    tokens = tokenizer.convert_ids_to_tokens(encoding["input_ids"])

    # Create labels for each token
    labels = ["O"] * len(tokens)

    # Build character-to-token mapping
    char_to_token = {}
    current_pos = 0

    for token_idx, token in enumerate(tokens):
        # Skip special tokens
        if token in ["<s>", "</s>", "<pad>", "<unk>"]:
            continue

        # Clean token (remove Ġ or ## prefixes if present)
        clean_token = token.replace("Ġ", " ").replace("@@", "")

        # Find token in text starting from current position
        token_start = text.find(clean_token, current_pos)

        if token_start != -1:
            token_end = token_start + len(clean_token)

            # Map all characters in this token to token_idx
            for char_pos in range(token_start, token_end):
                char_to_token[char_pos] = token_idx

            current_pos = token_end

    # Assign labels based on entity spans
    for start, end, entity_type in entities:
        token_indices = set()

        # Find all tokens that overlap with this entity
        for char_pos in range(start, end):
            if char_pos in char_to_token:
                token_indices.add(char_to_token[char_pos])

        # Sort token indices and assign B- and I- labels
        for idx, token_idx in enumerate(sorted(token_indices)):
            if idx == 0:
                labels[token_idx] = f"B-{entity_type}"
            else:
                labels[token_idx] = f"I-{entity_type}"

    # Convert labels to ids
    label_ids = [label2id.get(l, label2id["O"]) for l in labels]

    return encoding, label_ids


@dataclass
class NERDataset:
    encodings: List[Dict]
    labels: List[List[int]]

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        item = {key: val[idx] for key, val in self.encodings.items()}
        item["labels"] = self.labels[idx]
        return item


def prepare_datasets(raw_data, tokenizer, label2id, split_ratio=0.2):
    """Prepare train and validation datasets."""
    random.shuffle(raw_data)
    split_point = int(len(raw_data) * (1 - split_ratio))

    train_raw = raw_data[:split_point]
    val_raw = raw_data[split_point:]

    def process_data(data):
        all_encodings = {"input_ids": [], "attention_mask": []}
        all_labels = []

        for text, ann in data:
            entities = ann.get("entities", [])
            encoding, labels = convert_to_bio(text, entities, tokenizer, label2id)

            all_encodings["input_ids"].append(encoding["input_ids"])
            all_encodings["attention_mask"].append(encoding["attention_mask"])
            all_labels.append(labels)

        return NERDataset(all_encodings, all_labels)

    return process_data(train_raw), process_data(val_raw)


def compute_metrics(pred, id2label):
    """Compute seqeval metrics for NER."""
    predictions, labels = pred
    predictions = np.argmax(predictions, axis=2)

    true_labels = []
    pred_labels = []

    for prediction, label in zip(predictions, labels):
        true_label = []
        pred_label = []

        for p, l in zip(prediction, label):
            if l != -100:  # Ignore padding
                true_label.append(id2label[l])
                pred_label.append(id2label[p])

        true_labels.append(true_label)
        pred_labels.append(pred_label)

    return {
        "precision": precision_score(true_labels, pred_labels),
        "recall": recall_score(true_labels, pred_labels),
        "f1": f1_score(true_labels, pred_labels),
    }


class MetricsCallback(TrainerCallback):
    """Callback to collect training metrics for plotting."""

    def __init__(self):
        self.train_losses = []
        self.eval_losses = []
        self.eval_metrics = {
            "precision": [],
            "recall": [],
            "f1": [],
        }
        self.epochs = []

    def on_log(self, args, state, control, logs=None, **kwargs):
        if logs:
            if "loss" in logs:
                self.train_losses.append(
                    {"step": state.global_step, "loss": logs["loss"]}
                )

    def on_evaluate(self, args, state, control, metrics=None, **kwargs):
        if metrics:
            epoch = state.epoch
            self.epochs.append(epoch)

            if "eval_loss" in metrics:
                self.eval_losses.append({"epoch": epoch, "loss": metrics["eval_loss"]})

            for key in ["eval_precision", "eval_recall", "eval_f1"]:
                if key in metrics:
                    metric_name = key.replace("eval_", "")
                    self.eval_metrics[metric_name].append(
                        {"epoch": epoch, "value": metrics[key]}
                    )


def plot_training_curves(metrics_callback, output_dir):
    """Plot training and validation curves."""
    output_dir = Path(output_dir)

    # 1. Loss curves
    fig, ax = plt.subplots(figsize=(10, 6))

    if metrics_callback.train_losses:
        train_steps = [x["step"] for x in metrics_callback.train_losses]
        train_loss = [x["loss"] for x in metrics_callback.train_losses]
        ax.plot(train_steps, train_loss, label="Training Loss", alpha=0.7)

    if metrics_callback.eval_losses:
        eval_epochs = [x["epoch"] for x in metrics_callback.eval_losses]
        eval_loss = [x["loss"] for x in metrics_callback.eval_losses]
        # Convert epochs to approximate steps for alignment
        if train_steps:
            max_step = max(train_steps)
            max_epoch = max(eval_epochs) if eval_epochs else 1
            eval_steps = [e * (max_step / max_epoch) for e in eval_epochs]
            ax.plot(
                eval_steps, eval_loss, label="Validation Loss", marker="o", linewidth=2
            )

    ax.set_xlabel("Training Steps")
    ax.set_ylabel("Loss")
    ax.set_title("Training and Validation Loss")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / "loss_curve.png", dpi=150, bbox_inches="tight")
    plt.close()

    # 2. Metrics curves (Precision, Recall, F1)
    fig, ax = plt.subplots(figsize=(10, 6))

    for metric_name, metric_data in metrics_callback.eval_metrics.items():
        if metric_data:
            epochs = [x["epoch"] for x in metric_data]
            values = [x["value"] for x in metric_data]
            ax.plot(
                epochs, values, label=metric_name.capitalize(), marker="o", linewidth=2
            )

    ax.set_xlabel("Epoch")
    ax.set_ylabel("Score")
    ax.set_title("Validation Metrics (Precision, Recall, F1)")
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_ylim([0, 1])
    plt.tight_layout()
    plt.savefig(output_dir / "metrics_curve.png", dpi=150, bbox_inches="tight")
    plt.close()


def plot_confusion_matrix(model, dataset, tokenizer, id2label, output_dir):
    """Plot confusion matrix for entity types."""
    output_dir = Path(output_dir)

    model.eval()
    model_cpu = model.cpu() if model.training else model

    all_true = []
    all_pred = []

    # Get predictions
    for idx in range(len(dataset)):
        item = dataset[idx]
        inputs = {
            "input_ids": torch.tensor([item["input_ids"]]),
            "attention_mask": torch.tensor([item["attention_mask"]]),
        }

        with torch.no_grad():
            outputs = model_cpu(**inputs)
            predictions = torch.argmax(outputs.logits, dim=2)[0]

        labels = item["labels"]

        for pred, true in zip(predictions.tolist(), labels):
            if true != -100:
                all_true.append(id2label[true])
                all_pred.append(id2label[pred])

    # Get unique entity types (remove B-/I- prefixes)
    entity_types = sorted(
        set([label.split("-")[1] if "-" in label else label for label in all_true])
    )

    # Simplify labels for confusion matrix
    true_simple = [label.split("-")[1] if "-" in label else label for label in all_true]
    pred_simple = [label.split("-")[1] if "-" in label else label for label in all_pred]

    # Create confusion matrix
    cm = confusion_matrix(true_simple, pred_simple, labels=entity_types)

    # Plot
    fig, ax = plt.subplots(figsize=(12, 10))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=entity_types,
        yticklabels=entity_types,
        ax=ax,
        cbar_kws={"label": "Count"},
    )
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title("Confusion Matrix (Entity Types)")
    plt.tight_layout()
    plt.savefig(output_dir / "confusion_matrix.png", dpi=150, bbox_inches="tight")
    plt.close()


def plot_entity_distribution(raw_data, output_dir):
    """Plot entity type distribution in dataset."""
    output_dir = Path(output_dir)

    entity_counts = {}

    for text, ann in raw_data:
        for _, _, label in ann.get("entities", []):
            entity_counts[label] = entity_counts.get(label, 0) + 1

    if not entity_counts:
        return

    # Sort by count
    sorted_entities = sorted(entity_counts.items(), key=lambda x: x[1], reverse=True)
    labels = [x[0] for x in sorted_entities]
    counts = [x[1] for x in sorted_entities]

    # Plot
    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(range(len(labels)), counts, color="steelblue", alpha=0.8)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.set_xlabel("Entity Type")
    ax.set_ylabel("Count")
    ax.set_title("Entity Type Distribution in Dataset")
    ax.grid(True, alpha=0.3, axis="y")

    # Add count labels on bars
    for bar, count in zip(bars, counts):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            height,
            f"{int(count)}",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    plt.tight_layout()
    plt.savefig(output_dir / "entity_distribution.png", dpi=150, bbox_inches="tight")
    plt.close()


def main():
    print("=" * 70)
    print("🚀 NER TRAINING - PhoBERT")
    print("=" * 70)

    # ============================================
    # GPU SETUP
    # ============================================
    print("\n🔍 Checking GPU availability...")
    if torch.cuda.is_available():
        device = torch.device("cuda")
        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
        print(f"   ✅ GPU detected: {gpu_name}")
        print(f"   ✅ GPU memory: {gpu_memory:.2f} GB")
        print(f"   ✅ CUDA version: {torch.version.cuda}")
        print(f"   ✅ Training will use GPU")
    else:
        device = torch.device("cpu")
        print(f"   ⚠️  No GPU detected - training will use CPU")
    # ============================================

    # Load data
    raw_data, label_list, label2id, id2label = load_and_prepare_data()

    print(f"\n📊 Dataset loaded:")
    print(f"   - Total samples: {len(raw_data):,}")
    print(f"   - Entity types: {len(label_list)}")
    print(f"   - Labels: {', '.join(label_list)}")

    # Load tokenizer and model
    base = os.getenv("NER_BASE_MODEL", "vinai/phobert-base")
    out = Path("./phobert_ner_model")
    out.mkdir(exist_ok=True)

    print(f"\n🔧 Loading model: {base}")
    tokenizer = AutoTokenizer.from_pretrained(base, use_fast=False)
    model = AutoModelForTokenClassification.from_pretrained(
        base,
        num_labels=len(label_list),
        id2label=id2label,
        label2id=label2id,
    )

    # Prepare datasets
    print(f"\n🔄 Encoding data...")
    train_dataset, val_dataset = prepare_datasets(raw_data, tokenizer, label2id)

    print(f"\n📂 Split:")
    print(f"   - Train: {len(train_dataset):,} samples")
    print(f"   - Val:   {len(val_dataset):,} samples")

    # Training config
    batch_size = int(os.getenv("BATCH_SIZE", "16"))
    epochs = int(os.getenv("EPOCHS", "10"))
    lr = float(os.getenv("LR", "2e-5"))

    print(f"\n⚙️  Training config:")
    print(f"   - Device: {device}")
    print(f"   - Batch size: {batch_size}")
    print(f"   - Epochs: {epochs}")
    print(f"   - Learning rate: {lr}")
    print(f"   - Output dir: {out}")

    # Metrics callback
    metrics_callback = MetricsCallback()

    # Training arguments
    args = TrainingArguments(
        output_dir=str(out),
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=32,
        num_train_epochs=epochs,
        learning_rate=lr,
        weight_decay=0.01,
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=3,
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        greater_is_better=True,
        logging_steps=50,
        report_to=[],
        # GPU optimization
        fp16=torch.cuda.is_available(),
        dataloader_pin_memory=True,
        dataloader_num_workers=0,
    )

    # Data collator
    data_collator = DataCollatorForTokenClassification(tokenizer, padding=True)

    # Trainer
    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=lambda p: compute_metrics(p, id2label),
        callbacks=[metrics_callback],
    )

    print(f"\n🔥 Starting training...")
    print("=" * 70)
    trainer.train()

    print("\n" + "=" * 70)
    print("📊 Evaluating model...")
    metrics = trainer.evaluate()
    print("\n[EVALUATION RESULTS]")
    for key, value in metrics.items():
        print(f"   - {key:20s}: {value:.4f}")

    print(f"\n💾 Saving model to {out}")
    trainer.save_model(out)
    tokenizer.save_pretrained(out)

    # Save labels
    labels_path = out / "labels.json"
    labels_path.write_text(
        json.dumps({"labels": label_list}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"   ✅ Saved labels.json")

    # ============================================
    # GENERATE PLOTS
    # ============================================
    print("\n📈 Generating visualization plots...")

    try:
        # 1. Training curves
        print("   - Plotting loss curves...")
        plot_training_curves(metrics_callback, out)
        print("   ✅ Saved loss_curve.png")
        print("   ✅ Saved metrics_curve.png")

        # 2. Entity distribution
        print("   - Plotting entity distribution...")
        plot_entity_distribution(raw_data, out)
        print("   ✅ Saved entity_distribution.png")

        # 3. Confusion matrix
        print("   - Plotting confusion matrix...")
        plot_confusion_matrix(trainer.model, val_dataset, tokenizer, id2label, out)
        print("   ✅ Saved confusion_matrix.png")

    except Exception as e:
        print(f"   ⚠️  Warning: Could not generate all plots: {e}")
    # ============================================

    # Test predictions
    print("\n🧪 Testing with sample inputs...")
    test_samples = [
        "mở file report.xlsx bằng Excel",
        "phát nhạc Faded trên Spotify",
        "tìm kiếm python tutorial",
        "gửi email cho Alice",
        "đổi tên data.json thành data_new.json",
    ]

    print("\n📝 Sample Predictions:")
    model_cpu = model.cpu() if torch.cuda.is_available() else model

    results = []
    for text in test_samples:
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=128)

        with torch.no_grad():
            outputs = model_cpu(**inputs)
            predictions = torch.argmax(outputs.logits, dim=2)

        tokens = tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])
        pred_labels = [id2label[p.item()] for p in predictions[0]]

        # Extract entities
        entities = []
        current_entity = None

        for token, label in zip(tokens, pred_labels):
            if token in ["<s>", "</s>", "<pad>"]:
                continue

            if label.startswith("B-"):
                if current_entity:
                    entities.append(current_entity)
                current_entity = {"text": token, "label": label[2:]}
            elif label.startswith("I-") and current_entity:
                current_entity["text"] += " " + token
            else:
                if current_entity:
                    entities.append(current_entity)
                    current_entity = None

        if current_entity:
            entities.append(current_entity)

        ents_str = [(e["text"], e["label"]) for e in entities]
        result = f"{text:50s} → {ents_str if ents_str else '(no entities)'}"
        print(f"   {result}")
        results.append(result)

    sample_output = out / "sample_predictions.txt"
    sample_output.write_text("\n".join(results), encoding="utf-8")
    print(f"\n   ✅ Saved sample_predictions.txt")

    # GPU cleanup
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        print("\n🧹 GPU memory cache cleared")

    print("\n" + "=" * 70)
    print("✨ Training complete!")
    print("=" * 70)
    print(f"\n📁 Model saved to: {out}")
    print(f"   - config.json")
    print(f"   - pytorch_model.bin")
    print(f"   - tokenizer files")
    print(f"   - labels.json")
    print(f"   - sample_predictions.txt")
    print(f"\n📊 Visualization plots:")
    print(f"   - loss_curve.png")
    print(f"   - metrics_curve.png")
    print(f"   - entity_distribution.png")
    print(f"   - confusion_matrix.png")
    print("\n🎉 Done!")


if __name__ == "__main__":
    main()
