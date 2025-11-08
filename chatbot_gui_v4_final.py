
"""
Chatbot V4_final — Voice + Lazy NLP (spaCy NER + PhoBERT Intent)
-----------------------------------------------------------------
- Tkinter GUI responsive (no blocking on main thread).
- SpeechRecognition mic loop runs in a background thread.
- TTS via pyttsx3.
- Lazy-load NLP models when first needed (or on demand via "Reload NLP" button):
    * spaCy NER from "improved_ner_vi/final_model"
    * PhoBERT intent classifier from "phobert_intent_model"
- Safe fallbacks if models are missing.
- Status/logging for easy debugging.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
import threading
import queue
import time
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

# ---- Optional: read .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# ---- Optional deps (app still runs if missing; will show friendly hints)
try:
    import speech_recognition as sr
except Exception:
    sr = None

try:
    import pyttsx3
except Exception:
    pyttsx3 = None

# transformers & spacy are imported lazily inside the NLP loader

# ========== Logging setup ==========
LOG_PATH = Path("chatbot.log")
logger = logging.getLogger("chatbot")
logger.setLevel(logging.INFO)
_fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
_h1 = logging.StreamHandler()
_h1.setFormatter(_fmt)
logger.addHandler(_h1)
try:
    _h2 = RotatingFileHandler(LOG_PATH, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    _h2.setFormatter(_fmt)
    logger.addHandler(_h2)
except Exception:
    pass

# ========== NLP Loader (lazy) ==========
class NLPLoader:
    def __init__(self, app_log=logger):
        self.log = app_log
        self.spacy_model = None
        self.intent_classifier = None
        self.spacy_model_path = os.getenv("SPACY_MODEL_DIR", "improved_ner_vi/final_model")
        self.intent_model_path = os.getenv("INTENT_MODEL_DIR", "phobert_intent_model")
        self._lock = threading.Lock()

    def _load_spacy(self):
        import spacy  # local import
        self.spacy_model = spacy.load(self.spacy_model_path)
        return self.spacy_model

    def _load_intent_pipeline(self):
        from transformers import pipeline  # local import
        self.intent_classifier = pipeline(
            "text-classification",
            model=self.intent_model_path,
            tokenizer=self.intent_model_path
        )
        return self.intent_classifier

    def ensure_loaded(self):
        with self._lock:
            if self.spacy_model is None or self.intent_classifier is None:
                self.log.info("Attempting to load NLP models...")
                try:
                    self._load_spacy()
                    self._load_intent_pipeline()
                    self.log.info("NLP models loaded successfully")
                    return True, "Mô hình NLP đã được tải."
                except Exception as e:
                    self.log.error(f"Error loading NLP models: {e}")
                    # reset both to None to keep consistent state
                    self.spacy_model = None
                    self.intent_classifier = None
                    return False, f"Lỗi tải mô hình NLP: {e}. Chuyển sang chế độ từ khóa."

    def unload(self):
        with self._lock:
            self.spacy_model = None
            self.intent_classifier = None

    # -- Inference helpers --
    def analyze(self, text: str):
        """Run NER + Intent if available. Return dict with optional intent, entities, and text."""
        with self._lock:
            nlp = self.spacy_model
            ic = self.intent_classifier
        result = {"intent": None, "entities": [], "text": text}
        if nlp:
            try:
                doc = nlp(text)
                ents = []
                for e in doc.ents:
                    ents.append({"text": e.text, "label": e.label_})
                result["entities"] = ents
            except Exception as e:
                self.log.warning(f"spaCy NER error: {e}")
        if ic:
            try:
                out = ic(text)
                # transformers pipeline returns list of dicts [{'label': '...', 'score': 0.98}]
                if out and isinstance(out, list) and "label" in out[0]:
                    result["intent"] = out[0]["label"]
                    result["intent_score"] = float(out[0].get("score", 0.0))
            except Exception as e:
                self.log.warning(f"Intent pipeline error: {e}")
        return result

# ========== Voice (TTS) ==========
class VoiceEngine:
    def __init__(self):
        self.engine = None
        if pyttsx3:
            try:
                self.engine = pyttsx3.init()
            except Exception as e:
                logger.warning("pyttsx3 init failed: %s", e)

    def say(self, text: str):
        if not text:
            return
        if not self.engine:
            logger.info("[TTS disabled] %s", text)
            return
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            logger.error("TTS error: %s", e)

# ========== STT background worker ==========
class SRWorker(threading.Thread):
    def __init__(self, out_q: queue.Queue, stop_event: threading.Event, language="vi-VN"):
        super().__init__(daemon=True)
        self.out_q = out_q
        self.stop_event = stop_event
        self.language = language
        self.recognizer = sr.Recognizer() if sr else None

    def run(self):
        if not self.recognizer or not sr:
            self.out_q.put(("error", "Thiếu SpeechRecognition hoặc không khởi tạo được recognizer"))
            return
        self.recognizer.energy_threshold = 300
        self.recognizer.pause_threshold = 0.6
        try:
            with sr.Microphone() as mic:
                try:
                    self.recognizer.adjust_for_ambient_noise(mic, duration=0.5)
                except Exception as e:
                    logger.info("adjust_for_ambient_noise skipped: %s", e)
                while not self.stop_event.is_set():
                    try:
                        audio = self.recognizer.listen(mic, timeout=5, phrase_time_limit=10)
                        try:
                            text = self.recognizer.recognize_google(audio, language=self.language)
                        except sr.UnknownValueError:
                            text = ""
                        except Exception as e:
                            logger.warning("recognize_google error: %s", e)
                            text = ""
                        self.out_q.put(("transcript", text))
                    except sr.WaitTimeoutError:
                        continue
                    except Exception as e:
                        self.out_q.put(("error", f"Lỗi STT: {e}"))
                        time.sleep(0.3)
        except Exception as e:
            self.out_q.put(("error", f"Lỗi micro: {e}"))

# ========== Rule-based fallback ==========
def rule_based_reply(text: str) -> str:
    t = (text or "").lower().strip()
    if not t:
        return "Mình chưa nghe rõ, bạn nói lại giúp mình nhé."
    if any(k in t for k in ["mấy giờ", "giờ là", "what time"]):
        import datetime as dt
        now = dt.datetime.now()
        return f"Bây giờ là {now:%H:%M} ngày {now:%d/%m/%Y}."
    if t.startswith(("mở ", "open ")):
        app = t.split(" ", 1)[1] if " " in t else ""
        return f"(Demo) Sẽ mở: {app}. (Bạn có thể nối hành động thật sau.)"
    if any(k in t for k in ["tìm ", "search ", "google "]):
        q = t.split(" ", 1)[1] if " " in t else t
        return f"(Demo) Tìm kiếm: {q}"
    return f"Bạn vừa nói: {text}"

# ========== GUI App ==========
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Chatbot V4_final — Voice + NER/Intent (lazy load)")
        self.geometry("960x620")
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except Exception:
            pass

        # Widgets
        self.txt = tk.Text(self, wrap="word", state="disabled")
        self.txt.pack(fill="both", expand=True, padx=8, pady=8)

        bottom = ttk.Frame(self)
        bottom.pack(fill="x", padx=8, pady=8)

        self.btn_listen = ttk.Button(bottom, text="Start Listening", command=self.toggle_listen)
        self.btn_listen.pack(side="left")

        ttk.Label(bottom, text="STT lang:").pack(side="left", padx=(12,4))
        self.lang_var = tk.StringVar(value=os.getenv("STT_LANGUAGE", "vi-VN"))
        ttk.Entry(bottom, textvariable=self.lang_var, width=10).pack(side="left")

        ttk.Button(bottom, text="Reload NLP", command=self.reload_nlp).pack(side="left", padx=10)

        self.status = tk.StringVar(value="Idle")
        ttk.Label(bottom, textvariable=self.status).pack(side="right")

        entry_frame = ttk.Frame(self)
        entry_frame.pack(fill="x", padx=8, pady=(0,8))
        self.entry = ttk.Entry(entry_frame)
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.bind("<Return>", self.on_text_enter)
        ttk.Button(entry_frame, text="Send", command=self.on_text_button).pack(side="left", padx=6)

        # Engines
        self.voice = VoiceEngine()
        self.out_q = queue.Queue()
        self.stop_event = threading.Event()
        self.worker = None
        self.nlp = NLPLoader(logger)

        # Start queue polling
        self.after(50, self._poll_queue)

        # Dependency hints
        if sr is None:
            self._log("[Cảnh báo] Thiếu SpeechRecognition. Cài: pip install SpeechRecognition pyaudio")
        if pyttsx3 is None:
            self._log("[Cảnh báo] Thiếu pyttsx3 (TTS). Cài: pip install pyttsx3")

    def _log(self, msg: str):
        logger.info(msg)
        self.txt.configure(state="normal")
        self.txt.insert("end", msg + "\n")
        self.txt.see("end")
        self.txt.configure(state="disabled")

    # --- NLP helpers ---
    def reload_nlp(self):
        self.nlp.unload()
        ok, message = self.nlp.ensure_loaded()
        self._log("Bot: " + (message or ("Đã tải lại NLP" if ok else "Không thể tải NLP")))

    def _ensure_nlp(self):
        res = self.nlp.ensure_loaded()
        if not res:
            return False, "Không thể tải mô hình NLP."
        ok, msg = res
        if ok and msg:
            self._log("Bot: " + msg)
        elif not ok and msg:
            self._log("Bot: " + msg)
        return ok, msg

    def _respond_with_nlp(self, text: str) -> str:
        ok, _ = self._ensure_nlp()
        if ok:
            analysis = self.nlp.analyze(text)
            intent = analysis.get("intent")
            ents = analysis.get("entities") or []
            if intent:
                # Basic demo mapping — you can extend with real action handlers
                if intent.lower() in {"get_time", "time"}:
                    import datetime as dt
                    now = dt.datetime.now()
                    return f"Bây giờ là {now:%H:%M} ngày {now:%d/%m/%Y}."
                if intent.lower() in {"open_app", "open"}:
                    # Look for entity 'app' if your NER uses that label
                    app_name = ""
                    for e in ents:
                        if e.get("label","").lower() in {"app","application"}:
                            app_name = e.get("text","")
                            break
                    if not app_name:
                        # fallback from text for demo
                        parts = text.split(" ", 1)
                        app_name = parts[1] if len(parts) > 1 else ""
                    return f"(NLP) Sẽ mở: {app_name} (demo)."
                if intent.lower() in {"search", "search_web"}:
                    return f"(NLP) Tìm: {text}"
                # Fallback to display analysis
                ents_str = ", ".join([f"{e['text']}[{e['label']}]" for e in ents]) if ents else "không có entity"
                return f"(NLP) Intent={intent}; Entities={ents_str}"
        # If cannot load or no intent → rule-based
        return rule_based_reply(text)

    # --- UI Events ---
    def toggle_listen(self):
        if self.worker and self.worker.is_alive():
            self.stop_event.set()
            self.status.set("Stopping...")
            self.btn_listen.configure(text="Start Listening", state="disabled")
        else:
            self.stop_event.clear()
            lang = self.lang_var.get() or "vi-VN"
            self.worker = SRWorker(self.out_q, self.stop_event, language=lang)
            self.worker.start()
            self.status.set("Listening...")
            self.btn_listen.configure(text="Stop Listening")

    def on_text_enter(self, event):
        text = self.entry.get().strip()
        if text:
            self._log(f"Bạn (gõ): {text}")
            reply = self._respond_with_nlp(text)
            self._log(f"Trợ lý: {reply}")
            self.voice.say(reply)
            self.entry.delete(0, "end")

    def on_text_button(self):
        self.on_text_enter(None)

    # --- Queue polling from STT ---
    def _poll_queue(self):
        try:
            while True:
                topic, payload = self.out_q.get_nowait()
                if topic == "transcript":
                    text = payload or ""
                    self._log(f"Bạn (nói): {text if text else '(không nghe rõ)'}")
                    reply = self._respond_with_nlp(text)
                    self._log(f"Trợ lý: {reply}")
                    self.voice.say(reply)
                elif topic == "error":
                    self._log(f"[Lỗi] {payload}")
                    self.status.set("Error")
        except queue.Empty:
            pass
        if self.worker and not self.worker.is_alive():
            self.btn_listen.configure(text="Start Listening", state="normal")
            self.status.set("Idle")
        self.after(50, self._poll_queue)

    def on_close(self):
        try:
            self.stop_event.set()
        except Exception:
            pass
        self.after(200, self.destroy)

if __name__ == "__main__":
    App().mainloop()
