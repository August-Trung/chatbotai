"""Robust spaCy NER training with Vietnamese tokenizer and early stopping."""

import os, sys, json, random
from pathlib import Path
from typing import List, Tuple
import spacy
from spacy.util import minibatch, compounding
from spacy.training import Example

OUT_DIR = Path("./improved_ner_vi/final_model")
OUT_DIR.mkdir(parents=True, exist_ok=True)
LABELS_PATH = OUT_DIR / "labels.json"


def load_data():
    try:
        import train_ner_data_fixed as data_mod  # chỗ gọi file dữ liệu
    except Exception as e:
        print("[ERROR] Cannot import train_ner_data_fixed.py:", e, file=sys.stderr)
        sys.exit(1)
    data = getattr(data_mod, "TRAIN_DATA", None) or getattr(data_mod, "DATA", None)
    if data is None:
        raise RuntimeError("Expected TRAIN_DATA or DATA in train_ner_data_fixed.py")
    return data


def sanitize_samples(nlp, raw):
    clean = []
    bad = 0
    for text, ann in raw:
        ents = ann.get("entities", [])
        doc = nlp.make_doc(text)
        spans = []
        for s, e, label in ents:
            span = doc.char_span(s, e, label=label, alignment_mode="contract")
            if span is not None:
                spans.append((span.start_char, span.end_char, label))
        if len(spans) != len(ents):
            bad += 1
            continue
        clean.append((text, {"entities": spans}))
    if bad:
        print(f"[WARN] Filtered {bad} misaligned samples out of {len(raw)}")
    return clean


def create_nlp():
    # Try to load Vietnamese models in order of preference
    for model_name in ["vi_core_news_lg", "vi_core_news_sm"]:
        try:
            nlp = spacy.load(model_name)
            print(f"[INFO] Loaded '{model_name}'")
            break
        except Exception:
            continue
    else:
        # Use blank Vietnamese model (works without pre-trained model)
        nlp = spacy.blank("vi")
        print("[INFO] Using blank('vi') - this will work fine for NER training!")

    if "ner" not in nlp.pipe_names:
        ner = nlp.add_pipe("ner", last=True)
    else:
        ner = nlp.get_pipe("ner")
    return nlp, ner


def split_train_dev(data, dev_ratio=0.2, seed=42):
    random.Random(seed).shuffle(data)
    k = max(1, int(len(data) * dev_ratio))
    return data[:-k], data[-k:]


def add_labels(ner, data):
    labels = set()
    for _, ann in data:
        for _, _, L in ann.get("entities", []):
            labels.add(L)
    for L in labels:
        ner.add_label(L)
    return sorted(labels)


def evaluate(nlp, data):
    ex = [Example.from_dict(nlp.make_doc(t), a) for t, a in data]
    scores = nlp.evaluate(ex)
    return {k: float(scores.get(k, 0.0)) for k in ("ents_p", "ents_r", "ents_f")}


def train():
    print("=" * 70)
    print("🚀 NER TRAINING - spaCy")
    print("=" * 70)

    raw = load_data()
    base = spacy.blank("vi")
    raw = sanitize_samples(base, raw)

    print(f"\n📊 Dataset loaded:")
    print(f"   - Total samples: {len(raw):,}")

    nlp, ner = create_nlp()
    labels = add_labels(ner, raw)
    print(f"   - Entity types: {len(labels)}")
    print(f"   - Labels: {', '.join(labels)}")

    train_data, dev_data = split_train_dev(raw, dev_ratio=0.2, seed=42)
    print(f"\n📂 Split:")
    print(f"   - Train: {len(train_data):,} samples")
    print(f"   - Dev:   {len(dev_data):,} samples")

    other = [p for p in nlp.pipe_names if p != "ner"]
    dropout = float(os.getenv("DROPOUT", "0.15"))
    n_iter = int(os.getenv("EPOCHS", "30"))
    patience = int(os.getenv("PATIENCE", "5"))

    print(f"\n⚙️  Training config:")
    print(f"   - Epochs: {n_iter}")
    print(f"   - Dropout: {dropout}")
    print(f"   - Patience: {patience}")
    print(f"   - Output dir: {OUT_DIR}")

    print(f"\n🔥 Starting training...")
    print("=" * 70)
    print(
        f"{'Epoch':>6} │ {'Loss':>8} │ {'Dev F1':>7} │ {'Precision':>9} │ {'Recall':>7} │ {'Status':>10}"
    )
    print("─" * 70)

    with nlp.disable_pipes(*other):
        optimizer = nlp.initialize(
            get_examples=lambda: [
                Example.from_dict(nlp.make_doc(t), a) for t, a in train_data
            ]
        )
        best_f = -1.0
        bad = 0

        for epoch in range(1, n_iter + 1):
            random.shuffle(train_data)
            losses = {}
            for batch in minibatch(train_data, size=compounding(4.0, 32.0, 1.5)):
                examples = [Example.from_dict(nlp.make_doc(t), a) for t, a in batch]
                nlp.update(examples, drop=dropout, sgd=optimizer, losses=losses)

            dev = evaluate(nlp, dev_data)
            loss = losses.get("ner", 0)

            status = ""
            if dev["ents_f"] > best_f + 1e-4:
                best_f = dev["ents_f"]
                bad = 0
                nlp.to_disk(OUT_DIR)
                status = "✅ BEST"
            else:
                bad += 1
                status = f"⚠️  +{bad}"
                if bad >= patience:
                    print(
                        f"{epoch:>6d} │ {loss:>8.4f} │ {dev['ents_f']:>7.4f} │ {dev['ents_p']:>9.4f} │ {dev['ents_r']:>7.4f} │ {status:>10}"
                    )
                    print("─" * 70)
                    print("[EARLY STOP] No improvement for {} epochs".format(patience))
                    break

            print(
                f"{epoch:>6d} │ {loss:>8.4f} │ {dev['ents_f']:>7.4f} │ {dev['ents_p']:>9.4f} │ {dev['ents_r']:>7.4f} │ {status:>10}"
            )

    print("=" * 70)

    LABELS_PATH.write_text(
        json.dumps({"labels": labels}, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n💾 Saved labels to {LABELS_PATH}")

    # Test predictions
    print("\n🧪 Testing with sample inputs...")
    test_samples = [
        "mở file report.xlsx bằng Excel",
        "phát nhạc Faded trên Spotify",
        "tìm kiếm python tutorial",
        "gửi email cho Alice",
        "đổi tên data.json thành data_new.json",
    ]

    nlp_final = spacy.load(OUT_DIR)

    print("\n📝 Sample Predictions:")
    results = []
    for text in test_samples:
        doc = nlp_final(text)
        ents = [(ent.text, ent.label_) for ent in doc.ents]
        result = f"{text:50s} → {ents if ents else '(no entities)'}"
        print(f"   {result}")
        results.append(result)

    sample_output = OUT_DIR / "sample_predictions.txt"
    sample_output.write_text("\n".join(results), encoding="utf-8")
    print(f"\n   ✅ Saved sample_predictions.txt")

    print("\n" + "=" * 70)
    print("✨ Training complete!")
    print("=" * 70)
    print(f"\n📁 Model saved to: {OUT_DIR}")
    print(f"   - config.cfg")
    print(f"   - meta.json")
    print(f"   - ner/")
    print(f"   - tokenizer/")
    print(f"   - labels.json")
    print(f"   - sample_predictions.txt")
    print(f"\n📊 Best Dev F1: {best_f:.4f}")
    print("\n🎉 Done!")


if __name__ == "__main__":
    train()
