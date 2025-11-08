
""" Quick end-to-end test for trained intent & NER models. """
from pathlib import Path
import torch, spacy
from transformers import AutoTokenizer, AutoModelForSequenceClassification

INTENT_DIR=Path("./phobert_intent_model_fixed")
NER_DIR=Path("./improved_ner_vi/final_model_fixed")

def main():
    tok=AutoTokenizer.from_pretrained(INTENT_DIR, use_fast=False)
    mdl=AutoModelForSequenceClassification.from_pretrained(INTENT_DIR)
    nlp=spacy.load(NER_DIR)
    samples=["mở zalo","đóng notepad","tìm thời tiết hôm nay","xem thêm kết quả","mấy giờ rồi"]
    for s in samples:
        with torch.no_grad():
            pred=int(mdl(**tok(s, return_tensors='pt', truncation=True, max_length=128)).logits.argmax(dim=-1))
        print(s, "-> intent:", mdl.config.id2label[pred], "; ents:", [(e.text,e.label_) for e in nlp(s).ents])

if __name__=="__main__":
    main()
