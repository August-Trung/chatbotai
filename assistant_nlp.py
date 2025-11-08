
import os, threading
from typing import Dict, Any, Optional, Tuple
from assistant_logger import setup_logger

log = setup_logger("nlp")

class NLPProcessor:
    def __init__(self):
        self.spacy_model = None
        self.intent_clf = None
        self._lock = threading.Lock()
        self.spacy_path = os.getenv("SPACY_MODEL_DIR", "improved_ner_vi/final_model")
        self.intent_path = os.getenv("INTENT_MODEL_DIR", "phobert_intent_model")

    def ensure_loaded(self) -> Tuple[bool, str]:
        with self._lock:
            if self.spacy_model is not None and self.intent_clf is not None:
                return True, "Đã sẵn sàng."
            try:
                import spacy
                from transformers import pipeline
                self.spacy_model = spacy.load(self.spacy_path)
                self.intent_clf = pipeline("text-classification", model=self.intent_path, tokenizer=self.intent_path)
                log.info("Loaded NLP models: spaCy=%s, intent=%s", self.spacy_path, self.intent_path)
                return True, "Mô hình NLP đã được tải."
            except Exception as e:
                log.warning("NLP loading failed: %s", e)
                self.spacy_model = None
                self.intent_clf = None
                return False, f"Lỗi tải NLP ({e}); sẽ dùng rule-based."

    def analyze(self, text: str) -> Dict[str, Any]:
        text = (text or "").strip()
        result = {"text": text, "intent": None, "entities": []}
        if not text:
            return result
        with self._lock:
            spacy_model = self.spacy_model
            intent = self.intent_clf
        # NER
        if spacy_model:
            try:
                doc = spacy_model(text)
                result["entities"] = [{"text": e.text, "label": e.label_} for e in doc.ents]
            except Exception as e:
                log.warning("spaCy NER error: %s", e)
        # Intent
        if intent:
            try:
                out = intent(text)
                if out and isinstance(out, list) and "label" in out[0]:
                    result["intent"] = out[0]["label"]
                    result["score"] = float(out[0].get("score", 0.0))
            except Exception as e:
                log.warning("Intent clf error: %s", e)

        # Rule fallback
        if not result["intent"]:
            low = text.lower()
            if "mở " in low or low.startswith("mở"):
                result["intent"] = "open_app"
            elif "đóng " in low or low.startswith("đóng"):
                result["intent"] = "close_app"
            elif "mấy giờ" in low or "giờ là" in low or "what time" in low:
                result["intent"] = "get_time"
        return result

    def extract_app(self, analysis: Dict[str, Any]) -> Optional[str]:
        ents = analysis.get("entities") or []
        for e in ents:
            if e.get("label","").lower() in {"app", "application"}:
                return e.get("text")
        txt = (analysis.get("text") or "").lower()
        if "mở " in txt:
            return txt.split("mở ",1)[1]
        if "đóng " in txt:
            return txt.split("đóng ",1)[1]
        return None
