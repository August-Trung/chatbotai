# -*- coding: utf-8 -*-
import os, threading, re
from typing import Dict, Any, Optional, Tuple, List
from assistant_logger import setup_logger
def _canon(s: str) -> str:
    return (s or "").strip().lower()


log = setup_logger("nlp")

# Regex nhận diện file
FILE_EXT = re.compile(
    r"[\\w\\-\\s]+\\.(txt|docx?|xlsx?|pptx?|png|jpg|jpeg|zip|rar|7z|pdf)$", re.I
)


class NLPProcessor:
    def __init__(self):
        self.spacy_model = None
        self.intent_clf = None
        self._lock = threading.Lock()
        self.spacy_path = os.getenv(
            "SPACY_MODEL_DIR", "improved_ner_vi/final_model"
        )
        self.intent_path = os.getenv("INTENT_MODEL_DIR", "phobert_intent_model")

    def ensure_loaded(self) -> Tuple[bool, str]:
        with self._lock:
            if self.spacy_model is not None and self.intent_clf is not None:
                return True, "Đã sẵn sàng."
            try:
                import spacy
                from transformers import pipeline

                self.spacy_model = spacy.load(self.spacy_path)
                self.intent_clf = pipeline(
                    "text-classification",
                    model=self.intent_path,
                    tokenizer=self.intent_path,
                )
                log.info(
                    "Loaded NLP models: spaCy=%s, intent=%s",
                    self.spacy_path,
                    self.intent_path,
                )
                return True, "Mô hình NLP đã được tải."
            except Exception as e:
                log.warning("NLP loading failed: %s", e)
                self.spacy_model = None
                self.intent_clf = None
                return False, f"Lỗi tải NLP ({e}); dùng rule-based."

    def analyze(self, text: str) -> Dict[str, Any]:
        text = (text or "").strip()
        lower = text.lower()
        result = {"text": text, "intent": None, "entities": []}
        if not text:
            return result

        self.ensure_loaded()
        with self._lock:
            spacy_model = self.spacy_model
            intent_model = self.intent_clf

        # --- spaCy NER ---
        ents: List[Dict[str, Any]] = []
        if spacy_model:
            try:
                doc = spacy_model(text)
                ents = [{"text": e.text, "label": e.label_} for e in doc.ents]
            except Exception as e:
                log.warning("spaCy NER error: %s", e)

        # --- Rule nhận diện app/file ---
        if not any(e["label"] == "APP" for e in ents):
            if re.search(r"^(mở|bật|chạy)\s", lower):
                app_name = re.sub(r"^(mở|bật|chạy)\s+", "", lower).strip()
                if app_name:
                    ents.append({"text": _canon(app_name), "label": "APP"})
        if not any(e["label"] == "FILE" for e in ents):
            f = FILE_EXT.search(text)
            if f:
                ents.append({"text": f.group(0), "label": "FILE"})

        result["entities"] = ents

        # --- Intent model ---
        intent_out = None
        if intent_model:
            try:
                out = intent_model(text)
                if out and isinstance(out, list):
                    intent_out = {
                        "label": out[0]["label"],
                        "score": float(out[0].get("score", 0.0)),
                    }
            except Exception as e:
                log.warning("Intent clf error: %s", e)

        # --- Fallback override: nếu có ACTION mở/tắt thì chắc chắn là app ---
        if "mở" in lower or "bật" in lower:
            intent_out = {"label": "open_app", "score": 0.99}
        elif "đóng" in lower or "tắt" in lower:
            intent_out = {"label": "close_app", "score": 0.99}
        elif "tìm" in lower or "file" in lower:
            intent_out = {"label": "find_file", "score": 0.9}
        elif "thời tiết" in lower:
            intent_out = {"label": "get_weather", "score": 0.9}
        elif "mấy giờ" in lower or "giờ là" in lower:
            intent_out = {"label": "get_time", "score": 0.9}
        else:
            if not intent_out:
                intent_out = {"label": "chitchat", "score": 0.5}

        result["intent"] = intent_out["label"]
        result["score"] = intent_out["score"]
        return result

    def extract_app(self, analysis: Dict[str, Any]) -> Optional[str]:
        ents = analysis.get("entities") or []
        for e in ents:
            if e.get("label", "").lower() == "app":
                return e.get("text")
        txt = (analysis.get("text") or "").lower()
        if "mở " in txt:
            return txt.split("mở ", 1)[1]
        if "đóng " in txt:
            return txt.split("đóng ", 1)[1]
        return None
