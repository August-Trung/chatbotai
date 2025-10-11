# -*- coding: utf-8 -*-
import customtkinter as ctk
import tkinter as tk
import subprocess
import os
import platform
import webbrowser
import urllib.parse
import threading
import time
import fnmatch
import queue
import logging
from PIL import Image, ImageTk
from customtkinter import CTkImage
import spacy
from underthesea import word_tokenize
from transformers import pipeline

# +++ IMPORTS FOR STT/TTS +++
import speech_recognition as sr
from gtts import gTTS
from playsound import playsound # Ensure you have playsound==1.2.2 installed
# +++++++++++++++++++++++++++++

# --- Cài đặt logging ---
logging.basicConfig(
    filename="chatbot.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)

# --- Cài đặt Giao diện ---
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

APP_MAPPINGS = {
    "notepad": {"open_cmd": ["notepad.exe"], "process_name": "notepad.exe"},
    "excel": {"open_cmd": ["start", "excel.exe"], "process_name": "excel.exe"},
    "word": {"open_cmd": ["start", "winword.exe"], "process_name": "winword.exe"},
    "edge": {"open_cmd": ["start", "msedge"], "process_name": "msedge.exe"},
    "chrome": {"open_cmd": ["start", "chrome"], "process_name": "chrome.exe"},
    "firefox": {"open_cmd": ["start", "firefox"], "process_name": "firefox.exe"},
    "cmd": {"open_cmd": ["start", "cmd.exe"] if platform.system() == "Windows" else ["gnome-terminal"], "process_name": "cmd.exe"},
    "terminal": {"open_cmd": ["start", "wt.exe"] if platform.system() == "Windows" else ["gnome-terminal"], "process_name": "WindowsTerminal.exe" if platform.system() == "Windows" else "gnome-terminal-"},
    "calculator": {"open_cmd": ["calc.exe"], "process_name": "CalculatorApp.exe"},
    "explorer": {"open_cmd": ["explorer.exe"], "process_name": "explorer.exe"},
    "google": {"open_cmd": ["start", "chrome", "https://www.google.com"], "process_name": "chrome.exe", "url": "https://www.google.com"},
    "youtube": {"open_cmd": ["start", "chrome", "https://www.youtube.com"], "process_name": "chrome.exe", "url": "https://www.youtube.com"}, # Note: youtube.com/0 is unusual, consider youtube.com/
    "facebook": {"open_cmd": ["start", "chrome", "https://www.facebook.com"], "process_name": "chrome.exe", "url": "https://www.facebook.com"},
    "gemini": {"open_cmd": ["start", "chrome", "https://gemini.google.com/app"], "process_name": "chrome.exe", "url": "https://gemini.google.com/app"},
    "chatgpt": {"open_cmd": ["start", "chrome", "https://chatgpt.com/"], "process_name": "chrome.exe", "url": "https://chatgpt.com/"},
    "claude": {"open_cmd": ["start", "chrome", "https://claude.ai/"], "process_name": "msedge.exe", "url": "https://claude.ai/"}, # Consider if default browser or specific one for claude
}

ALIAS_MAP = {
    "note": "notepad", "me": "edge", "gg": "google", "ytb": "youtube", "yt": "youtube",
    "cal": "calculator", "exp": "explorer", "fb": "facebook", "face": "facebook",
    "gem": "gemini", "gemini": "gemini", "gpt": "chatgpt", "claude": "claude", "cai": "claude"
}

FILE_TYPE_EXTENSIONS = {
    "excel": (".xlsx", ".xls", ".xlsm", ".xlsb", ".csv"), "xls": (".xlsx", ".xls", ".xlsm", ".xlsb", ".csv"),
    "xlsx": (".xlsx", ".xls", ".xlsm", ".xlsb", ".csv"), "word": (".docx", ".doc", ".rtf"),
    "doc": (".docx", ".doc", ".rtf"), "docx": (".docx", ".doc", ".rtf"),
    "powerpoint": (".pptx", ".ppt"), "ppt": (".pptx", ".ppt"), "pptx": (".pptx", ".ppt"),
    "pdf": (".pdf",), "ảnh": (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp", ".heic", ".jfif"),
    "anh": (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp", ".heic", ".jfif"),
    "jpg": (".jpg", ".jpeg", ".jfif"), "png": (".png",), "video": (".mp4", ".avi", ".mov", ".wmv", ".mkv", ".flv", ".webm"),
    "mp4": (".mp4", ".mov", ".avi", ".wmv", ".mkv"), "nhạc": (".mp3", ".wav", ".aac", ".flac", ".m4a", ".ogg"),
    "nhac": (".mp3", ".wav", ".aac", ".flac", ".m4a", ".ogg"), "mp3": (".mp3", ".m4a", ".aac"),
    "văn bản": (".txt", ".log", ".md"), "van ban": (".txt", ".log", ".md"), "text": (".txt", ".log", ".md"),
    "txt": (".txt",), "nén": (".zip", ".rar", ".7z", ".tar", ".gz"), "nen": (".zip", ".rar", ".7z", ".tar", ".gz"),
    "zip": (".zip",), "rar": (".rar",),
}

WEBSITE_ALIASES = {"google", "youtube", "facebook", "gg", "ytb", "yt", "fb", "face", "gem", "gemini", "gpt", "chatgpt", "claude", "cai"}

KW_BASE_OPEN = ("mở", "khởi động")
KW_BASE_CLOSE = ("đóng", "tắt")
KW_BASE_WEB_SEARCH = ("truy cập", "vào web", "mở web", "mở trang", "tìm kiếm", "search", "tìm", "vào", "tìm nhạc", "tìm bài hát")
KW_BASE_FIND_FILE = ("tìm file", "kiếm file", "tìm tập tin", "kiếm tập tin")
KW_BASE_SHOW_MORE = ("hiển thị thêm", "xem thêm", "thêm kết quả", "show more", "thêm")

KW_SPACED_OPEN = tuple(kw + " " for kw in KW_BASE_OPEN)
KW_SPACED_CLOSE = tuple(kw + " " for kw in KW_BASE_CLOSE)
KW_SPACED_WEB_SEARCH = tuple(kw + " " for kw in KW_BASE_WEB_SEARCH)
KW_SPACED_FIND_FILE = tuple(kw + " " for kw in KW_BASE_FIND_FILE)

LOCATION_PREPOSITIONS = (" trong thư mục ", " tại thư mục ", " ở thư mục ", " trên ổ ", " trong ổ ", " tại ổ ", " ở ổ ", " trên ", " trong ", " ở ", " tại ")
BROWSER_PREPOSITIONS = (" trong ", " bằng ", " trên ")

LOCATION_MAP = {}
BROWSER_APPS = {"edge", "chrome", "firefox"}
YOUTUBE_ALIASES = {"youtube", "ytb", "yt"}

class ChatApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Trợ lý AI Desktop - V7.3.1 (NLP + Voice)")
        try:
            # Attempt to load icon, ensure icon.png is in the same directory or provide full path
            # self.iconphoto(True, tk.PhotoImage(file="icon.png")) # tk.PhotoImage might not work well with ctk
            # For CTkImage:
            # icon_image = CTkImage(Image.open("icon.png"))
            # self.iconphoto(True, icon_image) # This might also be tricky with CTk
            # Simplest cross-platform way for window icon:
            if os.path.exists("icon.ico"): # For windows .ico
                 self.iconbitmap("icon.ico")
            elif os.path.exists("icon.png"): # For some systems, .png might work with Tkinter's PhotoImage
                 self.iconphoto(True, tk.PhotoImage(file="icon.png"))

        except Exception as e:
            log.error(f"Error setting icon: {e}")
        self.minsize(700, 550) # Increased minsize slightly for new button

        # Biến trạng thái
        self.nlp = None
        self.intent_classifier = None
        self.last_search_results = []
        self.last_search_display_index = 0
        self.display_limit = 15
        self.command_queue = queue.Queue()
        self.message_widgets = []
        self.max_messages = 100
        
        self.geometry("800x650")
        # *** FIX: Initialize _current_theme BEFORE use ***
        self._current_theme = ctk.get_appearance_mode() 
        
        self.message_history = []
        self.history_index = 0
        self.nlp_cache = {}
        self.intent_cache = {}
        self.find_file_cancel = threading.Event()
        self.is_windows = platform.system() == "Windows"
        self._initialize_location_map() # Initialize after _current_theme if it uses any theme dependent things (it doesn't here)

        # +++ STT/TTS State +++
        self.is_recognizing_speech = False
        # +++++++++++++++++++++

        # Cấu hình layout chính
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        # Khung hiển thị chat
        self.chat_display_frame = ctk.CTkScrollableFrame(
            self, fg_color=("gray92", "gray18"), border_width=0, corner_radius=15
        )
        self.chat_display_frame.grid(row=0, column=0, padx=15, pady=(15, 10), sticky="nsew")
        self.chat_display_frame.grid_columnconfigure(0, weight=1)

        # Khung dưới cùng
        self.bottom_frame = ctk.CTkFrame(
            self, height=75, corner_radius=0, fg_color="transparent", border_width=1,
            border_color=("gray80", "gray25")
        )
        self.bottom_frame.grid(row=1, column=0, padx=0, pady=0, sticky="ew")
        # Adjusted column configuration for new Mic Button
        self.bottom_frame.grid_columnconfigure(0, weight=0)  # Theme button
        self.bottom_frame.grid_columnconfigure(1, weight=0)  # Mic button
        self.bottom_frame.grid_columnconfigure(2, weight=1)  # Entry message
        self.bottom_frame.grid_columnconfigure(3, weight=0)  # Send button
        self.bottom_frame.grid_columnconfigure(4, weight=0)  # Show more button
        self.bottom_frame.grid_columnconfigure(5, weight=0)  # Clear history button

        # Các nút và ô nhập
        initial_text_color = ("#333333", "#FFFFFF")
        initial_fg_color = ("#F0F0F0", "#2C2C2E")

        self.theme_button = ctk.CTkButton(
            self.bottom_frame,
            text="💡" if self._current_theme == "Dark" else "🌙",
            width=40, height=40, command=self.toggle_theme, font=("Segoe UI Emoji", 18),
            text_color=initial_text_color[0] if self._current_theme == "Light" else initial_text_color[1],
            fg_color=initial_fg_color[0] if self._current_theme == "Light" else initial_fg_color[1],
            hover_color=("#4A90E2", "#E5E5E5"), corner_radius=10
        )
        self.theme_button.grid(row=0, column=0, padx=(15, 5), pady=15)

        # +++ Microphone Button +++
        self.mic_button = ctk.CTkButton(
            self.bottom_frame, text="🎤", width=40, height=40,
            command=self.start_voice_input_thread, font=("Segoe UI Emoji", 18),
            text_color=initial_text_color[0] if self._current_theme == "Light" else initial_text_color[1],
            fg_color=initial_fg_color[0] if self._current_theme == "Light" else initial_fg_color[1],
            hover_color=("#4A90E2", "#E5E5E5"), corner_radius=10
        )
        self.mic_button.grid(row=0, column=1, padx=(0, 10), pady=15)
        # +++++++++++++++++++++++++

        self.entry_message = ctk.CTkEntry(
            self.bottom_frame, placeholder_text="Nhập tin nhắn hoặc nhấn 🎤",
            font=("Segoe UI", 15), height=40, border_width=1,
            fg_color=("white", "gray25"), corner_radius=15,
            border_color=("#D3D3D3", "#555555")
        )
        self.entry_message.grid(row=0, column=2, padx=0, pady=15, sticky="ew")
        self.entry_message.bind("<Return>", self.send_message_event)
        self.entry_message.bind("<Up>", self.recall_previous_message)
        self.entry_message.bind("<Down>", self.recall_next_message)
        self.entry_message.bind("<Button-3>", self.paste_on_right_click)

        self.send_button = ctk.CTkButton(
            self.bottom_frame, text="Gửi", width=80, height=40, command=self.send_message_event,
            font=("Segoe UI", 15, "bold"), corner_radius=15,
            fg_color=("#4A90E2", "#1E90FF"), hover_color=("#4682B4", "#87CEFA")
        )
        self.send_button.grid(row=0, column=3, padx=(10, 5), pady=15)

        self.show_more_button = ctk.CTkButton(
            self.bottom_frame, text="Xem thêm", width=100, height=40,
            command=self._on_show_more_button_click, font=("Segoe UI", 15, "bold"),
            text_color_disabled="gray60", corner_radius=15, fg_color=("#4A90E2", "#1E90FF")
        )
        self.show_more_button_grid_info = {"row": 0, "column": 4, "padx": (0, 5), "pady": 15, "sticky": "e"}
        self.show_more_button.grid_remove()

        self.clear_button = ctk.CTkButton( # Placed relative to entry_message
            self.bottom_frame, text="✖", width=30, height=30, font=("Segoe UI", 12),
            corner_radius=0, command=lambda: self.entry_message.delete(0, tk.END),
            fg_color=("white", "gray25"), text_color=("gray50", "gray60"),
        )
        self.clear_button.grid(row=0, column=2, padx=(0, 10), pady=15, sticky="e") # Overlaps right side of entry

        self.clear_history_button = ctk.CTkButton(
            self.bottom_frame, text="Xóa lịch sử", width=100, height=40, command=self.clear_chat_history,
            font=("Segoe UI", 15, "bold"), corner_radius=15,
            fg_color=("#FF4040", "#FF6666"), hover_color=("#CC3333", "#FF9999")
        )
        self.clear_history_button.grid(row=0, column=5, padx=(0, 15), pady=15)

        self.display_message("Bot: Chào bạn! Giao diện đã được nâng cấp với NLP và giọng nói. Nhấn 🎤 để nói.", sender="Bot", speak_this_message=True)
        self._process_commands_from_queue()

    # +++ TTS Method +++
    def _speak_thread_target(self, text_to_speak):
        try:
            log.info(f"TTS: Attempting to speak: {text_to_speak[:50]}...")
            tts = gTTS(text=text_to_speak, lang='vi', slow=False)
            temp_audio_file = "temp_bot_response.mp3" # Consider placing in a temp directory
            tts.save(temp_audio_file)
            playsound(temp_audio_file) # Ensure playsound==1.2.2 is used if 1.3.0 causes issues
            os.remove(temp_audio_file)
            log.info("TTS: Playback complete.")
        except ConnectionResetError: # Specific error for network issues often seen with gTTS
            log.error("TTS Connection Error: Connection reset by peer. Check internet or gTTS service status.")
            self.after(0, lambda: self.display_message("Bot: Lỗi TTS (mất kết nối).", "Bot", speak_this_message=False))
        except Exception as e:
            log.error(f"TTS Error: {e}", exc_info=True)
            self.after(0, self.display_message, f"Bot: Lỗi TTS ({type(e).__name__}).", "Bot", speak_this_message=False)

    def speak(self, message_text):
        threading.Thread(target=self._speak_thread_target, args=(message_text,), daemon=True).start()
    # ++++++++++++++++++

    # +++ STT Methods +++
    def _recognize_speech_thread_target(self):
        recognizer = sr.Recognizer()
        # You can specify device_index if default microphone is not desired
        # microphone = sr.Microphone(device_index=None) 
        microphone = sr.Microphone()


        self.after(0, self.mic_button.configure, {"text": "🎙️...", "state": "disabled"})
        # Speak "Đang nghe..." only if not already speaking something else critical.
        # For simplicity, let's assume it's okay for now.
        self.after(0, lambda: self.display_message("Bot: Đang nghe...", "Bot", speak_this_message=True))

        try:
            with microphone as source:
                recognizer.pause_threshold = 1.0 # seconds of non-speaking audio before phrase is considered complete
                recognizer.energy_threshold = 400 # default is 300, can adjust
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                log.info("STT: Listening for voice input...")
                try:
                    audio = recognizer.listen(source, timeout=7, phrase_time_limit=10) # timeout: max wait for speech, phrase_time_limit: max speech duration
                except sr.WaitTimeoutError:
                    log.warning("STT: No speech detected within timeout.")
                    self.after(0, self.display_message, "Bot: Không nhận được tín hiệu giọng nói.", "Bot", speak_this_message=True)
                    self.is_recognizing_speech = False # Reset flag
                    self.after(0, self.mic_button.configure, {"text": "🎤", "state": "normal"})
                    return # Exit thread

            log.info("STT: Processing speech...")
            self.after(0, self.display_message, "Bot: Đang nhận dạng...", "Bot", speak_this_message=False) # Don't speak this status
            recognized_text = recognizer.recognize_google(audio, language="vi-VN")
            log.info(f"STT: Recognized: {recognized_text}")

            def update_entry_and_send():
                self.entry_message.delete(0, tk.END)
                self.entry_message.insert(0, recognized_text)
                self.send_message_event()

            self.after(0, update_entry_and_send)

        except sr.UnknownValueError:
            log.warning("STT: Google Web Speech API could not understand audio.")
            self.after(0, lambda: self.display_message("Bot: Xin lỗi, tôi không thể nhận dạng giọng nói của bạn.", "Bot", speak_this_message=True))
        except sr.RequestError as e:
            log.error(f"STT: Could not request results from Google Web Speech API; {e}")
            self.after(0, lambda: self.display_message(f"Bot: Lỗi dịch vụ nhận dạng: {e}. Kiểm tra kết nối mạng.", "Bot", speak_this_message=True))
        except Exception as e:
            log.error(f"STT: An unexpected error occurred: {e}", exc_info=True)
            self.after(0, lambda: self.display_message(f"Bot: Lỗi STT không xác định: {type(e).__name__}.", "Bot", speak_this_message=True))
        finally:
            self.is_recognizing_speech = False # Reset flag in all cases
            self.after(0, self.mic_button.configure, {"text": "🎤", "state": "normal"})

    def start_voice_input_thread(self):
        if not self.is_recognizing_speech:
            self.is_recognizing_speech = True # Set flag immediately
            threading.Thread(target=self._recognize_speech_thread_target, daemon=True).start()
        else:
            log.info("STT: Recognition already in progress.")
            self.display_message("Bot: Đang xử lý yêu cầu giọng nói trước đó...", "Bot", speak_this_message=True)
    # +++++++++++++++++++

    def _load_nlp_models(self):
        if self.nlp is None or self.intent_classifier is None:
            log.info("Attempting to load NLP models...")
            try:
                self.nlp = spacy.load("improved_ner_vi/final_model")
                self.intent_classifier = pipeline(
                    "text-classification",
                    model="phobert_intent_model",
                    tokenizer="phobert_intent_model"
                )
                log.info("NLP models loaded successfully")
                self.display_message("Bot: Mô hình NLP đã được tải.", sender="Bot", speak_this_message=False) # Usually silent
            except Exception as e:
                log.error(f"Error loading NLP models: {e}")
                self.nlp = None
                self.intent_classifier = None
                self.display_message(f"Bot: Lỗi tải mô hình NLP: {e}. Chuyển sang chế độ từ khóa.", sender="Bot", speak_this_message=True)

    def preprocess_vietnamese(self, text):
        try:
            text = text.lower().replace("mđ", "microsoft") # Example shorthand
            return word_tokenize(text, format="text")
        except Exception as e:
            log.error(f"Error in preprocess_vietnamese: {e}")
            return text # Fallback to original text

    def sanitize_input(self, text):
        forbidden_chars = ['&', '|', ';', '`', '$', '>', '<'] # Basic santization
        if any(char in text for char in forbidden_chars):
            log.warning(f"Invalid input detected (forbidden chars): {text}")
            return None
        return text.strip()

    def process_command(self, command):
        command_clean = self.sanitize_input(command)
        if not command_clean:
            self.display_message("Bot: Đầu vào không hợp lệ, vui lòng thử lại.", sender="Bot", speak_this_message=True)
            return

        self._load_nlp_models() # Ensure models are loaded
        if not self.nlp or not self.intent_classifier:
            log.warning("NLP models not available, falling back to keyword logic.")
            self._process_command_fallback(command_clean)
            return

        command_lower = command_clean.lower()
        log.info(f"Processing command with NLP: '{command_clean}'")
        
        # Keyword override check BEFORE NLP for critical commands
        keyword_intent = None
        if any(command_lower.startswith(kw) for kw in KW_SPACED_CLOSE):
            keyword_intent = "close_app"
        elif any(command_lower.startswith(kw) for kw in KW_SPACED_OPEN):
            keyword_intent = "open_app"
        
        if keyword_intent:
             log.info(f"Keyword-based intent override: '{keyword_intent}' detected for command '{command_clean}'")

        # Cache lookup for NLP results
        if command_lower in self.nlp_cache and command_lower in self.intent_cache:
            entities = self.nlp_cache[command_lower]
            intent_data = self.intent_cache[command_lower]
            intent = intent_data['label']
            confidence = intent_data['score']
            log.info(f"Cache hit for '{command_lower}'. Intent: {intent} (Conf: {confidence:.2f}), Entities: {entities}")
        else:
            processed_command = self.preprocess_vietnamese(command_lower)
            doc = self.nlp(processed_command)
            entities = {"app": None, "file": None, "path": None, "query": None}
            extracted_ents = []
            for ent in doc.ents:
                extracted_ents.append((ent.text, ent.label_))
                if ent.label_ == "APP": entities["app"] = ent.text
                elif ent.label_ == "FILE": entities["file"] = ent.text
                elif ent.label_ == "PATH": entities["path"] = ent.text
                elif ent.label_ == "QUERY": entities["query"] = ent.text
            log.info(f"NER results: {extracted_ents}")

            intent_result = self.intent_classifier(command_clean) # Use original case for some models
            intent = intent_result[0]["label"]
            confidence = intent_result[0]["score"]
            log.info(f"Intent classification result: {intent} (Confidence: {confidence:.4f})")

            # Store in cache
            self.nlp_cache[command_lower] = entities
            self.intent_cache[command_lower] = {"label": intent, "score": confidence}
            # Simple cache eviction
            if len(self.nlp_cache) > 500: self.nlp_cache.pop(next(iter(self.nlp_cache)))
            if len(self.intent_cache) > 500: self.intent_cache.pop(next(iter(self.intent_cache)))
        
        # Intent refinement and execution
        final_intent = intent
        if keyword_intent: # Keyword intent takes precedence
            final_intent = keyword_intent
            log.info(f"Overriding NLP intent '{intent}' with keyword intent '{final_intent}'")
        elif confidence < 0.75 and entities.get("app"): # If low confidence but APP found, lean towards open_app
            if intent != "close_app": # Don't override if it's already a close command
                 log.info(f"Low confidence ({confidence:.2f}) in NLP intent '{intent}'. Detected APP: {entities['app']}. Considering 'open_app'.")
                 final_intent = "open_app" # Tentatively set, can be refined by app type below

        # Specific logic for Youtube with "trên youtube"
        is_Youtube_query = False
        if final_intent == "open_website" and entities.get("query"):
            if any(yt_alias in command_lower for yt_alias in YOUTUBE_ALIASES) and \
               any(prep in command_lower for prep in (" trên ", " ở ")):
                is_Youtube_query = True
                log.info("Identified potential Youtube query for open_website intent.")


        executed = False
        response_message = None

        try:
            if final_intent == "close_app":
                app_name_to_close = entities["app"] or self._extract_app_from_command(command_clean, KW_SPACED_CLOSE)
                if app_name_to_close: response_message = self._handle_close_app(app_name_to_close)
                else: response_message = "Bạn muốn đóng ứng dụng nào?"
                executed = True
            elif final_intent == "open_app":
                app_name_to_open = entities["app"] or self._extract_app_from_command(command_clean, KW_SPACED_OPEN)
                if app_name_to_open:
                    # Check if it's actually a website alias mistaken as app
                    canonical_app = ALIAS_MAP.get(app_name_to_open.lower(), app_name_to_open.lower())
                    if canonical_app in WEBSITE_ALIASES and canonical_app not in BROWSER_APPS:
                         log.info(f"App '{app_name_to_open}' is a website alias. Switching to open_website.")
                         self.command_queue.put(("open_website", canonical_app, None))
                         response_message = None # Handled by queue
                    else:
                         response_message = self._handle_open_app(app_name_to_open)
                else: response_message = "Bạn muốn mở ứng dụng nào?"
                executed = True
            elif final_intent == "find_file":
                file_to_find = entities["file"] or self._extract_file_from_command(command_clean)
                path_str = entities["path"]
                search_path = self._parse_complex_location(path_str) if path_str else None
                if file_to_find:
                    self.find_file_cancel.clear()
                    self.display_message("Bot: Đang tìm kiếm file...", sender="Bot", speak_this_message=False)
                    self.command_queue.put(("find_file", file_to_find, [search_path] if search_path else None, path_str or "vị trí mặc định"))
                    response_message = None # Handled by queue
                else: response_message = "Vui lòng cung cấp tên file hoặc mẫu cần tìm."
                executed = True
            elif final_intent == "open_website":
                target_web = entities["query"] or entities["app"] or command_clean # Fallback to whole command for safety
                
                # If it's a browser name itself, treat as open_app
                canonical_target_web = ALIAS_MAP.get(target_web.lower(), target_web.lower())
                if canonical_target_web in BROWSER_APPS:
                    log.info(f"Intent open_website target '{target_web}' is a browser. Switching to open_app.")
                    response_message = self._handle_open_app(canonical_target_web)
                else:
                    self.command_queue.put(("open_website", target_web, None))
                    response_message = None # Handled by queue
                executed = True

            elif final_intent == "show_more":
                response_message, more_available = self._handle_show_more_results()
                self._update_show_more_button(more_available)
                executed = True

            if not executed:
                log.warning(f"NLP processed but no action taken for intent '{final_intent}' and command '{command_clean}'")
                response_message = f"Xin lỗi, tôi chưa hiểu lệnh này (Intent: {final_intent})."

        except Exception as e:
            log.error(f"Error processing NLP command '{command_clean}': {e}", exc_info=True)
            response_message = f"Có lỗi xảy ra khi xử lý lệnh: {e}"

        if response_message:
            self.display_message(f"Bot: {response_message}", sender="Bot", speak_this_message=True)

    def _process_command_fallback(self, command):
        command_lower = command.lower()
        log.info(f"Processing command with fallback logic: '{command}'")
        response = f"Xin lỗi, tôi chưa hiểu rõ lệnh của bạn: '{command}'" # Default response
        executed = False
        speak_response = True # By default, speak fallback responses

        # Helper
        def get_target(cmd_full_lower, keywords_spaced):
            for kw in keywords_spaced:
                if cmd_full_lower.startswith(kw):
                    return command[len(kw):].strip()
            return None

        # Show more (should be handled by NLP, but as a pure fallback)
        if command_lower in KW_BASE_SHOW_MORE or command_lower.startswith("xem thêm") or command_lower.startswith("hiển thị thêm"):
            response, more_available = self._handle_show_more_results()
            self._update_show_more_button(more_available)
            executed = True
        else:
            self._reset_search_state() # Reset if not a show_more command

        # Close app
        if not executed:
            target_close = get_target(command_lower, KW_SPACED_CLOSE)
            if target_close is not None:
                response = self._handle_close_app(target_close)
                executed = True
            elif command_lower in KW_BASE_CLOSE:
                response = "Bạn muốn đóng ứng dụng nào?"
                executed = True
        
        # Find File
        if not executed:
            file_target = get_target(command_lower, KW_SPACED_FIND_FILE)
            if file_target is not None:
                if not file_target: response = "Bạn muốn tìm file tên gì?"
                else:
                    # Basic location parsing for fallback
                    pattern, search_paths, loc_name = file_target, None, "vị trí mặc định"
                    for prep in LOCATION_PREPOSITIONS:
                        if prep in file_target.lower():
                            parts = file_target.lower().rsplit(prep, 1)
                            potential_pattern = file_target[:len(parts[0])].strip() # Preserve case of original pattern
                            potential_loc = parts[1].strip()
                            parsed_loc = self._parse_complex_location(potential_loc)
                            if parsed_loc:
                                pattern = potential_pattern
                                search_paths = [parsed_loc]
                                loc_name = potential_loc
                                break
                    self.find_file_cancel.clear()
                    self.display_message("Bot: Đang tìm kiếm file (fallback)...", sender="Bot", speak_this_message=False)
                    self.command_queue.put(("find_file", pattern, search_paths, loc_name))
                    response = None # Handled by queue
                    speak_response = False
                executed = True
            elif command_lower in KW_BASE_FIND_FILE:
                response = "Bạn muốn tìm file tên gì?"
                executed = True

        # Web Search / Open Website (includes music search as a general web search in fallback)
        if not executed:
            web_target = get_target(command_lower, KW_SPACED_WEB_SEARCH)
            if web_target is not None:
                if not web_target: response = "Bạn muốn tìm kiếm gì hoặc vào web nào?"
                else:
                    self.command_queue.put(("open_website", web_target, None)) # Let queue handler decide if it's URL or search
                    response = None
                    speak_response = False
                executed = True
            elif command_lower in KW_BASE_WEB_SEARCH:
                response = "Bạn muốn tìm kiếm gì hoặc vào web nào?"
                executed = True
        
        # Open App
        if not executed:
            open_target = get_target(command_lower, KW_SPACED_OPEN)
            if open_target is not None:
                if not open_target: response = "Bạn muốn mở ứng dụng nào?"
                else:
                    # Check if it's a website alias
                    canonical_target = ALIAS_MAP.get(open_target.lower(), open_target.lower())
                    if canonical_target in WEBSITE_ALIASES and canonical_target not in BROWSER_APPS:
                        self.command_queue.put(("open_website", canonical_target, None))
                        response = None
                        speak_response = False
                    else:
                        response = self._handle_open_app(open_target)
                executed = True
            elif command_lower in KW_BASE_OPEN:
                response = "Bạn muốn mở ứng dụng/web nào?"
                executed = True

        if not executed:
            log.warning(f"Fallback logic could not understand command: '{command}'")
            # Default response is already set

        if response: # Only display if there's a response string
            self.display_message(f"Bot: {response}", sender="Bot", speak_this_message=speak_response)
    
    def _process_commands_from_queue(self):
        try:
            command_type, *args = self.command_queue.get_nowait()
            log.info(f"Processing command from queue: {command_type}, Args: {args}")

            if command_type == "find_file":
                threading.Thread(target=self._find_file_thread, args=args, daemon=True).start()
            elif command_type == "open_website":
                # Display message before starting thread for better UX
                target_display = args[0][:60] + '...' if len(args[0]) > 60 else args[0]
                self.display_message(f"Bot: Đang xử lý mở web/tìm kiếm: {target_display}", sender="Bot", speak_this_message=False)
                threading.Thread(target=self._handle_open_website_thread, args=args, daemon=True).start()
            
            self.command_queue.task_done()
        except queue.Empty:
            pass # No commands in queue
        except Exception as e:
            log.error(f"Error processing command queue: {e}", exc_info=True)
            self.display_message(f"Bot: Lỗi hàng đợi lệnh: {e}", "Bot", speak_this_message=True)
        
        self.after(100, self._process_commands_from_queue) # Check queue periodically

    def _extract_app_from_command(self, command, relevant_keywords=None):
        command_lower_parts = command.lower().split()
        # Remove keywords if provided
        if relevant_keywords:
            for kw_spaced in relevant_keywords:
                kw_base = kw_spaced.strip()
                if kw_base in command_lower_parts:
                    # Attempt to get part after keyword
                    try:
                        idx = command_lower_parts.index(kw_base)
                        if idx + 1 < len(command_lower_parts):
                            potential_app = command.split()[idx+1] # Get original case
                            # Check if this potential_app is known
                            if ALIAS_MAP.get(potential_app.lower(), potential_app.lower()) in APP_MAPPINGS:
                                return potential_app
                            # If not, it might be part of a longer app name or garbage
                    except ValueError:
                        pass # Keyword not found as a whole word

        # General extraction by checking known apps/aliases
        words = command.split() # Original case
        for i in range(len(words)):
            # Check single word
            word_lower = words[i].lower()
            if ALIAS_MAP.get(word_lower, word_lower) in APP_MAPPINGS: return words[i]
            # Check two words (e.g., "microsoft edge") - not robust, NLP should handle this better
            if i + 1 < len(words):
                two_words = words[i] + " " + words[i+1]
                two_words_lower = two_words.lower()
                if ALIAS_MAP.get(two_words_lower, two_words_lower) in APP_MAPPINGS: return two_words
        
        # Fallback: last word if command is short, or best guess based on remaining parts
        if words: return words[-1] # Simplistic fallback
        return command # Very last resort


    def _extract_file_from_command(self, command):
        command_lower = command.lower()
        # Try to find parts after "tìm file", "kiếm file", etc.
        for kw_spaced in KW_SPACED_FIND_FILE:
            if command_lower.startswith(kw_spaced):
                potential_file_part = command[len(kw_spaced):].strip()
                # Remove location prepositions if present at the end
                for prep in LOCATION_PREPOSITIONS:
                    if potential_file_part.lower().rfind(prep) > 0: # Avoid if prep is at start
                        idx = potential_file_part.lower().rfind(prep)
                        potential_file_part = potential_file_part[:idx].strip()
                        break
                if potential_file_part: return potential_file_part
        
        # Fallback: look for extensions if no keyword found (less reliable)
        words = command.split()
        for word in reversed(words): # Check from end
            if any(word.lower().endswith(ext) for ext_list in FILE_TYPE_EXTENSIONS.values() for ext in ext_list):
                return word # Return the word that seems to have an extension
        
        # Very basic fallback if nothing specific: assume last part after common keywords is filename
        common_keywords = list(KW_BASE_OPEN) + list(KW_BASE_CLOSE) + list(KW_BASE_WEB_SEARCH) + list(KW_BASE_FIND_FILE)
        processed_command = command
        for kw in common_keywords:
            if command.lower().startswith(kw.lower() + " "):
                processed_command = command[len(kw)+1:].strip()
                break
        return processed_command if processed_command != command else command.split(" ")[-1] if " " in command else command


    def _handle_open_app(self, app_name):
        app_name_lower = app_name.lower()
        canonical_name = ALIAS_MAP.get(app_name_lower, app_name_lower)
        log.info(f"Attempting to open app: '{app_name}' (Canonical: '{canonical_name}')")

        if canonical_name in APP_MAPPINGS:
            app_info = APP_MAPPINGS[canonical_name]
            command_to_run = app_info["open_cmd"]
            use_shell = self.is_windows and command_to_run[0] == 'start'
            log.info(f"Executing command: {command_to_run} with shell={use_shell}")
            try:
                # For 'start' on Windows, shell=True is needed.
                # For direct exe calls, shell=False is safer.
                # subprocess.run handles lists of args well with shell=False.
                # If command_to_run is a list like ['start', 'excel.exe'], shell=True is fine.
                # If it's ['notepad.exe'], shell=False is better.
                process = subprocess.Popen(command_to_run, shell=use_shell, 
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                # Optionally, wait for a short period or check return code if needed, but Popen is async
                # stdout, stderr = process.communicate(timeout=5) # Can add timeout
                # if process.returncode != 0 and process.returncode is not None :
                #     log.error(f"Error opening {canonical_name}. Return code: {process.returncode}. Stderr: {stderr.decode(errors='ignore')}")
                #     return f"Lỗi khi mở {canonical_name}. Mã lỗi: {process.returncode}."
                
                log.info(f"Successfully initiated opening of {canonical_name}.")
                return f"Đã gửi yêu cầu mở {canonical_name}."
            except FileNotFoundError:
                log.error(f"Command not found for {canonical_name}: {command_to_run}")
                return f"Lỗi: Lệnh hoặc ứng dụng '{canonical_name}' không tìm thấy."
            except subprocess.TimeoutExpired:
                log.warning(f"Timeout expired when trying to open {canonical_name}.")
                return f"Quá thời gian khi cố gắng mở {canonical_name}."
            except Exception as e:
                log.error(f"Unexpected error opening {canonical_name}: {e}", exc_info=True)
                return f"Lỗi không xác định khi mở {canonical_name}: {e}"
        else:
            log.warning(f"Application not found in APP_MAPPINGS: '{app_name}' (Canonical: '{canonical_name}')")
            return f"Không tìm thấy cấu hình cho ứng dụng: {app_name}"

    def _handle_close_app(self, app_name):
        app_name_lower = app_name.lower()
        canonical_name = ALIAS_MAP.get(app_name_lower, app_name_lower)
        log.info(f"Attempting to close app: '{app_name}' (Canonical: '{canonical_name}')")

        if canonical_name in APP_MAPPINGS and "process_name" in APP_MAPPINGS[canonical_name]:
            process_name = APP_MAPPINGS[canonical_name]["process_name"]
            log.info(f"Target process name: {process_name}")
            try:
                if self.is_windows:
                    # Using taskkill /F /IM process_name
                    # /T to kill child processes if any, though might be too aggressive.
                    command = ["taskkill", "/F", "/IM", process_name]
                    result = subprocess.run(command, shell=False, check=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
                    log.info(f"taskkill stdout: {result.stdout}")
                    if "SUCCESS" in result.stdout.upper(): # Check uppercase for robustness
                        log.info(f"Successfully sent close signal to {process_name}.")
                        return f"Đã gửi yêu cầu đóng {canonical_name}."
                    # taskkill might not say "not found" in stdout for non-existent processes if /F is used,
                    # it might just succeed if no matching process is running.
                    # Check stderr for "not found" if stdout doesn't confirm success.
                    elif "ERROR: The process" in result.stdout and "not found" in result.stdout:
                         log.warning(f"Process {process_name} not found by taskkill (stdout).")
                         return f"Không tìm thấy tiến trình {canonical_name} đang chạy."
                    else: # If not clearly success or not found from stdout.
                        log.warning(f"taskkill for {process_name} - stdout: {result.stdout}, stderr: {result.stderr}")
                        return f"Đã cố gắng đóng {canonical_name}. Kết quả không rõ."

                else: # For Linux/macOS using pkill
                    command = ["pkill", "-f", process_name] # -f matches against full command line
                    subprocess.run(command, shell=False, check=True) # pkill exits with 0 if processes were killed, 1 if not.
                    log.info(f"Successfully sent kill signal to {process_name} (or no process was found).")
                    return f"Đã gửi yêu cầu đóng {canonical_name}." # pkill is less verbose on success
            except FileNotFoundError:
                cmd_name = "taskkill" if self.is_windows else "pkill"
                log.error(f"Close command '{cmd_name}' not found.")
                return f"Lỗi: Lệnh '{cmd_name}' không tìm thấy trên hệ thống."
            except subprocess.CalledProcessError as e:
                stderr_output = e.stderr if hasattr(e, 'stderr') and e.stderr else "Không có thông tin chi tiết."
                stdout_output = e.stdout if hasattr(e, 'stdout') and e.stdout else ""
                log.warning(f"Error closing {canonical_name} (process: {process_name}). CMD: {e.cmd} RC: {e.returncode} Stderr: {stderr_output} Stdout: {stdout_output}")
                if self.is_windows and ("not found" in stderr_output.lower() or "không tìm thấy" in stderr_output.lower()):
                    return f"Không tìm thấy tiến trình {canonical_name} đang chạy."
                elif not self.is_windows and e.returncode == 1: # pkill returns 1 if no process matched
                     return f"Không tìm thấy tiến trình {canonical_name} đang chạy."
                elif "access denied" in stderr_output.lower() or "từ chối truy cập" in stderr_output.lower():
                    log.error(f"Permission denied while trying to close {process_name}.")
                    return f"Lỗi: Không có quyền đóng {canonical_name}."
                else:
                    return f"Lỗi khi đóng {canonical_name}. Chi tiết: {stderr_output[:100]}"
            except Exception as e:
                log.error(f"Unexpected error closing {canonical_name}: {e}", exc_info=True)
                return f"Lỗi không xác định khi đóng {canonical_name}: {e}"
        else:
            log.warning(f"Cannot close app '{app_name}'. No process name defined or app not found.")
            return f"Không tìm thấy thông tin tiến trình để đóng ứng dụng: {app_name}"

    def _handle_open_website_thread(self, target, browser_key=None): # browser_key not actively used with webbrowser.open
        log.info(f"Thread: Handling open website. Target='{target}', BrowserKey='{browser_key}'")
        url_to_open = None
        message_to_user = f"Đang xử lý yêu cầu cho: '{target[:50]}...'" # Default message
        success = False

        try:
            target_lower = target.lower()
            canonical_target = ALIAS_MAP.get(target_lower, target_lower)

            # 1. Check if target is a known website alias with a predefined URL
            if canonical_target in APP_MAPPINGS and 'url' in APP_MAPPINGS[canonical_target]:
                url_to_open = APP_MAPPINGS[canonical_target]['url']
                message_to_user = f"Đang mở trang web '{canonical_target}': {url_to_open}"
                log.info(f"Opening predefined URL for alias '{canonical_target}': {url_to_open}")
            # 2. Check if target is already a full URL
            elif target.startswith("http://") or target.startswith("https://"):
                url_to_open = target
                message_to_user = f"Đang mở URL: {url_to_open}"
                log.info(f"Target is already a URL: {url_to_open}")
            # 3. Check if target is a domain-like string (e.g., "google.com")
            elif '.' in target and ' ' not in target and not target.startswith("www.") and not target.endswith(".com"): # simple check
                url_to_open = "https://" + target # Prepend https
                message_to_user = f"Đang mở tên miền: {url_to_open}"
                log.info(f"Target looks like a domain, prepending https://: {url_to_open}")
            # 4. Otherwise, treat as a search query
            else:
                # Special handling for "tìm nhạc/bài hát X trên youtube"
                is_music_search_on_youtube = False
                search_query_text = target
                if ("tìm nhạc" in target_lower or "tìm bài hát" in target_lower):
                    for yt_alias_token in YOUTUBE_ALIASES: # e.g. "trên yt", "trên youtube"
                        if f" trên {yt_alias_token}" in target_lower:
                            is_music_search_on_youtube = True
                            # Extract actual song title
                            search_query_text = target_lower.split(f" trên {yt_alias_token}")[0]
                            # Remove "tìm nhạc", "tìm bài hát" from the extracted query
                            search_query_text = search_query_text.replace("tìm nhạc", "").replace("tìm bài hát", "").strip()
                            break
                
                if is_music_search_on_youtube and search_query_text:
                    encoded_query = urllib.parse.quote_plus(search_query_text)
                    url_to_open = f"https://www.youtube.com/results?search_query={encoded_query}"
                    message_to_user = f"Đang tìm nhạc '{search_query_text}' trên YouTube..."
                else: # General Google search
                    encoded_query = urllib.parse.quote_plus(target)
                    url_to_open = f"https://www.google.com/search?q={encoded_query}"
                    message_to_user = f"Đang tìm kiếm '{target}' trên Google..."
                log.info(f"Performing search. Query='{target}', URL='{url_to_open}'")

            if url_to_open:
                log.info(f"Attempting to open URL with webbrowser: {url_to_open}")
                opened = webbrowser.open(url_to_open)
                if opened:
                    log.info("webbrowser.open returned True.")
                    # message_to_user is already set based on logic above
                    success = True
                else:
                    # This case is rare, usually means no browser is found or OS blocks it.
                    log.warning("webbrowser.open returned False. Opening might have failed.")
                    message_to_user = f"Không thể mở '{target}'. Trình duyệt không phản hồi hoặc URL không hợp lệ."
                    success = False # Explicitly set
            else:
                message_to_user = f"Không thể xác định URL hoặc hành động cho '{target}'."
                success = False

        except Exception as e:
            log.error(f"Error in _handle_open_website_thread for target '{target}': {e}", exc_info=True)
            message_to_user = f"Lỗi khi mở web/tìm kiếm '{target[:30]}...': {type(e).__name__}"
            success = False
        
        # Always send a final message back to the user via the main thread
        self.after(0, self.display_message, f"Bot: {message_to_user}", "Bot", speak_this_message=success) # Only speak on success

    def _find_file_thread(self, pattern, search_locations, location_name_display):
        log.info(f"Thread: Starting file search. Pattern='{pattern}', Locations='{search_locations}', DisplayName='{location_name_display}'")
        results = []
        search_timed_out = False
        search_cancelled = False
        error_message = None
        processed_files = 0
        max_files_to_scan_per_dir = 10000 # Safety limit to avoid extremely long scans in huge dirs

        try:
            start_time = time.time()
            timeout_seconds = 30 # Search timeout

            actual_dirs_to_search = []
            if search_locations and search_locations[0] is not None : # As it's passed as a list
                actual_dirs_to_search = [loc for loc in search_locations if loc and os.path.isdir(loc)]
                if not actual_dirs_to_search:
                    error_message = f"Thư mục '{location_name_display}' không hợp lệ hoặc không tồn tại."
            else: # Default search locations
                user_home = os.path.expanduser("~")
                default_dirs = [
                    os.path.join(user_home, "Desktop"),
                    os.path.join(user_home, "Documents"),
                    os.path.join(user_home, "Downloads"),
                    os.path.join(user_home, "Pictures"),
                    os.path.join(user_home, "Videos"),
                    os.path.join(user_home, "Music"),
                ]
                if self.is_windows: # Add common drives on Windows
                    for d_letter in "CDEFGHIJKLMNOPQRSTUVWXYZ":
                        drive_path = f"{d_letter}:\\"
                        if os.path.exists(drive_path): default_dirs.append(drive_path)
                
                actual_dirs_to_search = [d for d in default_dirs if os.path.isdir(d)]
                location_name_display = "các vị trí mặc định"
                log.info(f"No specific location, searching default locations: {actual_dirs_to_search}")

            if not actual_dirs_to_search and not error_message:
                 error_message = "Không tìm thấy thư mục nào để tìm kiếm."

            if not error_message:
                search_pattern_os = f"*{pattern}*" if pattern != "*" and not pattern.startswith("*") and not pattern.endswith("*") else pattern
                search_pattern_os = search_pattern_os.lower() # fnmatch is case-insensitive on Win, sensitive on Unix by default. Lowercasing helps consistency.

                for dir_path in actual_dirs_to_search:
                    if search_cancelled or search_timed_out: break
                    log.info(f"Searching in: {dir_path} for pattern: {search_pattern_os}")
                    files_in_current_dir = 0
                    try:
                        for root, _, files in os.walk(dir_path, topdown=True, onerror=lambda e: log.warning(f"os.walk error: {e}")):
                            if search_cancelled or search_timed_out: break
                            if files_in_current_dir > max_files_to_scan_per_dir :
                                log.warning(f"Reached max files scan limit for {dir_path}")
                                break
                            
                            for name in files:
                                if search_cancelled or search_timed_out: break
                                if time.time() - start_time > timeout_seconds:
                                    search_timed_out = True; break
                                
                                try: # fnmatch can sometimes error with weird filenames
                                    if fnmatch.fnmatch(name.lower(), search_pattern_os):
                                        full_path = os.path.join(root, name)
                                        results.append((full_path, name)) # Store full path and name
                                        if len(results) >= self.display_limit * 5: # Stop if too many results are found early
                                            log.info("Reached early result limit for find_file.")
                                            search_timed_out = True; break # Treat as timeout to stop search
                                except Exception as e_fnmatch:
                                    log.warning(f"fnmatch error with file '{name}': {e_fnmatch}")

                                processed_files += 1
                                files_in_current_dir +=1
                                if processed_files % 500 == 0: # Check cancellation periodically
                                    if self.find_file_cancel.is_set(): search_cancelled = True; break
                    except OSError as e_walk:
                        log.warning(f"Could not access or walk directory '{dir_path}': {e_walk}")
                    except Exception as e_outer_walk:
                        log.error(f"Unexpected error during os.walk in '{dir_path}': {e_outer_walk}")


        except Exception as e_thread:
            log.error(f"Error during file search thread: {e_thread}", exc_info=True)
            error_message = f"Lỗi trong quá trình tìm kiếm: {type(e_thread).__name__}"

        # --- Update GUI after search ---
        if error_message:
            self.after(0, self.display_message, f"Bot: {error_message}", "Bot", speak_this_message=True)
            self.after(0, self._reset_search_state)
        elif search_cancelled:
            self.after(0, self.display_message, "Bot: Đã hủy tìm kiếm file.", "Bot", speak_this_message=True)
            self.after(0, self._reset_search_state)
        else:
            log.info(f"File search finished. Found {len(results)} results. Processed ~{processed_files} items.")
            if search_timed_out and len(results) < self.display_limit * 5 : # Only show timeout if not already stopped by result limit
                self.after(0, self.display_message, "Bot: Tìm kiếm file bị giới hạn thời gian.", "Bot", speak_this_message=False)
            
            self.last_search_results = results
            self.last_search_display_index = 0 # Reset display index for new search
            self.after(0, self._display_file_results, results, location_name_display)

    def _display_file_results(self, current_results, location_name):
        if self.find_file_cancel.is_set() and not current_results : # If cancelled before any display
            log.info("Display file results skipped due to cancellation (no prior results).")
            self._reset_search_state()
            return

        if not current_results:
            search_context = f" trong {location_name}" if location_name else ""
            self.display_message(f"Bot: Không tìm thấy file nào khớp{search_context}.", sender="Bot", speak_this_message=True)
            self._reset_search_state() # No results, so reset
            return

        start_idx = self.last_search_display_index
        end_idx = min(start_idx + self.display_limit, len(current_results))
        result_subset = current_results[start_idx:end_idx]

        if not result_subset and start_idx > 0 : # Trying to show more but no more subset
             self.display_message("Bot: Không còn kết quả nào để hiển thị.", sender="Bot", speak_this_message=True)
             self._update_show_more_button(False)
             return

        response_parts = [f"Tìm thấy {len(current_results)} file"]
        if location_name: response_parts.append(f"tại '{location_name}'")
        response_parts.append(f"(hiển thị {start_idx + 1}-{end_idx}):")
        
        for i, (full_path, name) in enumerate(result_subset, start=start_idx + 1):
            response_parts.append(f"{i}. {name} ({os.path.dirname(full_path)})") # Show name and parent dir

        self.last_search_display_index = end_idx # Update for next "show more"
        more_available = end_idx < len(current_results)

        self.display_message(f"Bot: {chr(10).join(response_parts)}", sender="Bot", speak_this_message=False) # Don't speak long list
        self._update_show_more_button(more_available)

    def _handle_show_more_results(self):
        log.info("Handling show more results.")
        if not self.last_search_results or self.last_search_display_index >= len(self.last_search_results):
            log.info("No more results to show or no previous search.")
            return "Không có kết quả nào nữa để hiển thị.", False

        # Reuse _display_file_results to show the next chunk
        self._display_file_results(self.last_search_results, "kết quả trước đó") # location_name is just for context here
        # _display_file_results handles the actual response message and button update
        # So this function primarily acts as a trigger and returns a generic confirmation
        # The actual textual response for "show more" is now part of _display_file_results
        more_available_after_display = self.last_search_display_index < len(self.last_search_results)
        return "Đang hiển thị thêm kết quả...", more_available_after_display # Simple message for log

    def _update_show_more_button(self, more_available):
        if more_available:
            self.show_more_button.grid(**self.show_more_button_grid_info)
            self.show_more_button.configure(state="normal")
            log.debug("Show more button enabled and visible.")
        else:
            self.show_more_button.grid_remove()
            log.debug("Show more button hidden.")

    def _reset_search_state(self):
        log.debug("Resetting file search state.")
        self.last_search_results = []
        self.last_search_display_index = 0
        self.find_file_cancel.set() # Cancel any ongoing search
        self._update_show_more_button(False)

    def _parse_complex_location(self, location_str):
        if not location_str: return None
        location_lower = location_str.lower().strip().strip('"').strip("'")
        log.info(f"Parsing location string: '{location_str}' (parsed as: '{location_lower}')")

        # Check direct aliases
        if location_lower in LOCATION_MAP:
            path = LOCATION_MAP[location_lower]
            if os.path.isdir(path):
                log.info(f"Location mapped to alias '{location_lower}': {path}")
                return path
            else: log.warning(f"Alias '{location_lower}' path '{path}' is not a valid directory.")

        # Check for drive letters (e.g., "ổ C", "C")
        if (location_lower.startswith("ổ ") and len(location_lower) == 3 and location_lower[2].isalpha()) or \
           (len(location_lower) == 1 and location_lower.isalpha()):
            drive_letter = location_lower[-1].upper()
            drive_path = f"{drive_letter}:\\"
            if os.path.isdir(drive_path):
                log.info(f"Location identified as drive: {drive_path}")
                return drive_path
            else: log.warning(f"Drive '{drive_path}' does not exist or is not a directory.")
        
        # Check if it's an absolute path already
        if os.path.isabs(location_str) and os.path.isdir(location_str): # Check original case for path
            log.info(f"Location is a valid absolute path: {location_str}")
            return location_str

        log.warning(f"Could not parse location string '{location_str}' to a valid path.")
        return None # No valid path found

    def _initialize_location_map(self):
        global LOCATION_MAP # Make sure to use the global
        user_home = os.path.expanduser("~")
        potential_locations = {
            "desktop": os.path.join(user_home, "Desktop"),
            "màn hình nền": os.path.join(user_home, "Desktop"),
            "tài liệu": os.path.join(user_home, "Documents"),
            "documents": os.path.join(user_home, "Documents"),
            "tải xuống": os.path.join(user_home, "Downloads"),
            "download": os.path.join(user_home, "Downloads"),
            "hình ảnh": os.path.join(user_home, "Pictures"),
            "pictures": os.path.join(user_home, "Pictures"),
            "nhạc": os.path.join(user_home, "Music"),
            "music": os.path.join(user_home, "Music"),
            "video": os.path.join(user_home, "Videos"),
            "videos": os.path.join(user_home, "Videos"),
        }
        LOCATION_MAP = {} # Reset before populating
        for alias, path in potential_locations.items():
            if os.path.isdir(path):
                LOCATION_MAP[alias] = path
            else:
                log.warning(f"Default location alias '{alias}' path does not exist: {path}")
        log.info(f"Initialized LOCATION_MAP with {len(LOCATION_MAP)} entries.")


    def display_message(self, message, sender="User", speak_this_message=True):
        if threading.current_thread() is not threading.main_thread():
            self.after(0, self.display_message, message, sender, speak_this_message)
            return

        if len(self.message_widgets) >= self.max_messages:
            try:
                oldest_frame = self.message_widgets.pop(0)
                oldest_frame.destroy()
            except Exception as e:
                log.error(f"Error destroying oldest message frame: {e}")

        try:
            # Determine alignment and color based on sender
            anchor_side = "e" if sender == "User" else "w"
            frame_fg_color = ("#E1F5FE", "#2B5278") if sender == "User" else (("gray95", "gray20")) # User messages different color
            text_color = ("black", "white") # Default, can be customized more

            frame = ctk.CTkFrame(self.chat_display_frame, fg_color=frame_fg_color, corner_radius=10)
            frame.grid(row=len(self.message_widgets), column=0, padx=10, pady=(5, 2), sticky=anchor_side)
            frame.grid_columnconfigure(0, weight=0) # Don't let label expand frame unnecessarily

            label = ctk.CTkLabel(
                frame,
                text=message,
                font=("Segoe UI", 14),
                wraplength=self.chat_display_frame.winfo_width() - 70, # Adjusted wraplength
                anchor="w", # Always anchor text to west within its bubble
                justify="left", # Always justify left within its bubble
                text_color=text_color
            )
            label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

            self.message_widgets.append(frame)
            self.update_idletasks() # Ensure layout is updated
            self.chat_display_frame._parent_canvas.yview_moveto(1.0) # Scroll to bottom

            if sender == "Bot" and speak_this_message:
                text_for_speech = message
                if message.startswith("Bot: "):
                    text_for_speech = message[len("Bot: "):]
                self.speak(text_for_speech)
        except Exception as e:
            log.error(f"Error displaying message: {e}", exc_info=True)


    def clear_chat_history(self):
        log.info("Clearing chat history.")
        for frame in self.message_widgets:
            try: frame.destroy()
            except tk.TclError: pass # Widget already destroyed
            except Exception as e: log.error(f"Error destroying message frame during clear: {e}")
        self.message_widgets = []
        self.message_history = [] # Clear command history too
        self.history_index = 0
        self._reset_search_state() # Also reset search results
        self.display_message("Bot: Lịch sử chat và tìm kiếm đã được xóa.", sender="Bot", speak_this_message=True)

    def send_message_event(self, event=None):
        message = self.entry_message.get().strip()
        if message:
            if not self.message_history or self.message_history[-1] != message:
                self.message_history.append(message)
            self.history_index = len(self.message_history) # Reset index to end for new message

            self.display_message(message, sender="User", speak_this_message=False) # User's own message, don't speak
            self.entry_message.delete(0, tk.END)
            
            # Process command in a new thread
            threading.Thread(target=self.process_command, args=(message,), daemon=True).start()

    def recall_previous_message(self, event=None): # Allow calling without event
        if not self.message_history: return
        if self.history_index > 0:
            self.history_index -= 1
            self.entry_message.delete(0, tk.END)
            self.entry_message.insert(0, self.message_history[self.history_index])
            self.entry_message.icursor(tk.END) # Move cursor to end
        return "break" # Prevents default widget behavior for arrow keys

    def recall_next_message(self, event=None): # Allow calling without event
        if not self.message_history: return
        if self.history_index < len(self.message_history) -1 :
            self.history_index += 1
            self.entry_message.delete(0, tk.END)
            self.entry_message.insert(0, self.message_history[self.history_index])
            self.entry_message.icursor(tk.END)
        elif self.history_index == len(self.message_history) -1: # If at the last typed message
            self.history_index = len(self.message_history) # Move "beyond" history
            self.entry_message.delete(0, tk.END) # Clear entry to type new message
        return "break"

    def paste_on_right_click(self, event):
        try:
            clipboard_content = self.clipboard_get()
            self.entry_message.insert(tk.INSERT, clipboard_content)
        except tk.TclError: log.warning("Could not get clipboard content (empty or not text).")
        except Exception as e: log.error(f"Error pasting from clipboard: {e}")

    def toggle_theme(self):
        current_mode = ctk.get_appearance_mode()
        new_mode = "Light" if current_mode == "Dark" else "Dark"
        log.info(f"Toggling theme from {current_mode} to: {new_mode}")
        ctk.set_appearance_mode(new_mode)
        self._current_theme = new_mode # Update internal state
        
        # Update theme button text and colors
        initial_text_color = ("#333333", "#FFFFFF")
        initial_fg_color = ("#F0F0F0", "#2C2C2E")
        self.theme_button.configure(
            text="💡" if new_mode == "Dark" else "🌙",
            text_color=initial_text_color[0] if new_mode == "Light" else initial_text_color[1],
            fg_color=initial_fg_color[0] if new_mode == "Light" else initial_fg_color[1]
        )
        # You might need to update other themed widgets if their colors don't auto-update
        # For example, the mic button:
        self.mic_button.configure(
            text_color=initial_text_color[0] if new_mode == "Light" else initial_text_color[1],
            fg_color=initial_fg_color[0] if new_mode == "Light" else initial_fg_color[1]
        )


    def _on_show_more_button_click(self):
        log.info("Show more button clicked.")
        # _handle_show_more_results now directly calls _display_file_results,
        # which handles the message display and button update.
        # We just need to trigger it and potentially log its simple confirmation.
        response_text, more_available = self._handle_show_more_results()
        # If _handle_show_more_results displays the message itself, no need to do it here again.
        # self.display_message(f"Bot: {response_text}", sender="Bot", speak_this_message=False)
        # self._update_show_more_button(more_available) # This is now handled within _display_file_results flow
        log.info(f"Show more action resulted in: '{response_text}', more available: {more_available}")


if __name__ == "__main__":
    # Optional: Set high DPI awareness on Windows if not handled by customtkinter already
    # if platform.system() == "Windows":
    #     try:
    #         from ctypes import windll
    #         windll.shcore.SetProcessDpiAwareness(1)
    #     except Exception as e:
    #         log.warning(f"Could not set DPI awareness: {e}")
            
    app = ChatApp()
    app.mainloop()