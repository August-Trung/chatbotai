# -*- coding: utf-8 -*-
"""
Chatbot V4 (Voice Full) — dựa trên V2 + tích hợp Voice ổn định
--------------------------------------------------------------
- Tái sử dụng toàn bộ UI/logic của V2 (customtkinter, mở app, tìm file, web,...)
- Thêm STT (SpeechRecognition) chạy nền bằng thread + hàng đợi (không treo UI)
- Thêm TTS (pyttsx3) đọc tin nhắn của Bot
- Không sửa mã V2: kế thừa ChatApp của V2 và mở rộng tính năng
"""

import os
import threading
import queue
import time
import logging

# Đọc .env nếu có
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# Import lớp ChatApp gốc từ V2
from assistant_core import ChatApp as CoreChatApp
import tkinter as tk
import customtkinter as ctk

# Optional deps
try:
    import speech_recognition as sr
except Exception:
    sr = None

try:
    import pyttsx3
except Exception:
    pyttsx3 = None

log = logging.getLogger(__name__)
if not log.handlers:
    logging.basicConfig(
        filename="chatbot.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

# ========== Voice (TTS) ==========
class VoiceEngine:
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
                    log.info("adjust_for_ambient_noise skipped: %s", e)
                while not self.stop_event.is_set():
                    try:
                        audio = self.recognizer.listen(mic, timeout=5, phrase_time_limit=10)
                        try:
                            text = self.recognizer.recognize_google(audio, language=self.language)
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
                        time.sleep(0.3)
        except Exception as e:
            self.out_q.put(("error", f"Lỗi micro: {e}"))


# ========== ChatApp kế thừa từ V2 và thêm Voice ==========
class ChatAppVoice(CoreChatApp):
    def __init__(self):
        super().__init__()  # Khởi tạo UI/logic V2
        # Voice engines & queues
        self.voice = VoiceEngine()
        self.stt_q = queue.Queue()
        self.stt_stop = threading.Event()
        self.stt_worker = None
        # Ngôn ngữ STT
        self.stt_lang = os.getenv("STT_LANGUAGE", "vi-VN")

        # Thêm nút bật/tắt nghe giọng nói vào khung đáy của V2
        # V2 đã có bottom_frame với các cột 0..4; ta thêm cột 5
        try:
            self.btn_listen = ctk.CTkButton(
                self.bottom_frame,
                text="🎤 Nghe",
                width=90,
                height=40,
                command=self.toggle_listen,
                font=("Segoe UI", 15, "bold"),
                corner_radius=15,
                fg_color=("#4A90E2", "#1E90FF"),
                hover_color=("#4682B4", "#87CEFA")
            )
            self.btn_listen.grid(row=0, column=5, padx=(10, 15), pady=15)
        except Exception as e:
            log.error(f"Cannot add voice button: {e}", exc_info=True)

        # Bắt đầu vòng poll hàng đợi STT
        self.after(50, self._poll_stt_queue)

    # Gọi TTS mỗi khi Bot nói (ghi đè nhẹ display_message)
    def display_message(self, message, sender="User"):
        super().display_message(message, sender=sender)
        try:
            if sender == "Bot":
                # đọc phần nội dung sau "Bot: " nếu có
                spoken = message
                if spoken.lower().startswith("bot:"):
                    spoken = message.split(":", 1)[1].strip() or message
                self.voice.say(spoken)
        except Exception as e:
            log.warning(f"TTS speak error: {e}")

    # Nút bật/tắt STT
    def toggle_listen(self):
        if self.stt_worker and self.stt_worker.is_alive():
            self.stt_stop.set()
            self.btn_listen.configure(text="🎤 Nghe", state="disabled")
        else:
            if sr is None:
                self.display_message("Bot: Thiếu thư viện SpeechRecognition/pyaudio.", sender="Bot")
                return
            self.stt_stop.clear()
            self.stt_worker = SRWorker(self.stt_q, self.stt_stop, language=self.stt_lang)
            self.stt_worker.start()
            self.display_message("Bot: Đang lắng nghe...", sender="Bot")
            self.btn_listen.configure(text="⏹ Dừng")

    # Poll hàng đợi STT và đẩy vào process_command của V2
    def _poll_stt_queue(self):
        try:
            while True:
                topic, payload = self.stt_q.get_nowait()
                if topic == "transcript":
                    text = payload or ""
                    if text.strip():
                        # Hiển thị người dùng nói + xử lý bằng V2
                        self.display_message(text, sender="User")
                        threading.Thread(target=self.process_command, args=(text,), daemon=True).start()
                    else:
                        self.display_message("Bot: (không nghe rõ)", sender="Bot")
                elif topic == "error":
                    self.display_message(f"Bot: {payload}", sender="Bot")
        except queue.Empty:
            pass

        # Cập nhật trạng thái nút khi dừng
        if self.stt_worker and not self.stt_worker.is_alive():
            self.btn_listen.configure(text="🎤 Nghe", state="normal")

        self.after(80, self._poll_stt_queue)


if __name__ == "__main__":
    app = ChatAppVoice()
    app.mainloop()
