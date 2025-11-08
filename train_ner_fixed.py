""" Robust spaCy NER training with Vietnamese tokenizer and early stopping. """
import os, sys, json, random
from pathlib import Path
from typing import List, Tuple
import spacy
from spacy.util import minibatch, compounding
from spacy.training import Example

OUT_DIR = Path("./improved_ner_vi/final_model"); OUT_DIR.mkdir(parents=True, exist_ok=True)
LABELS_PATH = OUT_DIR / "labels.json"

def load_data():
    try:
        import train_ner_data_fixed as data_mod
    except Exception as e:
        print("[ERROR] Cannot import train_ner_data_fixed.py:", e, file=sys.stderr)
        sys.exit(1)
    data = getattr(data_mod, "TRAIN_DATA", None) or getattr(data_mod, "DATA", None)
    if data is None:
        raise RuntimeError("Expected TRAIN_DATA or DATA in train_ner_data_fixed.py")
    return data

def sanitize_samples(nlp, raw):
    clean=[]; bad=0
    for text, ann in raw:
        ents = ann.get("entities", [])
        doc = nlp.make_doc(text)
        spans=[]
        for s,e,label in ents:
            span = doc.char_span(s,e,label=label, alignment_mode="contract")
            if span is not None:
                spans.append((span.start_char, span.end_char, label))
        if len(spans) != len(ents):
            bad+=1; continue
        clean.append((text, {"entities": spans}))
    if bad: print(f"[WARN] Filtered {bad} misaligned samples out of {len(raw)}")
    return clean

def create_nlp():
    try:
        nlp = spacy.load("vi_core_news_lg"); print("[INFO] Loaded 'vi_core_news_lg'")
    except Exception:
        try:
            nlp = spacy.load("vi_core_news_sm"); print("[INFO] Loaded 'vi_core_news_sm'")
        except Exception:
            nlp = spacy.blank("vi"); print("[INFO] Using blank('vi')")
    if "ner" not in nlp.pipe_names:
        ner = nlp.add_pipe("ner", last=True)
    else:
        ner = nlp.get_pipe("ner")
    return nlp, ner

def split_train_dev(data, dev_ratio=0.2, seed=42):
    random.Random(seed).shuffle(data)
    k=max(1,int(len(data)*dev_ratio))
    return data[:-k], data[-k:]

def add_labels(ner, data):
    labels=set()
    for _,ann in data:
        for _,_,L in ann.get("entities", []):
            labels.add(L)
    for L in labels: ner.add_label(L)
    return sorted(labels)

def evaluate(nlp, data):
    ex=[Example.from_dict(nlp.make_doc(t), a) for t,a in data]
    scores=nlp.evaluate(ex)
    return {k: float(scores.get(k,0.0)) for k in ("ents_p","ents_r","ents_f")}

def train():
    raw=load_data()
    base=spacy.blank("vi")
    raw=sanitize_samples(base, raw)
    nlp, ner = create_nlp()
    labels = add_labels(ner, raw)
    print("[INFO] Labels:", labels)
    train_data, dev_data = split_train_dev(raw, dev_ratio=0.2, seed=42)
    print(f"[INFO] Train={len(train_data)} | Dev={len(dev_data)}")

    other=[p for p in nlp.pipe_names if p!="ner"]
    dropout=float(os.getenv("DROPOUT","0.15")); n_iter=int(os.getenv("EPOCHS","30")); patience=int(os.getenv("PATIENCE","5"))
    with nlp.disable_pipes(*other):
        optimizer=nlp.initialize(get_examples=lambda: [Example.from_dict(nlp.make_doc(t), a) for t,a in train_data])
        best_f=-1.0; bad=0
        for epoch in range(1, n_iter+1):
            random.shuffle(train_data)
            losses={}
            for batch in minibatch(train_data, size=compounding(4.0, 32.0, 1.5)):
                examples=[Example.from_dict(nlp.make_doc(t), a) for t,a in batch]
                nlp.update(examples, drop=dropout, sgd=optimizer, losses=losses)
            dev=evaluate(nlp, dev_data)
            print(f"[EPOCH {epoch:03d}] loss={losses.get('ner',0):.4f}  dev_f1={dev['ents_f']:.4f}  p={dev['ents_p']:.4f} r={dev['ents_r']:.4f}")
            if dev["ents_f"] > best_f + 1e-4:
                best_f=dev["ents_f"]; bad=0; nlp.to_disk(OUT_DIR)
            else:
                bad+=1
                if bad>=patience:
                    print("[EARLY STOP] No improvement."); break
    LABELS_PATH.write_text(json.dumps({"labels": labels}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("[DONE] Saved best model to", OUT_DIR)

if __name__=="__main__":
    train()
