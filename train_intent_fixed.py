"""Robust PhoBERT fine-tuning for Vietnamese intent classification."""

import os, sys, json, random
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix,
    classification_report,
)
import matplotlib.pyplot as plt
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
    DataCollatorWithPadding,
)
from sklearn.utils.multiclass import unique_labels
import transformers, sys

def _import_data_module():
    import importlib

    try:
        return importlib.import_module("train_intent_data_fixed")
    except Exception as e:
        print("[ERROR] Cannot import train_intent_data_fixed.py:", e, file=sys.stderr)
        sys.exit(1)


def _normalize_dataset(m):
    if hasattr(m, "get_data"):
        data = m.get_data()
        train = [x for x in data if x.get("split", "train") == "train"]
        val = [
            x
            for x in data
            if x.get("split", "train") in ("val", "valid", "dev", "test")
        ]
        if not val:
            k = max(1, len(train) // 5)
            return train[:-k], train[-k:]
        return train, val
    for a, b in [
        ("TRAIN", "VAL"),
        ("TRAIN", "VALID"),
        ("TRAIN", "DEV"),
        ("TRAIN", "TEST"),
    ]:
        if hasattr(m, a):
            train = getattr(m, a)
            val = getattr(m, b, None) or []
            if not val:
                k = max(1, len(train) // 5)
                return train[:-k], train[-k:]
            return train, val
    if hasattr(m, "DATA"):
        data = getattr(m, "DATA")
        k = max(1, int(0.2 * len(data)))
        return data[:-k], data[-k:]
    raise RuntimeError("train_intent_data.py missing expected variables")


def _ensure_items(items):
    norm = []
    for x in items:
        if isinstance(x, dict) and "text" in x and "label" in x:
            norm.append({"text": str(x["text"]), "label": str(x["label"])})
        elif isinstance(x, (list, tuple)) and len(x) >= 2:
            norm.append({"text": str(x[0]), "label": str(x[1])})
        else:
            raise ValueError(f"Invalid sample format: {x}")
    return norm


@dataclass
class SimpleDS:
    encodings: Any
    labels: List[int]

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        # HuggingFace Trainer expects input_ids, attention_mask, labels
        item = {key: val[idx] for key, val in self.encodings.items()}
        item["labels"] = self.labels[idx]
        return item

def build_label_map(items):
    labels = sorted(list({it["label"] for it in items}))
    return {l: i for i, l in enumerate(labels)}, {i: l for l, i in enumerate(labels)}


def compute_metrics(eval_pred):
    import numpy as np

    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    acc = accuracy_score(labels, preds)
    prec, rec, f1, _ = precision_recall_fscore_support(
        labels, preds, average="weighted", zero_division=0
    )
    return {"accuracy": acc, "precision": prec, "recall": rec, "f1": f1}


def main():
    m = _import_data_module()
    train_raw, val_raw = _normalize_dataset(m)
    train_raw, val_raw = _ensure_items(train_raw), _ensure_items(val_raw)
    labels = sorted(list({it["label"] for it in (train_raw + val_raw)}))
    label2id = {l: i for i, l in enumerate(labels)}
    id2label = {i: l for l, i in label2id.items()}

    base = os.getenv("INTENT_BASE_MODEL", "vinai/phobert-base")
    out = Path("./phobert_intent_model")
    out.mkdir(exist_ok=True)
    tok = AutoTokenizer.from_pretrained(base, use_fast=False)
    mdl = AutoModelForSequenceClassification.from_pretrained(
        base, num_labels=len(labels), id2label=id2label, label2id=label2id
    )

    def encode_items(items):
        texts = [it["text"] for it in items]
        y = [label2id[it["label"]] for it in items]
        encodings = tok(texts, truncation=True, padding=True, max_length=128)
        return SimpleDS(encodings, y)

    train_ds = encode_items(train_raw)
    val_ds = encode_items(val_raw)

    collator = DataCollatorWithPadding(tok)
    args = TrainingArguments(
        output_dir=str(out),
        per_device_train_batch_size=int(os.getenv("BATCH_SIZE", "16")),
        per_device_eval_batch_size=int(os.getenv("EVAL_BATCH_SIZE", "32")),
        num_train_epochs=float(os.getenv("EPOCHS", "5")),
        learning_rate=float(os.getenv("LR", "3e-5")),
        weight_decay=float(os.getenv("WD", "0.01")),
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=3,
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        greater_is_better=True,
        logging_steps=50,
        report_to=[],
    )
    trainer = Trainer(
        model=mdl,
        args=args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        tokenizer=tok,
        data_collator=collator,
        compute_metrics=compute_metrics,
    )
    trainer.train()
    metrics = trainer.evaluate()
    print("[EVAL]", metrics)
    trainer.save_model(out)
    tok.save_pretrained(out)

    # Confusion matrix & report
    import numpy as np, matplotlib.pyplot as plt
    from sklearn.metrics import confusion_matrix, classification_report

    preds = trainer.predict(val_ds)
    y_true = preds.label_ids
    y_pred = np.argmax(preds.predictions, axis=-1)
    cm = confusion_matrix(y_true, y_pred)
    fig = plt.figure(figsize=(6, 6))
    plt.imshow(cm, interpolation="nearest")
    plt.title("Confusion Matrix")
    plt.colorbar()
    ticks = np.arange(len(labels))
    plt.xticks(ticks, labels, rotation=45, ha="right")
    plt.yticks(ticks, labels)
    plt.tight_layout()
    plt.ylabel("True")
    plt.xlabel("Predicted")
    fig.savefig(out / "confusion_matrix.png", dpi=150, bbox_inches="tight")
    used_labels = sorted(list(unique_labels(y_true)))
    rep = classification_report(
        y_true,
        y_pred,
        labels=used_labels,
        target_names=[labels[i] for i in used_labels],
        zero_division=0
    )
    (out / "classification_report.txt").write_text(rep, encoding="utf-8")

    # Sample predictions
    samples = [
        "mở zalo",
        "đóng word",
        "tìm thời tiết hôm nay",
        "xem thêm kết quả",
        "mấy giờ rồi",
    ]
    with open(out / "sample_predictions.txt", "w", encoding="utf-8") as f:
        for s in samples:
            t = tok(s, return_tensors="pt", truncation=True, max_length=128)
            with torch.no_grad():
                p = mdl(**t).logits.argmax(dim=-1).item()
            f.write(f"{s} -> {id2label[p]}\n")
    print("[DONE] Saved to", out)


if __name__ == "__main__":
    main()
