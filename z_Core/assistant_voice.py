# -*- coding: utf-8 -*-
"""
assistant_voice.py

Reusable voice core (TTS + STT worker) extracted from chatbot GUI.

Provides:
- VoiceEngine: thin wrapper around `pyttsx3` for TTS (graceful no-op if missing)
- SRWorker: background thread using `speech_recognition` to produce transcripts

The classes are UI-agnostic and use queues/callbacks so they can be integrated
into different frontends (eg. `assistant_core_modular.py`).
"""
import threading
import queue
import logging

try:
    import pyttsx3
except Exception:
    pyttsx3 = None

try:
    import speech_recognition as sr
except Exception:
    sr = None

log = logging.getLogger(__name__)


class VoiceEngine:
    """Thin TTS wrapper. If `pyttsx3` is not available, it becomes a logger no-op."""

    def __init__(self):
        self.engine = None
        if pyttsx3:
            try:
                self.engine = pyttsx3.init()
            except Exception as e:
                log.warning("pyttsx3 init failed: %s", e)

    def say(self, text: str):
        if not text:
            return
        if not self.engine:
            log.info("[TTS disabled] %s", text)
            return
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            log.error("TTS error: %s", e)


class VoiceController:
    """Higher-level controller that selects a Vietnamese voice if available
    and exposes a `say(text, lang='vi')` convenience method.

    Behavior:
    - If `pyttsx3` is missing, methods are no-ops and logged.
    - Attempts to pick a voice whose name/lang contains 'vi' or 'vietnam' or 'vietnamese'.
    - Falls back to default voice if no Vietnamese-specific voice found.
    """

    def __init__(self):
        self._engine = None
        self._has_engine = False
        try:
            if pyttsx3:
                self._engine = pyttsx3.init()
                self._has_engine = True
                # Try to select a Vietnamese voice if present
                try:
                    voices = self._engine.getProperty("voices") or []
                    vi_candidate = None
                    for v in voices:
                        name = (getattr(v, "name", "") or "").lower()
                        lang = ""
                        if hasattr(v, "languages"):
                            try:
                                lang = " ".join([str(x).lower() for x in v.languages])
                            except Exception:
                                lang = ""
                        combined = f"{name} {lang}"
                        if (
                            "vi" in combined
                            or "vietnam" in combined
                            or "vietnamese" in combined
                        ):
                            vi_candidate = v
                            break
                    if vi_candidate:
                        try:
                            self._engine.setProperty("voice", vi_candidate.id)
                            log.info(
                                "Selected Vietnamese voice: %s",
                                getattr(vi_candidate, "name", vi_candidate.id),
                            )
                        except Exception as e:
                            log.info("Could not set Vietnamese voice: %s", e)
                except Exception as e:
                    log.info("Voice enumeration skipped: %s", e)
        except Exception as e:
            log.warning("pyttsx3 init failed (VoiceController): %s", e)
            self._engine = None
            self._has_engine = False

    def say(self, text: str, lang: str = "vi"):
        """Speak the provided text. If Vietnamese voices are not available, still try default TTS.
        The `lang` parameter is reserved for future extension (e.g., switching engines).
        """
        if not text:
            return
        if not self._has_engine:
            log.info("[TTS disabled] %s", text)
            return
        try:
            self._engine.say(text)
            self._engine.runAndWait()
        except Exception as e:
            log.error("TTS speak failed: %s", e)


__all__ = ["VoiceEngine", "SRWorker", "VoiceController"]


class SRWorker(threading.Thread):
    """Background STT worker that pushes results to an output queue.

    Args:
        out_q (queue.Queue): queue to put tuples like (topic, payload) where
            topic == 'transcript' or 'error'.
        stop_event (threading.Event): event to request worker stop.
        language (str): language for recognizer (default 'vi-VN').
    """

    def __init__(
        self, out_q: queue.Queue, stop_event: threading.Event, language="vi-VN"
    ):
        super().__init__(daemon=True)
        self.out_q = out_q
        self.stop_event = stop_event
        self.language = language
        self.recognizer = sr.Recognizer() if sr else None

    def run(self):
        if not self.recognizer or not sr:
            self.out_q.put(
                ("error", "Thiếu SpeechRecognition hoặc không khởi tạo được recognizer")
            )
            return
        # sensible defaults; allow caller to tweak if needed by subclassing
        self.recognizer.energy_threshold = 300
        self.recognizer.pause_threshold = 0.6
        try:
            with sr.Microphone() as mic:
                try:
                    self.recognizer.adjust_for_ambient_noise(mic, duration=0.5)
                except Exception as e:
                    log.info("adjust_for_ambient_noise skipped: %s", e)
                while not self.stop_event.is_set():
                    try:
                        audio = self.recognizer.listen(
                            mic, timeout=5, phrase_time_limit=10
                        )
                        try:
                            text = self.recognizer.recognize_google(
                                audio, language=self.language
                            )
                        except sr.UnknownValueError:
                            text = ""
                        except Exception as e:
                            log.warning("recognize_google error: %s", e)
                            text = ""
                        self.out_q.put(("transcript", text))
                    except sr.WaitTimeoutError:
                        continue
                    except Exception as e:
                        self.out_q.put(("error", f"Lỗi STT: {e}"))
                        # avoid tight-loop on repeated errors
                        threading.Event().wait(0.3)
        except Exception as e:
            self.out_q.put(("error", f"Lỗi micro: {e}"))


__all__ = ["VoiceEngine", "SRWorker"]
