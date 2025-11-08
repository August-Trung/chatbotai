
# Training (Fixed) — PhoBERT Intent & spaCy NER

## Intent (PhoBERT)
Run:
    pip install transformers torch scikit-learn matplotlib
    python train_intent_fixed.py

Outputs in ./phobert_intent_model_fixed:
- confusion_matrix.png
- classification_report.txt
- sample_predictions.txt

## NER (spaCy)
Run:
    pip install spacy
    # optional: python -m spacy download vi_core_news_lg
    python train_ner_fixed.py

Outputs in ./improved_ner_vi/final_model_fixed:
- best model (updated each improvement)
- labels.json

## End-to-End Check
Run:
    python evaluate_after_train.py
