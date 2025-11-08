
# Modular Core for Desktop Assistant

## Files
- `assistant_core_modular.py` — GUI (CustomTkinter) + command queue, gọi NLP & App layers
- `assistant_nlp.py` — NLP (lazy spaCy NER + PhoBERT intent) + rule fallback & helpers
- `assistant_apps.py` — AppManager: alias + app mapping (đọc `apps_index.json`, `alias_map.json`)
- `assistant_logger.py` — Logging xoay vòng
- `apps_index.json` — (tùy chọn) danh sách app → lệnh mở
- `alias_map.json` — (tùy chọn) alias tiếng Việt cho app

## Cài đặt
```bash
pip install customtkinter spacy transformers torch python-dotenv
```
(Không cần spaCy/transformers nếu bạn chỉ test rule-based; hệ thống sẽ tự fallback)

## Chạy
```bash
python assistant_core_modular.py
```

## Tích hợp model của bạn
- spaCy: `improved_ner_vi/final_model`
- PhoBERT: `phobert_intent_model`
Hoặc cấu hình bằng biến môi trường:
```
SPACY_MODEL_DIR=improved_ner_vi/final_model
INTENT_MODEL_DIR=phobert_intent_model
```
