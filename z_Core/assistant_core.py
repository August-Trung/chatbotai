"""Core module for Desktop Assistant (formerly chatbot_gui_v2_NLP)"""
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
    "youtube": {"open_cmd": ["start", "chrome", "https://www.youtube.com"], "process_name": "chrome.exe", "url": "https://www.youtube.com"},
    "facebook": {"open_cmd": ["start", "chrome", "https://www.facebook.com"], "process_name": "chrome.exe", "url": "https://www.facebook.com"},
    "gemini": {"open_cmd": ["start", "chrome", "https://gemini.google.com/app"], "process_name": "chrome.exe", "url": "https://gemini.google.com/app"},
    "chatgpt": {"open_cmd": ["start", "chrome", "https://chatgpt.com/"], "process_name": "chrome.exe", "url": "https://chatgpt.com/"},
    "claude": {"open_cmd": ["start", "chrome", "https://claude.ai/"], "process_name": "msedge.exe", "url": "https://claude.ai/"},
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

# Danh sách các trình duyệt để ưu tiên xử lý mở app
BROWSER_APPS = {"edge", "chrome", "firefox"}

# Danh sách các alias cho YouTube
YOUTUBE_ALIASES = {"youtube", "ytb", "yt"}

class ChatApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Trợ lý AI Desktop - V7.3.1 (NLP Enhanced - Fixed)")
        try:
            pass
        except Exception as e:
            log.error(f"An error occurred: {e}", exc_info=True)
            self.iconphoto(True, tk.PhotoImage(file="icon.png"))
        except Exception as e:
            log.error(f"Error setting icon: {e}")
        self.minsize(650, 500)

        # Biến trạng thái
        self.nlp = None
        self.intent_classifier = None
        self.last_search_results = []
        self.last_search_display_index = 0
        self.display_limit = 15
        self.command_queue = queue.Queue()
        self.message_widgets = []
        self.max_messages = 100
        self._initialize_location_map()
        self.geometry("800x650")
        self._current_theme = ctk.get_appearance_mode()
        self.message_history = []
        self.history_index = 0
        self.nlp_cache = {}
        self.intent_cache = {}
        self.find_file_cancel = threading.Event()
        self.is_windows = platform.system() == "Windows"

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
        self.bottom_frame.grid_columnconfigure(0, weight=0)
        self.bottom_frame.grid_columnconfigure(1, weight=1)
        self.bottom_frame.grid_columnconfigure(2, weight=0)
        self.bottom_frame.grid_columnconfigure(3, weight=0)
        self.bottom_frame.grid_columnconfigure(4, weight=0)

        # Các nút và ô nhập
        initial_text_color = ("#333333", "#FFFFFF")
        initial_fg_color = ("#F0F0F0", "#2C2C2E")
        self.theme_button = ctk.CTkButton(
            self.bottom_frame,
            text="💡" if self._current_theme == "Dark" else "🌙",
            width=40,
            height=40,
            command=self.toggle_theme,
            font=("Segoe UI Emoji", 18),
            text_color=initial_text_color[0] if self._current_theme == "Light" else initial_text_color[1],
            fg_color=initial_fg_color[0] if self._current_theme == "Light" else initial_fg_color[1],
            hover_color=("#4A90E2", "#E5E5E5"),
            corner_radius=10
        )
        self.theme_button.grid(row=0, column=0, padx=(15, 10), pady=15)
        self.entry_message = ctk.CTkEntry(
            self.bottom_frame,
            placeholder_text="Nhập tin nhắn...",
            font=("Segoe UI", 15),
            height=40,
            border_width=1,
            fg_color=("white", "gray25"),
            corner_radius=15,
            border_color=("#D3D3D3", "#555555")
        )
        self.entry_message.grid(row=0, column=1, padx=0, pady=15, sticky="ew")
        self.entry_message.bind("<Return>", self.send_message_event)
        self.entry_message.bind("<Up>", self.recall_previous_message)
        self.entry_message.bind("<Down>", self.recall_next_message)
        self.entry_message.bind("<Button-3>", self.paste_on_right_click)
        self.send_button = ctk.CTkButton(
            self.bottom_frame,
            text="Gửi",
            width=80,
            height=40,
            command=self.send_message_event,
            font=("Segoe UI", 15, "bold"),
            corner_radius=15,
            fg_color=("#4A90E2", "#1E90FF"),
            hover_color=("#4682B4", "#87CEFA")
        )
        self.send_button.grid(row=0, column=2, padx=(10, 5), pady=15)
        self.show_more_button = ctk.CTkButton(
            self.bottom_frame,
            text="Xem thêm",
            width=100,
            height=40,
            command=self._on_show_more_button_click,
            font=("Segoe UI", 15, "bold"),
            text_color_disabled="gray60",
            corner_radius=15,
            fg_color=("#4A90E2", "#1E90FF")
        )
        self.show_more_button_grid_info = {"row": 0, "column": 3, "padx": (0, 15), "pady": 15, "sticky": "e"}
        self.show_more_button.grid_remove()
        self.clear_button = ctk.CTkButton(
            self.bottom_frame,
            text="✖",
            width=30,
            height=30,
            font=("Segoe UI", 12),
            corner_radius=0,
            command=lambda: self.entry_message.delete(0, tk.END),
            fg_color=("white", "gray25"),
            text_color=("gray50", "gray60"),
        )
        self.clear_button.grid(row=0, column=1, padx=(0, 10), pady=15, sticky="e")
        self.clear_history_button = ctk.CTkButton(
            self.bottom_frame,
            text="Xóa lịch sử",
            width=100,
            height=40,
            command=self.clear_chat_history,
            font=("Segoe UI", 15, "bold"),
            corner_radius=15,
            fg_color=("#FF4040", "#FF6666"),
            hover_color=("#CC3333", "#FF9999")
        )
        self.clear_history_button.grid(row=0, column=4, padx=(0, 15), pady=15)

        self.display_message("Bot: Chào bạn! Giao diện đã được nâng cấp với NLP (V7.3.1).", sender="Bot")
        self._process_commands_from_queue()

    def _load_nlp_models(self):
        """Tải mô hình NLP khi cần (lazy loading)."""
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
                self.display_message("Bot: Mô hình NLP đã được tải.", sender="Bot")
            except Exception as e:
                log.error(f"Error loading NLP models: {e}")
                self.nlp = None
                self.intent_classifier = None
                self.display_message(f"Bot: Lỗi tải mô hình NLP: {e}. Chuyển sang chế độ từ khóa.", sender="Bot")

    def preprocess_vietnamese(self, text):
        """Phân đoạn từ tiếng Việt và xử lý shorthand."""
        try:
            # Xử lý shorthand như "mđ" -> "microsoft"
            text = text.lower().replace("mđ", "microsoft")
            return word_tokenize(text, format="text")
        except Exception as e:
            log.error(f"Error in preprocess_vietnamese: {e}")
            return text

    def sanitize_input(self, text):
        """Kiểm tra và làm sạch đầu vào để tăng bảo mật."""
        forbidden_chars = ['&', '|', ';', '`', '$', '>', '<']
        if any(char in text for char in forbidden_chars):
            log.warning(f"Invalid input detected (forbidden chars): {text}")
            return None
        return text.strip()

    def process_command(self, command):
        """Xử lý câu lệnh bằng spaCy (NER) và PhoBERT (intent classification)."""
        command_clean = self.sanitize_input(command)
        if not command_clean:
            self.display_message("Bot: Đầu vào không hợp lệ, vui lòng thử lại.", sender="Bot")
            return

        self._load_nlp_models()
        if not self.nlp or not self.intent_classifier:
            log.warning("NLP models not available, falling back to keyword logic.")
            self._process_command_fallback(command_clean)
            return

        command_lower = command_clean.lower()
        log.info(f"Processing command with NLP: '{command_clean}'")

        # Kiểm tra từ khóa trước khi dùng NLP để đảm bảo "đóng" được ưu tiên
        keyword_intent = None
        if any(command_lower.startswith(kw) for kw in KW_SPACED_CLOSE):
            keyword_intent = "close_app"
            log.info(f"Keyword-based intent override: 'close_app' detected for command '{command_clean}'")
        elif any(command_lower.startswith(kw) for kw in KW_SPACED_OPEN):
            keyword_intent = "open_app"
            log.info(f"Keyword-based intent override: 'open_app' detected for command '{command_clean}'")

        # Cache lookup
        if command_lower in self.nlp_cache and command_lower in self.intent_cache:
            entities = self.nlp_cache[command_lower]
            intent = self.intent_cache[command_lower]
            log.info(f"Cache hit for '{command_lower}'. Intent: {intent}, Entities: {entities}")
        else:
            log.info(f"Cache miss for '{command_lower}'. Running NLP models.")
            processed_command = self.preprocess_vietnamese(command_lower)
            doc = self.nlp(processed_command)
            entities = {"app": None, "file": None, "path": None, "query": None}
            extracted_ents = []
            for ent in doc.ents:
                extracted_ents.append((ent.text, ent.label_))
                if ent.label_ == "APP":
                    entities["app"] = ent.text
                elif ent.label_ == "FILE":
                    entities["file"] = ent.text
                elif ent.label_ == "PATH":
                    entities["path"] = ent.text
                elif ent.label_ == "QUERY":
                    entities["query"] = ent.text
            log.info(f"NER results: {extracted_ents}")

            result = self.intent_classifier(command_clean)
            intent = result[0]["label"]
            confidence = result[0]["score"]
            log.info(f"Intent classification result: {intent} (Confidence: {confidence:.4f})")

            # Nếu confidence thấp, ưu tiên keyword_intent
            if confidence < 0.8 and keyword_intent:
                log.info(f"Low confidence ({confidence:.4f}) in NLP intent '{intent}'. Overriding with keyword intent: '{keyword_intent}'")
                intent = keyword_intent

            # Chỉ ghi đè thành open_app nếu không phải lệnh tìm kiếm và không có "trên" với youtube alias
            if entities["app"] and intent != "close_app":
                app_name = entities["app"]
                canonical_app_name = ALIAS_MAP.get(app_name.lower(), app_name.lower())
                is_search_command = any(kw in command_lower for kw in ("tìm nhạc", "tìm bài hát", "tìm video"))
                is_on_youtube = "trên" in command_lower and any(alias in command_lower for alias in YOUTUBE_ALIASES)
                if is_search_command and is_on_youtube:
                    log.info(f"Preserving 'open_website' intent for search command on '{canonical_app_name}'")
                else:
                    log.info(f"Overriding intent to 'open_app' due to detected APP entity: {app_name}")
                    intent = "open_app"
            
            # Truyền toàn bộ lệnh nếu là tìm kiếm trên YouTube
            if intent == "open_website" and is_search_command and is_on_youtube:
                query_or_app = command_clean  # Sử dụng toàn bộ chuỗi lệnh
                log.info(f"Intent open_website: target='{query_or_app}'")
            else:
                query_or_app = entities["query"] or entities["app"]
                log.info(f"Intent open_website: target='{query_or_app}'")

            # Update cache
            self.nlp_cache[command_lower] = entities
            self.intent_cache[command_lower] = intent
            if len(self.nlp_cache) > 500:
                self.nlp_cache = dict(list(self.nlp_cache.items())[-250:])
            if len(self.intent_cache) > 500:
                self.intent_cache = dict(list(self.intent_cache.items())[-250:])

        executed = False
        response = None
        try:
            # Ưu tiên keyword_intent nếu có
            if keyword_intent == "close_app" and intent != "close_app":
                log.info(f"Overriding NLP intent '{intent}' with keyword intent 'close_app'")
                intent = "close_app"
            elif keyword_intent == "open_app" and intent != "open_app":
                log.info(f"Overriding NLP intent '{intent}' with keyword intent 'open_app'")
                intent = "open_app"

            if intent == "close_app":
                app_name = entities["app"] or self._extract_app_from_command(command_clean)
                if app_name:
                    response = self._handle_close_app(app_name)
                else:
                    response = "Bạn muốn đóng ứng dụng nào?"
                executed = True
            elif intent == "open_app":
                app_name = entities["app"] or self._extract_app_from_command(command_clean)
                if app_name:
                    response = self._handle_open_app(app_name)
                else:
                    response = "Bạn muốn mở ứng dụng nào?"
                executed = True
            elif intent == "find_file":
                file_name = entities["file"] or self._extract_file_from_command(command_clean)
                path_str = entities["path"]
                search_path = self._parse_complex_location(path_str) if path_str else None

                if file_name:
                    self.find_file_cancel.clear()
                    self.display_message("Bot: Đang tìm kiếm file...", sender="Bot")
                    self.command_queue.put(("find_file", file_name, [search_path] if search_path else None, path_str))
                    response = None
                else:
                    response = "Vui lòng cung cấp tên file hoặc mẫu cần tìm."
                executed = True
            elif intent == "open_website":
                # Chỉ xử lý open_website nếu không có APP entity là trình duyệt
                app_name = entities["app"]
                canonical_app_name = ALIAS_MAP.get(app_name.lower(), app_name.lower()) if app_name else None
                if app_name and canonical_app_name in BROWSER_APPS:
                    log.info(f"Detected APP entity as browser ({app_name}), treating as open_app instead of open_website")
                    response = self._handle_open_app(app_name)
                    executed = True
                else:
                    query_or_app = entities["query"] or entities["app"]
                    target = query_or_app or command_clean
                    log.info(f"Intent open_website: target='{target}'")
                    self.command_queue.put(("open_website", target, None))
                    response = None
                    executed = True
            elif intent == "show_more":
                response, more_available = self._handle_show_more_results()
                self._update_show_more_button(more_available)
                executed = True

            if not executed:
                log.warning(f"NLP processed but no action taken for intent '{intent}' and command '{command_clean}'")
                response = f"Xin lỗi, tôi chưa hiểu lệnh này (Intent: {intent})."

        except Exception as e:
            log.error(f"Error processing NLP command '{command_clean}': {e}", exc_info=True)
            response = f"Có lỗi xảy ra khi xử lý lệnh: {e}"

        if response:
            self.display_message(f"Bot: {response}", sender="Bot")

    def _process_command_fallback(self, command):
        """Logic dự phòng dựa trên từ khóa nếu NLP thất bại hoặc không xác định được."""
        command_lower = command.lower()
        log.info(f"Processing command with fallback logic: '{command}'")
        response = f"Xin lỗi, tôi chưa hiểu lệnh: '{command}'"
        executed = False

        # Helper để trích xuất target
        def get_target_from_command(cmd_lower_full, kw_spaced_tuple):
            for kw in kw_spaced_tuple:
                if cmd_lower_full.startswith(kw):
                    return command[len(kw):].strip()
            return None

        # Xử lý "Xem thêm" trước
        is_show_more_command = command_lower in KW_BASE_SHOW_MORE or command_lower.startswith("xem thêm") or command_lower.startswith("hiển thị thêm")
        if is_show_more_command:
            response_tuple = self._handle_show_more_results()
            response = response_tuple[0]
            more_available = response_tuple[1]
            self._update_show_more_button(more_available)
            executed = True
        else:
            self._reset_search_state()

        # Lệnh Đóng (có target) - Ưu tiên kiểm tra trước
        if not executed:
            target_close = get_target_from_command(command_lower, KW_SPACED_CLOSE)
            if target_close is not None:
                response = self._handle_close_app(target_close)
                executed = True

        # Các lệnh đơn giản không có target
        if not executed:
            if command_lower in KW_BASE_CLOSE:
                response = "Bạn muốn đóng ứng dụng nào?"
                executed = True
            elif command_lower in KW_BASE_OPEN:
                response = "Bạn muốn mở ứng dụng/web nào?"
                executed = True
            elif command_lower in KW_BASE_WEB_SEARCH and command_lower not in ("tìm nhạc", "tìm bài hát"):
                response = "Bạn muốn truy cập web nào hoặc tìm kiếm gì?"
                executed = True
            elif command_lower in ("tìm nhạc", "tìm bài hát"):
                response = "Bạn muốn tìm bài nhạc nào?"
                executed = True
            elif command_lower in KW_BASE_FIND_FILE:
                response = "Bạn muốn tìm file tên gì?"
                executed = True

        # Lệnh Tìm File (có target)
        if not executed:
            file_target_full = get_target_from_command(command_lower, KW_SPACED_FIND_FILE)
            if file_target_full is not None:
                if not file_target_full:
                    response = "Bạn muốn tìm file tên gì?"
                else:
                    pattern = file_target_full
                    search_location_paths = None
                    location_name_found = None
                    for prep in LOCATION_PREPOSITIONS:
                        prep_lower = prep.lower()
                        last_pos = file_target_full.lower().rfind(prep_lower)
                        if last_pos != -1:
                            potential_pattern = file_target_full[:last_pos].strip()
                            potential_location_str = file_target_full[last_pos + len(prep):].strip()
                            if potential_pattern:
                                parsed_path = self._parse_complex_location(potential_location_str)
                                if parsed_path:
                                    pattern = potential_pattern
                                    search_location_paths = [parsed_path]
                                    location_name_found = potential_location_str
                                    log.info(f"Find file: pattern='{pattern}', location='{location_name_found}', path='{parsed_path}'")
                                    break
                                else:
                                    log.warning(f"Could not parse location: '{potential_location_str}'")
                            else:
                                parsed_path = self._parse_complex_location(potential_location_str)
                                if parsed_path:
                                    pattern = "*"
                                    search_location_paths = [parsed_path]
                                    location_name_found = potential_location_str
                                    log.info(f"Find file: pattern='{pattern}', location='{location_name_found}', path='{parsed_path}'")
                                    break

                    self.find_file_cancel.clear()
                    self.display_message("Bot: Đang tìm kiếm file...", sender="Bot")
                    self.command_queue.put(("find_file", pattern, search_location_paths, location_name_found))
                    response = None
                executed = True

        # Lệnh Tìm Nhạc (có target)
        if not executed:
            song_target_full = get_target_from_command(command_lower, ("tìm nhạc ", "tìm bài hát "))
            if song_target_full is not None:
                song_title = song_target_full.strip()
                browser_key = None
                search_on_google = False
                search_on_youtube = False

                # Kiểm tra xem có yêu cầu tìm trên Google hay YouTube không
                google_triggers = [" trên google", " google"]
                youtube_triggers = [f" trên {alias}" for alias in YOUTUBE_ALIASES] + list(YOUTUBE_ALIASES)
                for trigger in google_triggers:
                    if song_title.lower().endswith(trigger):
                        search_on_google = True
                        song_title = song_title[:-len(trigger)].strip()
                        log.info(f"Music search explicitly requested on Google for '{song_title}'")
                        break
                if not search_on_google:
                    for trigger in youtube_triggers:
                        if song_title.lower().endswith(trigger):
                            search_on_youtube = True
                            song_title = song_title[:-len(trigger)].strip()
                            log.info(f"Music search explicitly requested on YouTube for '{song_title}'")
                            break

                # Kiểm tra browser nếu có
                for prep in BROWSER_PREPOSITIONS:
                    prep_lower = prep.lower()
                    if prep_lower in song_title.lower():
                        parts = song_title.rsplit(prep, 1)
                        if len(parts) == 2:
                            potential_browser_key = parts[1].strip().lower()
                            canonical_browser_key = ALIAS_MAP.get(potential_browser_key, potential_browser_key)
                            if canonical_browser_key in ["chrome", "edge", "firefox"]:
                                song_title = parts[0].strip()
                                browser_key = canonical_browser_key
                                log.info(f"Music search specified browser: {browser_key}")
                                break

                if not song_title:
                    response = "Bạn muốn tìm bài nhạc nào?"
                else:
                    final_url = ""
                    try:
                        search_query = urllib.parse.quote_plus(song_title)
                        if search_on_google:
                            final_url = f"https://www.google.com/search?q={search_query}"
                            log.info(f"Constructed Google search URL for music: {final_url}")
                        elif search_on_youtube:
                            final_url = f"https://www.youtube.com/results?search_query={search_query}"
                            log.info(f"Constructed YouTube search URL for music: {final_url}")
                        else:
                            final_url = f"https://www.youtube.com/results?search_query={search_query}"
                            log.info(f"Defaulted to YouTube search URL for music: {final_url}")
                    except Exception as e:
                        response = f"Lỗi tạo URL tìm kiếm nhạc: {e}"
                        log.error(f"Error creating music search URL for '{song_title}': {e}")
                        final_url = None

                    if final_url:
                        self.command_queue.put(("open_website", final_url, browser_key))
                        response = None
                    executed = True

        # Lệnh Mở Web / Tìm kiếm Web (có target)
        if not executed:
            web_search_keywords_no_music = tuple(kw for kw in KW_SPACED_WEB_SEARCH if kw not in ("tìm nhạc ", "tìm bài hát "))
            target_web = get_target_from_command(command_lower, web_search_keywords_no_music)
            if target_web is not None:
                browser_key = None
                target_to_use = target_web.strip()

                for prep in BROWSER_PREPOSITIONS:
                    prep_lower = prep.lower()
                    if prep_lower in target_to_use.lower():
                        parts = target_to_use.rsplit(prep, 1)
                        if len(parts) == 2:
                            potential_browser_key = parts[1].strip().lower()
                            canonical_browser_key = ALIAS_MAP.get(potential_browser_key, potential_browser_key)
                            if canonical_browser_key in ["chrome", "edge", "firefox"]:
                                target_to_use = parts[0].strip()
                                browser_key = canonical_browser_key
                                log.info(f"Web search/open specified browser: {browser_key}")
                                break

                if not target_to_use:
                    response = "Bạn muốn truy cập web nào hoặc tìm kiếm gì?"
                else:
                    # Kiểm tra xem target có phải là trình duyệt không
                    canonical_target = ALIAS_MAP.get(target_to_use.lower(), target_to_use.lower())
                    if canonical_target in BROWSER_APPS and browser_key is None:
                        log.info(f"Fallback: Treating '{target_to_use}' as app open instead of web search")
                        response = self._handle_open_app(target_to_use)
                    else:
                        log.info(f"Fallback identified web open/search: target='{target_to_use}', browser='{browser_key}'")
                        self.command_queue.put(("open_website", target_to_use, browser_key))
                        response = None
                executed = True

        # Lệnh Mở App (có target) - Kiểm tra sau cùng để tránh nhầm với đóng
        if not executed:
            target_open = get_target_from_command(command_lower, KW_SPACED_OPEN)
            if target_open is not None:
                browser_key = None
                target_to_use = target_open.strip()

                is_explicit_browser_app = False
                for prep in BROWSER_PREPOSITIONS:
                    prep_lower = prep.lower()
                    if prep_lower in target_to_use.lower():
                        parts = target_to_use.rsplit(prep, 1)
                        if len(parts) == 2:
                            potential_browser_key = parts[1].strip().lower()
                            canonical_browser_key = ALIAS_MAP.get(potential_browser_key, potential_browser_key)
                            if canonical_browser_key in ["chrome", "edge", "firefox"]:
                                if parts[0].strip().lower() == canonical_browser_key:
                                    target_to_use = canonical_browser_key
                                    is_explicit_browser_app = True
                                    break
                                else:
                                    target_to_use = parts[0].strip()
                                    break

                if not target_to_use:
                    response = "Bạn muốn mở ứng dụng nào?"
                else:
                    canonical_name = ALIAS_MAP.get(target_to_use.lower(), target_to_use.lower())
                    if canonical_name in WEBSITE_ALIASES and not is_explicit_browser_app and canonical_name not in BROWSER_APPS:
                        log.info(f"Fallback identified open website alias: '{target_to_use}'")
                        self.command_queue.put(("open_website", target_to_use, None))
                        response = None
                    else:
                        log.info(f"Fallback identified open app: '{target_to_use}'")
                        response = self._handle_open_app(target_to_use)
                executed = True

        if not executed:
            log.warning(f"Fallback logic could not understand command: '{command}'")

        if response:
            self.display_message(f"Bot: {response}", sender="Bot")

    def _process_commands_from_queue(self):
        """Xử lý lệnh từ hàng đợi trong main thread."""
        try:
            command_type, *args = self.command_queue.get_nowait()
            log.info(f"Processing command from queue: {command_type}, Args: {args}")

            if command_type == "find_file":
                threading.Thread(
                    target=self._find_file_thread,
                    args=args,
                    daemon=True
                ).start()
            elif command_type == "open_website":
                self.display_message("Bot: Đang xử lý yêu cầu mở web...", sender="Bot")
                threading.Thread(
                    target=self._handle_open_website_thread,
                    args=args,
                    daemon=True
                ).start()

            self.command_queue.task_done()
        except queue.Empty:
            pass
        except Exception as e:
            log.error(f"Error processing command queue: {e}", exc_info=True)

        self.after(100, self._process_commands_from_queue)

    def _extract_app_from_command(self, command):
        """Trích xuất tên ứng dụng (fallback nếu NER không tìm thấy)."""
        command_lower = command.lower()
        for alias, canonical in ALIAS_MAP.items():
            if alias in command_lower.split():
                if canonical in APP_MAPPINGS:
                    return canonical
        for app in APP_MAPPINGS:
            if app in command_lower.split():
                return app
        return command.split()[-1] if command.split() else command

    def _extract_file_from_command(self, command):
        """Trích xuất tên file (fallback nếu NER không tìm thấy)."""
        command_lower = command.lower()
        for ext_list in FILE_TYPE_EXTENSIONS.values():
            for ext in ext_list:
                if ext in command_lower:
                    parts = command_lower.split(ext)
                    if parts[0]:
                        pattern_part = parts[0]
                        for kw in KW_BASE_FIND_FILE:
                            if pattern_part.startswith(kw + " "):
                                pattern_part = pattern_part[len(kw)+1:]
                                break
                        for prep in LOCATION_PREPOSITIONS:
                            if prep in pattern_part:
                                pattern_part = pattern_part.split(prep)[0]
                                break
                        return pattern_part.strip() + ext

        for kw in KW_SPACED_FIND_FILE:
            if command_lower.startswith(kw):
                potential_file = command[len(kw):].strip()
                for prep in LOCATION_PREPOSITIONS:
                    if prep in potential_file:
                        potential_file = potential_file.split(prep)[0].strip()
                        break
                return potential_file
        return command

    def _handle_open_app(self, app_name):
        """Mở ứng dụng."""
        app_name_lower = app_name.lower()
        canonical_name = ALIAS_MAP.get(app_name_lower, app_name_lower)
        log.info(f"Attempting to open app: '{app_name}' (Canonical: '{canonical_name}')")

        if canonical_name in APP_MAPPINGS:
            app_info = APP_MAPPINGS[canonical_name]
            command_to_run = app_info["open_cmd"]
            use_shell = self.is_windows and command_to_run[0] == 'start'
            log.info(f"Executing command: {command_to_run} with shell={use_shell}")
            try:
                subprocess.run(command_to_run, shell=use_shell, check=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                log.info(f"Successfully opened {canonical_name}.")
                return f"Đã mở {canonical_name}."
            except FileNotFoundError:
                log.error(f"Command not found for {canonical_name}: {command_to_run}")
                return f"Lỗi: Lệnh hoặc ứng dụng '{canonical_name}' không tìm thấy. Hãy kiểm tra cài đặt."
            except subprocess.CalledProcessError as e:
                log.error(f"Error running command for {canonical_name}: {e}. stderr: {e.stderr.decode(errors='ignore')}")
                error_msg = f"Lỗi khi chạy lệnh mở {canonical_name}."
                if self.is_windows and isinstance(e.__cause__, FileNotFoundError):
                    error_msg += " Có thể ứng dụng chưa được cài đặt hoặc không nằm trong PATH."
                elif "WinError 2" in str(e):
                    error_msg += " Có thể ứng dụng chưa được cài đặt hoặc không nằm trong PATH."
                return error_msg
            except Exception as e:
                log.error(f"Unexpected error opening {canonical_name}: {e}", exc_info=True)
                return f"Lỗi không xác định khi mở {canonical_name}: {e}"
        else:
            log.warning(f"Application not found in APP_MAPPINGS: '{app_name}' (Canonical: '{canonical_name}')")
            return f"Không tìm thấy cấu hình cho ứng dụng: {app_name}"

    def _handle_close_app(self, app_name):
        """Đóng ứng dụng."""
        app_name_lower = app_name.lower()
        canonical_name = ALIAS_MAP.get(app_name_lower, app_name_lower)
        log.info(f"Attempting to close app: '{app_name}' (Canonical: '{canonical_name}')")

        if canonical_name in APP_MAPPINGS and "process_name" in APP_MAPPINGS[canonical_name]:
            process_name = APP_MAPPINGS[canonical_name]["process_name"]
            log.info(f"Target process name: {process_name}")
            try:
                if self.is_windows:
                    command = ["taskkill", "/F", "/IM", process_name]
                    log.info(f"Executing close command on Windows: {command}")
                    result = subprocess.run(
                        command,
                        shell=False,
                        check=True,
                        capture_output=True,
                        text=True
                    )
                    log.info(f"taskkill stdout: {result.stdout}")
                    log.info(f"taskkill stderr: {result.stderr}")
                    if "SUCCESS" in result.stdout:
                        log.info(f"Successfully sent close signal to {process_name}.")
                        return f"Đã gửi yêu cầu đóng {canonical_name}."
                    elif "ERROR: The process" in result.stdout and "not found" in result.stdout:
                        log.warning(f"Process {process_name} not found when trying to close.")
                        return f"Không tìm thấy tiến trình {canonical_name} đang chạy."
                    else:
                        log.warning(f"taskkill command for {process_name} finished with unexpected output: {result.stdout}")
                        return f"Đã cố gắng đóng {canonical_name}, nhưng kết quả không chắc chắn. Kiểm tra xem ứng dụng có còn chạy không."
                else:
                    command = ["pkill", process_name]
                    log.info(f"Executing close command on non-Windows: {command}")
                    subprocess.run(command, shell=False, check=True)
                    log.info(f"Successfully sent kill signal to {process_name}.")
                    return f"Đã gửi yêu cầu đóng {canonical_name}."
            except FileNotFoundError:
                cmd_name = "taskkill" if self.is_windows else "pkill"
                log.error(f"Close command '{cmd_name}' not found.")
                return f"Lỗi: Lệnh '{cmd_name}' không tìm thấy trên hệ thống."
            except subprocess.CalledProcessError as e:
                stderr_output = e.stderr if e.stderr else "Không có thông tin chi tiết."
                log.warning(f"Error closing {canonical_name} (process: {process_name}). Stderr: {stderr_output}")
                if "not found" in stderr_output.lower():
                    return f"Không tìm thấy tiến trình {canonical_name} đang chạy."
                elif "access denied" in stderr_output.lower():
                    log.error(f"Permission denied while trying to close {process_name}.")
                    return f"Lỗi: Không có quyền đóng {canonical_name}. Vui lòng chạy chương trình với quyền quản trị (Run as Administrator) hoặc đóng ứng dụng thủ công."
                else:
                    return f"Lỗi khi đóng {canonical_name}: {stderr_output}. Vui lòng thử đóng thủ công."
            except Exception as e:
                log.error(f"Unexpected error closing {canonical_name}: {e}", exc_info=True)
                return f"Lỗi không xác định khi đóng {canonical_name}: {e}"
        else:
            log.warning(f"Cannot close app '{app_name}'. No process name defined or app not found.")
            return f"Không tìm thấy thông tin tiến trình để đóng ứng dụng: {app_name}"

    def _handle_open_website_thread(self, target, browser_key):
        """Mở website hoặc tìm kiếm trong thread riêng, ưu tiên webbrowser."""
        log.info(f"Thread: Handling open website. Target='{target}', BrowserKey='{browser_key}'")
        url_to_open = None
        message = f"Đang mở '{target}'..."
        success = False

        try:
            # Kiểm tra xem target đã là URL chưa
            if target.startswith("http://") or target.startswith("https://"):
                url_to_open = target
                log.info(f"Target is already a URL: {url_to_open}")
                message = f"Đang mở URL được cung cấp: {url_to_open}"
            else:
                target_lower = target.lower()
                canonical_name = ALIAS_MAP.get(target_lower, target_lower)

                # Kiểm tra xem target có phải là trình duyệt không
                if canonical_name in BROWSER_APPS:
                    log.info(f"Target '{target}' is a browser app, redirecting to open_app")
                    self.after(0, self._handle_open_app_wrapper, target)
                    return

                # Kiểm tra nếu target là một website alias (youtube, google, v.v.)
                if canonical_name in WEBSITE_ALIASES and canonical_name in APP_MAPPINGS:
                    app_info = APP_MAPPINGS[canonical_name]
                    if 'url' in app_info:
                        url_to_open = app_info['url']
                        log.info(f"Using pre-defined URL for alias '{canonical_name}': {url_to_open}")
                        message = f"Đang mở URL định sẵn cho '{canonical_name}': {url_to_open}"
                    else:
                        log.warning(f"Alias '{canonical_name}' is a website but has no 'url' defined. Searching instead.")
                        search_query = urllib.parse.quote_plus(canonical_name)
                        url_to_open = f"https://www.google.com/search?q={search_query}"
                        message = f"Không tìm thấy URL cho '{canonical_name}', đang tìm kiếm trên Google..."

                # Kiểm tra nếu là lệnh tìm kiếm trên YouTube
                is_search_command = any(kw in target_lower for kw in ("tìm nhạc", "tìm bài hát", "tìm video"))
                is_on_youtube = "trên" in target_lower and any(alias in target_lower for alias in YOUTUBE_ALIASES)
                if is_search_command and is_on_youtube:
                    # Tách query từ target
                    for alias in YOUTUBE_ALIASES:
                        if f" trên {alias}" in target_lower:
                            search_query = target_lower.split(f" trên {alias}")[0].strip()
                            break   
                    else:
                        search_query = target_lower.split(" trên ")[0].strip()
                    search_query_encoded = urllib.parse.quote_plus(search_query)
                    url_to_open = f"https://www.youtube.com/results?search_query={search_query_encoded}"
                    log.info(f"Constructed YouTube search URL for query: '{search_query}', URL: {url_to_open}")
                    message = f"Đang tìm kiếm '{search_query}' trên YouTube..."
                elif '.' in target and ' ' not in target:
                    url_to_open = "https://" + target
                    log.info(f"Target looks like a domain, adding https://: {url_to_open}")
                    message = f"Đang mở tên miền được nhận diện: {url_to_open}"
                else:
                    search_query_encoded = urllib.parse.quote_plus(target)
                    url_to_open = f"https://www.google.com/search?q={search_query_encoded}"
                    log.info(f"Target '{target}' does not look like a URL or YouTube search. Performing Google search.")
                    message = f"Đang tìm kiếm '{target}' trên Google..."

                # Nếu không phải URL hoặc alias, xử lý như một truy vấn tìm kiếm
                if url_to_open is None:
                    # Kiểm tra xem có yêu cầu tìm trên YouTube không
                    search_on_youtube = False
                    search_query = target
                    youtube_triggers = [f" trên {alias}" for alias in YOUTUBE_ALIASES] + list(YOUTUBE_ALIASES)
                    for trigger in youtube_triggers:
                        if target_lower.endswith(trigger):
                            search_on_youtube = True
                            search_query = target[:-len(trigger)].strip()
                            log.info(f"Detected YouTube search request in target: '{target}', query: '{search_query}'")
                            break

                    if search_on_youtube:
                        search_query_encoded = urllib.parse.quote_plus(search_query)
                        url_to_open = f"https://www.youtube.com/results?search_query={search_query_encoded}"
                        message = f"Đang tìm kiếm '{search_query}' trên YouTube..."
                    elif '.' in target and ' ' not in target:
                        url_to_open = "https://" + target
                        log.info(f"Target looks like a domain, adding https://: {url_to_open}")
                        message = f"Đang mở tên miền được nhận diện: {url_to_open}"
                    else:
                        search_query_encoded = urllib.parse.quote_plus(target)
                        url_to_open = f"https://www.google.com/search?q={search_query_encoded}"
                        log.info(f"Target '{target}' does not look like a URL or YouTube search. Performing Google search.")
                        message = f"Đang tìm kiếm '{target}' trên Google..."

            if url_to_open:
                log.info(f"Attempting to open URL with webbrowser: {url_to_open}")
                opened = webbrowser.open(url_to_open)
                if opened:
                    log.info("webbrowser.open returned True.")
                    message = f"Đã gửi yêu cầu mở: {url_to_open}"
                    success = True
                else:
                    log.warning("webbrowser.open returned False. Opening might have failed silently.")
                    message = f"Không thể mở '{target}'. Có thể không có trình duyệt mặc định hoặc URL không hợp lệ."
            else:
                message = f"Không thể xác định URL để mở cho '{target}'."

        except Exception as e:
            log.error(f"Error in _handle_open_website_thread for target '{target}': {e}", exc_info=True)
            message = f"Lỗi khi mở web '{target}': {e}"
            success = False

        self.after(0, self.display_message, f"Bot: {message}", "Bot")

    def _handle_open_app_wrapper(self, app_name):
        """Wrapper để gọi _handle_open_app từ thread khác."""
        response = self._handle_open_app(app_name)
        self.display_message(f"Bot: {response}", sender="Bot")

    def _find_file_thread(self, pattern, search_locations, location_name):
        """Tìm file trong thread riêng với giới hạn thời gian và hủy bỏ."""
        log.info(f"Thread: Starting file search. Pattern='{pattern}', Locations='{search_locations}', LocationName='{location_name}'")
        results = []
        search_timed_out = False
        search_cancelled = False
        error_message = None

        try:
            start_time = time.time()
            timeout = 30

            dirs_to_search = []
            if search_locations:
                dirs_to_search = [loc for loc in search_locations if loc and os.path.isdir(loc)]
                if not dirs_to_search:
                    log.warning(f"Provided search locations are invalid or do not exist: {search_locations}")
                    if location_name:
                        error_message = f"Không tìm thấy hoặc không thể truy cập thư mục được chỉ định: {location_name}"
                    else:
                        error_message = "Đường dẫn tìm kiếm không hợp lệ."
            else:
                default_dirs = [
                    os.path.join(os.path.expanduser("~"), "Desktop"),
                    os.path.join(os.path.expanduser("~"), "Documents"),
                    os.path.join(os.path.expanduser("~"), "Downloads"),
                ]
                if self.is_windows:
                    drive_generator = (f"{d}:\\" for d in "CDEFGHIJKLMNOPQRSTUVWXYZ" if os.path.exists(f"{d}:\\"))
                    default_dirs.extend(drive_generator)

                dirs_to_search = [d for d in default_dirs if os.path.isdir(d)]
                location_name = "các vị trí mặc định"
                log.info(f"No location specified, searching default locations: {dirs_to_search}")

            if not error_message:
                search_pattern_lower = f"*{pattern.lower()}*" if pattern != "*" else "*"

                for dir_path in dirs_to_search:
                    log.info(f"Searching in: {dir_path}")
                    try:
                        for root, _, files in os.walk(dir_path, topdown=True):
                            if self.find_file_cancel.is_set():
                                search_cancelled = True
                                log.info("File search cancelled.")
                                break
                            if time.time() - start_time > timeout:
                                search_timed_out = True
                                log.warning("File search timed out.")
                                break

                            for name in files:
                                try:
                                    if fnmatch.fnmatch(name.lower(), search_pattern_lower):
                                        full_path = os.path.join(root, name)
                                        results.append((full_path, name))
                                except Exception as e_file:
                                    log.warning(f"Error processing file name '{name}' in '{root}': {e_file}")

                            if search_cancelled or search_timed_out: break
                    except OSError as e_walk:
                        log.warning(f"Could not access or walk directory '{dir_path}': {e_walk}")
                    if search_cancelled or search_timed_out: break

        except Exception as e:
            log.error(f"Error during file search thread: {e}", exc_info=True)
            error_message = f"Lỗi trong quá trình tìm kiếm: {e}"

        if error_message:
            self.after(0, self.display_message, f"Bot: {error_message}", "Bot")
            self.after(0, self._reset_search_state)
        elif search_cancelled:
            self.after(0, self.display_message, "Bot: Đã hủy tìm kiếm file.", "Bot")
            self.after(0, self._reset_search_state)
        else:
            log.info(f"File search finished. Found {len(results)} results.")
            if search_timed_out:
                self.after(0, self.display_message, "Bot: Tìm kiếm bị giới hạn thời gian.", "Bot")
            self.last_search_results = results
            self.last_search_display_index = 0
            self.after(0, self._display_file_results, results, location_name)

    def _display_file_results(self, results, location_name):
        """Hiển thị kết quả tìm file trong main thread."""
        if self.find_file_cancel.is_set():
            log.info("Display file results skipped due to cancellation.")
            self._reset_search_state()
            return

        if not results:
            search_context = f" trong {location_name}" if location_name else ""
            self.display_message(f"Bot: Không tìm thấy file nào khớp{search_context}.", sender="Bot")
            self._reset_search_state()
            return

        start_idx = self.last_search_display_index
        end_idx = min(start_idx + self.display_limit, len(results))
        result_subset = results[start_idx:end_idx]

        response = f"Tìm thấy {len(results)} file"
        if location_name:
            response += f" tại {location_name}"
        response += f" (hiển thị {start_idx + 1}-{end_idx}):\n"
        response += "\n".join(f"- {f[1]} ({f[0]})" for f in result_subset)

        self.last_search_display_index = end_idx
        more_available = end_idx < len(results)

        self.display_message(f"Bot: {response}", sender="Bot")
        self._update_show_more_button(more_available)

    def _handle_show_more_results(self):
        """Xử lý hiển thị thêm kết quả tìm kiếm (chạy trong main thread)."""
        log.info("Handling show more results.")
        if not self.last_search_results or self.last_search_display_index >= len(self.last_search_results):
            log.info("No more results to show or no previous search.")
            return "Không có kết quả nào nữa để hiển thị.", False

        start_idx = self.last_search_display_index
        end_idx = min(start_idx + self.display_limit, len(self.last_search_results))
        result_subset = self.last_search_results[start_idx:end_idx]

        response = f"Kết quả tiếp theo ({start_idx + 1}-{end_idx} / {len(self.last_search_results)}):\n"
        response += "\n".join(f"- {f[1]} ({f[0]})" for f in result_subset)

        self.last_search_display_index = end_idx
        more_available = end_idx < len(self.last_search_results)

        log.info(f"Displayed results {start_idx + 1}-{end_idx}. More available: {more_available}")
        return response, more_available

    def _update_show_more_button(self, more_available):
        """Cập nhật trạng thái nút Xem thêm trong main thread."""
        if more_available:
            self.show_more_button.grid(**self.show_more_button_grid_info)
            self.show_more_button.configure(state="normal")
            log.debug("Show more button enabled.")
        else:
            self.show_more_button.grid_remove()
            log.debug("Show more button hidden.")

    def _reset_search_state(self):
        """Đặt lại trạng thái tìm kiếm file."""
        log.debug("Resetting file search state.")
        self.last_search_results = []
        self.last_search_display_index = 0
        self._update_show_more_button(False)

    def _parse_complex_location(self, location_str):
        """Phân tích đường dẫn từ chuỗi vị trí (cải thiện)."""
        if not location_str:
            return None
        location_lower = location_str.lower()
        log.info(f"Parsing location string: '{location_str}'")

        for alias, path in LOCATION_MAP.items():
            if location_lower == alias or location_lower == alias.lower():
                if os.path.isdir(path):
                    log.info(f"Location mapped to alias '{alias}': {path}")
                    return path
                else:
                    log.warning(f"Alias '{alias}' path '{path}' does not exist or is not a directory.")

        potential_path = location_str.strip('"')
        if os.path.isabs(potential_path) and os.path.isdir(potential_path):
            log.info(f"Location is a valid absolute path: {potential_path}")
            return potential_path

        drive_match = None
        if location_lower.startswith("ổ ") and len(location_lower) == 3 and location_lower[2].isalpha():
            drive_match = location_lower[2].upper()
        elif len(location_lower) == 1 and location_lower.isalpha():
            drive_match = location_lower.upper()

        if drive_match:
            drive_path = f"{drive_match}:\\"
            if os.path.exists(drive_path):
                log.info(f"Location identified as drive: {drive_path}")
                return drive_path
            else:
                log.warning(f"Drive '{drive_path}' does not exist.")

        log.warning(f"Could not parse location string '{location_str}' to a valid path.")
        return None

    def _initialize_location_map(self):
        """Khởi tạo ánh xạ vị trí."""
        global LOCATION_MAP
        user_home = os.path.expanduser("~")
        potential_locations = {
            "desktop": os.path.join(user_home, "Desktop"),
            "tài liệu": os.path.join(user_home, "Documents"),
            "documents": os.path.join(user_home, "Documents"),
            "download": os.path.join(user_home, "Downloads"),
            "tải xuống": os.path.join(user_home, "Downloads"),
            "pictures": os.path.join(user_home, "Pictures"),
            "hình ảnh": os.path.join(user_home, "Pictures"),
            "music": os.path.join(user_home, "Music"),
            "nhạc": os.path.join(user_home, "Music"),
            "video": os.path.join(user_home, "Videos"),
            "videos": os.path.join(user_home, "Videos"),
        }
        LOCATION_MAP = {}
        for alias, path in potential_locations.items():
            try:
                if os.path.isdir(path):
                    LOCATION_MAP[alias] = path
                else:
                    log.warning(f"Default location alias '{alias}' path does not exist: {path}")
            except Exception as e:
                log.error(f"Error checking path for alias '{alias}' ({path}): {e}")
        log.info(f"Initialized LOCATION_MAP: {LOCATION_MAP}")

    def display_message(self, message, sender="User"):
        """Hiển thị tin nhắn trong khung chat (chạy trên main thread)."""
        if threading.current_thread() is not threading.main_thread():
            log.warning(f"display_message called from non-main thread ({threading.current_thread().name}). Scheduling on main thread.")
            self.after(0, self.display_message, message, sender)
            return

        if len(self.message_widgets) >= self.max_messages:
            try:
                oldest_frame = self.message_widgets.pop(0)
                oldest_frame.destroy()
            except Exception as e:
                log.error(f"Error destroying oldest message frame: {e}")

        try:
            frame = ctk.CTkFrame(self.chat_display_frame, fg_color=("gray95", "gray20"), corner_radius=10)
            anchor_side = "e" if sender == "User" else "w"
            frame.grid(row=len(self.message_widgets), column=0, padx=10, pady=(5, 2), sticky=anchor_side)
            frame.grid_columnconfigure(0, weight=0)

            label = ctk.CTkLabel(
                frame,
                text=message,
                font=("Segoe UI", 14),
                wraplength=self.chat_display_frame.winfo_width() - 60,
                anchor="w",
                justify="left",
                text_color=("black", "white")
            )
            label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

            self.message_widgets.append(frame)
            self.update_idletasks()
            self.chat_display_frame._parent_canvas.yview_moveto(1.0)
        except Exception as e:
            log.error(f"Error displaying message: {e}", exc_info=True)

    def clear_chat_history(self):
        """Xóa lịch sử chat."""
        log.info("Clearing chat history.")
        for frame in self.message_widgets:
            try:
                frame.destroy()
            except tk.TclError:
                pass
            except Exception as e:
                log.error(f"Error destroying message frame during clear: {e}")
        self.message_widgets = []
        self.message_history = []
        self.history_index = 0
        self._reset_search_state()
        self.display_message("Bot: Lịch sử chat và kết quả tìm kiếm đã được xóa.", sender="Bot")

    def send_message_event(self, event=None):
        """Xử lý sự kiện gửi tin nhắn."""
        message = self.entry_message.get().strip()
        if message:
            if not self.message_history or self.message_history[-1] != message:
                self.message_history.append(message)
            self.history_index = len(self.message_history)

            self.display_message(message, sender="User")
            self.entry_message.delete(0, tk.END)

            threading.Thread(target=self.process_command, args=(message,), daemon=True).start()

    def recall_previous_message(self, event):
        """Gọi lại tin nhắn trước đó từ lịch sử."""
        if not self.message_history: return
        if self.history_index > 0:
            self.history_index -= 1
            self.entry_message.delete(0, tk.END)
            self.entry_message.insert(0, self.message_history[self.history_index])
            self.entry_message.icursor(tk.END)

    def recall_next_message(self, event):
        """Gọi lại tin nhắn tiếp theo (hoặc xóa nếu ở cuối)."""
        if not self.message_history: return
        if self.history_index < len(self.message_history) - 1:
            self.history_index += 1
            self.entry_message.delete(0, tk.END)
            self.entry_message.insert(0, self.message_history[self.history_index])
            self.entry_message.icursor(tk.END)
        elif self.history_index == len(self.message_history) - 1:
            self.history_index = len(self.message_history)
            self.entry_message.delete(0, tk.END)

    def paste_on_right_click(self, event):
        """Dán nội dung từ clipboard khi nhấp chuột phải vào ô nhập."""
        try:
            clipboard_content = self.clipboard_get()
            self.entry_message.insert(tk.INSERT, clipboard_content)
        except tk.TclError:
            log.warning("Could not get clipboard content.")
            pass
        except Exception as e:
            log.error(f"Error pasting from clipboard: {e}")

    def toggle_theme(self):
        """Chuyển đổi giao diện sáng/tối."""
        current_mode = ctk.get_appearance_mode()
        new_mode = "Light" if current_mode == "Dark" else "Dark"
        log.info(f"Toggling theme to: {new_mode}")
        ctk.set_appearance_mode(new_mode)
        self._current_theme = new_mode
        self.theme_button.configure(text="💡" if new_mode == "Dark" else "🌙")

    def _on_show_more_button_click(self):
        """Xử lý nút hiển thị thêm."""
        log.info("Show more button clicked.")
        response, more_available = self._handle_show_more_results()
        self.display_message(f"Bot: {response}", sender="Bot")
        self._update_show_more_button(more_available)

if __name__ == "__main__":
    if platform.system() == "Windows":
        pass
    app = ChatApp()
    app.mainloop()