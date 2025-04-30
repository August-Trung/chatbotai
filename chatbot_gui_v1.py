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

# --- Cài đặt Giao diện ---
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# --- Ánh xạ và Alias ---
APP_MAPPINGS = { "notepad": {"open_cmd": "notepad.exe", "process_name": "notepad.exe"}, "edge": {"open_cmd": "start msedge", "process_name": "msedge.exe"}, "chrome": {"open_cmd": "start chrome", "process_name": "chrome.exe"}, "firefox": {"open_cmd": "start firefox", "process_name": "firefox.exe"}, "cmd": {"open_cmd": "start cmd.exe" if platform.system() == "Windows" else "gnome-terminal", "process_name": "cmd.exe"}, "terminal": {"open_cmd": "start wt.exe" if platform.system() == "Windows" else "gnome-terminal", "process_name": "WindowsTerminal.exe" if platform.system() == "Windows" else "gnome-terminal-"}, "calculator": {"open_cmd": "calc.exe", "process_name": "CalculatorApp.exe"}, "explorer": {"open_cmd": "explorer.exe", "process_name": "explorer.exe"}, "google": {"open_cmd": "start chrome https://www.google.com", "process_name": "chrome.exe"}, "youtube": {"open_cmd": "start chrome https://www.youtube.com", "process_name": "chrome.exe"}, "facebook": {"open_cmd": "start chrome https://www.facebook.com", "process_name": "chrome.exe"}, "gemini": {"open_cmd": "start chrome https://gemini.google.com/app", "process_name": "chrome.exe"}, "chatgpt": {"open_cmd": "start chrome https://chatgpt.com/", "process_name": "chrome.exe"}, }
ALIAS_MAP = { "note": "notepad", "me": "edge", "gg": "google", "ytb": "youtube", "yt": "youtube", "cal": "calculator", "exp": "explorer", "fb": "facebook", "face": "facebook", "gem": "gemini", "gemini": "gemini", "gpt": "chatgpt", }
FILE_TYPE_EXTENSIONS = { "excel": (".xlsx", ".xls", ".xlsm", ".xlsb", ".csv"), "xls": (".xlsx", ".xls", ".xlsm", ".xlsb", ".csv"), "xlsx": (".xlsx", ".xls", ".xlsm", ".xlsb", ".csv"), "word": (".docx", ".doc", ".rtf"), "doc": (".docx", ".doc", ".rtf"), "docx": (".docx", ".doc", ".rtf"), "powerpoint": (".pptx", ".ppt"), "ppt": (".pptx", ".ppt"), "pptx": (".pptx", ".ppt"), "pdf": (".pdf",), "ảnh": (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp", ".heic", ".jfif"), "anh": (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp", ".heic", ".jfif"), "jpg": (".jpg", ".jpeg", ".jfif"), "png": (".png",), "video": (".mp4", ".avi", ".mov", ".wmv", ".mkv", ".flv", ".webm"), "mp4": (".mp4", ".mov", ".avi", ".wmv", ".mkv"), "nhạc": (".mp3", ".wav", ".aac", ".flac", ".m4a", ".ogg"), "nhac": (".mp3", ".wav", ".aac", ".flac", ".m4a", ".ogg"), "mp3": (".mp3", ".m4a", ".aac"), "văn bản": (".txt", ".log", ".md"), "van ban": (".txt", ".log", ".md"), "text": (".txt", ".log", ".md"), "txt": (".txt",), "nén": (".zip", ".rar", ".7z", ".tar", ".gz"), "nen": (".zip", ".rar", ".7z", ".tar", ".gz"), "zip": (".zip",), "rar": (".rar",), }
WEBSITE_ALIASES = {"google", "youtube", "facebook", "gg", "ytb", "yt", "fb", "face", "gem", "gemini", "gpt", "chatgpt"}
# --- Định nghĩa các bộ từ khóa ---
KW_BASE_OPEN = ("mở", "khởi động"); KW_BASE_CLOSE = ("đóng", "tắt"); KW_BASE_WEB_SEARCH = ("truy cập", "vào web", "mở web", "mở trang", "tìm kiếm", "search", "tìm", "vào", "tìm nhạc")
KW_BASE_FIND_FILE = ("tìm file", "kiếm file", "tìm tập tin", "kiếm tập tin"); KW_BASE_SHOW_MORE = ("hiển thị thêm", "xem thêm", "thêm kết quả", "show more", "thêm")
KW_SPACED_OPEN = tuple(kw + " " for kw in KW_BASE_OPEN); KW_SPACED_CLOSE = tuple(kw + " " for kw in KW_BASE_CLOSE); KW_SPACED_WEB_SEARCH = tuple(kw + " " for kw in KW_BASE_WEB_SEARCH); KW_SPACED_FIND_FILE = tuple(kw + " " for kw in KW_BASE_FIND_FILE)
LOCATION_PREPOSITIONS = (" trong thư mục ", " tại thư mục ", " ở thư mục ", " trên ổ ", " trong ổ ", " tại ổ ", " ở ổ ", " trên ", " trong ", " ở ", " tại ")
BROWSER_PREPOSITIONS = (" trong ", " bằng ", " trên ")
LOCATION_MAP = {}

class ChatApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Trợ lý AI Desktop - V6.7 (Fix Location Map)") # Đổi tên version
        self.last_search_results = [] ; self.last_search_display_index = 0; self.display_limit = 15
        self.web_thread = None; self.find_file_thread = None
        self._initialize_location_map()
        self.geometry("750x600"); self._current_theme = ctk.get_appearance_mode(); self.message_history = []; self.history_index = 0
        self.grid_columnconfigure(0, weight=1); self.grid_rowconfigure(0, weight=1); self.grid_rowconfigure(1, weight=0)
        self.chat_display_frame = ctk.CTkScrollableFrame(self, label_text="Lịch sử Chat", label_font=("Segoe UI", 11, "italic"), fg_color="transparent")
        self.chat_display_frame.grid(row=0, column=0, padx=15, pady=(5, 10), sticky="nsew"); self.chat_display_frame.grid_columnconfigure(0, weight=1)
        self.bottom_frame = ctk.CTkFrame(self, height=60, corner_radius=0, fg_color="transparent")
        self.bottom_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew"); self.bottom_frame.grid_columnconfigure(0, weight=0); self.bottom_frame.grid_columnconfigure(1, weight=1); self.bottom_frame.grid_columnconfigure(2, weight=0); self.bottom_frame.grid_columnconfigure(3, weight=0)
        self.theme_button = ctk.CTkButton(self.bottom_frame, text="💡" if self._current_theme == "Dark" else "🌙", width=40, command=self.toggle_theme, font=("Segoe UI Emoji", 16))
        self.theme_button.grid(row=0, column=0, padx=(10, 5), pady=10)
        self.entry_message = ctk.CTkEntry(self.bottom_frame, placeholder_text="Nhập lệnh của bạn...", font=("Segoe UI", 14))
        self.entry_message.grid(row=0, column=1, padx=5, pady=10, sticky="ew"); self.entry_message.bind("<Return>", self.send_message_event); self.entry_message.bind("<Up>", self.recall_previous_message); self.entry_message.bind("<Down>", self.recall_next_message); self.entry_message.bind("<Button-3>", self.paste_on_right_click)
        self.send_button = ctk.CTkButton(self.bottom_frame, text="Gửi", width=70, command=self.send_message_event, font=("Segoe UI", 14, "bold"))
        self.send_button.grid(row=0, column=2, padx=5, pady=10)
        self.show_more_button = ctk.CTkButton(self.bottom_frame, text="Xem thêm", width=90, command=self._on_show_more_button_click, font=("Segoe UI", 14)); self.show_more_button_grid_info = {"row": 0, "column": 3, "padx": (0, 10), "pady": 10, "sticky": "e"}
        self.show_more_button.grid_remove()
        self.display_message("Bot: Đã cập nhật V6.7 - Sửa lỗi nhận diện vị trí 'ảnh', 'pictures'.", sender="Bot") # Đổi message

    # === V6.7: Sửa lại hàm khởi tạo LOCATION_MAP ===
    def _initialize_location_map(self):
        """Tạo map vị trí động, ít kiểm tra isdir hơn cho thư mục chuẩn."""
        global LOCATION_MAP
        home_dir = os.path.expanduser("~")
        # Định nghĩa các đường dẫn chuẩn và alias
        # Value là tuple: (Tên thư mục chuẩn hoặc Path ổ đĩa, is_drive_flag)
        location_map_temp = {
            "desktop": ("Desktop", False), "màn hình nền": ("Desktop", False), "màn hình chính": ("Desktop", False),
            "documents": ("Documents", False), "tài liệu": ("Documents", False), "document": ("Documents", False),
            "downloads": ("Downloads", False), "tải về": ("Downloads", False), "download": ("Downloads", False),
            "pictures": ("Pictures", False), "ảnh": ("Pictures", False), "anh": ("Pictures", False), "picture": ("Pictures", False),
            "music": ("Music", False), "nhạc": ("Music", False), "nhac": ("Music", False),
            "videos": ("Videos", False), "video": ("Videos", False),
            # Ổ đĩa
            "ổ c": ("C:\\", True), "c": ("C:\\", True), "c:": ("C:\\", True),
            "ổ d": ("D:\\", True), "d": ("D:\\", True), "d:": ("D:\\", True),
            "ổ e": ("E:\\", True), "e": ("E:\\", True), "e:": ("E:\\", True),
            "ổ f": ("F:\\", True), "f": ("F:\\", True), "f:": ("F:\\", True),
        }
        valid_map = {} # <--- Sửa lỗi typo, dùng valid_map
        sorted_keys = sorted(location_map_temp.keys(), key=len, reverse=True)

        # Kiểm tra thư mục home tồn tại không
        if not os.path.exists(home_dir):
             print(f"Cảnh báo: Không tìm thấy thư mục chính '{home_dir}'. Các vị trí chuẩn có thể không đúng.")

        for key in sorted_keys:
             path_info = location_map_temp[key]
             path_part = path_info[0]
             is_drive = path_info[1] # Lấy cờ is_drive

             try:
                 if is_drive:
                     # Chỉ kiểm tra sự tồn tại của gốc ổ đĩa
                     drive_path = path_part
                     if os.path.exists(drive_path):
                          valid_map[key] = drive_path # <--- Sửa lỗi typo
                          print(f"Map Verify: Drive '{key}' -> '{drive_path}' exists.")
                     else:
                          print(f"Map Verify: Drive '{key}' -> '{drive_path}' does NOT exist.")
                 else:
                     # Đối với thư mục chuẩn, tạo đường dẫn và thêm vào map
                     # *** KHÔNG kiểm tra isdir() nữa ***
                     full_path = os.path.join(home_dir, path_part)
                     valid_map[key] = full_path # <--- Sửa lỗi typo
                     print(f"Map Added: Standard Folder '{key}' -> '{full_path}' (existence assumed).")

             except Exception as e:
                  print(f"Map Verify Error processing key '{key}': {e}")

        LOCATION_MAP = valid_map # Gán vào biến global
        print(f"--- Location Map Initialized (V6.7 Logic) ---")
        for k, v in LOCATION_MAP.items(): # In ra map cuối cùng để dễ kiểm tra
            print(f"'{k}': '{v}'")
        print(f"--- End Location Map ---")


    # --- Các hàm còn lại giữ nguyên như V6.6.1 ---
    # (_on_show_more_button_click, process_command, _parse_complex_location,
    #  _find_file_thread, _handle_find_file_logic, _process_and_display_find_results,
    #  _handle_show_more_results, _format_search_results,
    #  _handle_open_website_thread, _handle_open_website,
    #  _handle_open_app, _handle_close_app, và các hàm giao diện khác)
    def _on_show_more_button_click(self):
        print("Show More button clicked."); result_string, more_available = self._handle_show_more_results();
        if result_string: self.display_message(result_string, sender="Bot")
        if more_available: self.show_more_button.grid(**self.show_more_button_grid_info); self.show_more_button.configure(state="normal")
        else: self.show_more_button.grid_remove()

    def process_command(self, command):
        command_lower = command.lower(); response = f"Xin lỗi, tôi chưa hiểu lệnh: '{command}'"; executed = False
        def get_target_from_command(cmd_lower_full, kw_spaced_tuple):
            for kw in kw_spaced_tuple:
                if cmd_lower_full.startswith(kw): return command[len(kw):].strip()
            return None
        is_show_more_command = command_lower in KW_BASE_SHOW_MORE
        if is_show_more_command: response_tuple = self._handle_show_more_results(); response = response_tuple[0]; executed = True
        elif command_lower in KW_BASE_OPEN: response = "Bạn muốn mở ứng dụng/web nào?"; executed = True
        elif command_lower in KW_BASE_CLOSE: response = "Bạn muốn đóng ứng dụng nào?"; executed = True
        elif command_lower in KW_BASE_WEB_SEARCH:
            if command_lower == "tìm nhạc": response = "Bạn muốn tìm bài nhạc nào?"
            else: response = "Bạn muốn truy cập web nào hoặc tìm kiếm gì?"
            executed = True
        elif command_lower in KW_BASE_FIND_FILE: response = "Bạn muốn tìm file tên gì?"; executed = True
        if not executed and not is_show_more_command: self.show_more_button.grid_remove(); self.last_search_results = []; self.last_search_display_index = 0
        if not executed: # Lệnh Đóng
            target_close = get_target_from_command(command_lower, KW_SPACED_CLOSE)
            if target_close is not None: executed = True; response = self._handle_close_app(target_close)
        if not executed: # Lệnh TÌM FILE
            file_target_full = get_target_from_command(command_lower, KW_SPACED_FIND_FILE)
            if file_target_full is not None:
                executed = True
                if not file_target_full: response = "Bạn muốn tìm file tên gì?"
                else:
                    pattern = file_target_full; search_location_paths = None; location_name_found = None; parsed = False
                    for prep in LOCATION_PREPOSITIONS:
                        prep_lower = prep.lower(); last_pos = file_target_full.lower().rfind(prep_lower)
                        if last_pos != -1:
                            potential_pattern = file_target_full[:last_pos].strip(); potential_location_str = file_target_full[last_pos + len(prep):].strip(); print(f"Found prep '{prep}'. Ptn='{potential_pattern}', Loc Str='{potential_location_str}'")
                            parsed_path = self._parse_complex_location(potential_location_str)
                            if parsed_path: pattern = potential_pattern; search_location_paths = [parsed_path]; location_name_found = potential_location_str; print(f"Advanced location parsed: '{potential_location_str}' -> '{search_location_paths[0]}'"); parsed = True; break
                            else: print(f"Could not resolve complex loc: '{potential_location_str}'")
                    print("\n--- Debug Before Starting Find Thread ---"); print(f"Final Pattern: '{pattern}'"); print(f"Final Paths: {search_location_paths}"); print(f"Final Loc Name: {location_name_found}"); print("--- End Debug ---")
                    if hasattr(self, 'find_file_thread') and self.find_file_thread and self.find_file_thread.is_alive(): response = "Bot: Đang bận tìm kiếm file..."
                    else:
                         if pattern: self.display_message("Bot: Đang tìm kiếm file...", sender="Bot"); self.find_file_thread = threading.Thread(target=self._find_file_thread, args=(pattern, search_location_paths, location_name_found), daemon=True); self.find_file_thread.start(); response = None
                         else: response = "Vui lòng cung cấp tên file hoặc mẫu cần tìm."
        if not executed: # Tìm Nhạc
            song_target_full = get_target_from_command(command_lower, ("tìm nhạc ",))
            if song_target_full is not None:
                executed = True; song_title = song_target_full; browser_key = None; search_on_google = False; browser_specified = False; temp_target = song_target_full
                for prep in BROWSER_PREPOSITIONS:
                    if prep in song_target_full.lower():
                        parts = song_target_full.rsplit(prep, 1);
                        if len(parts) == 2: browser_specified = True; target_part, browser_part = parts; potential_browser_key = browser_part.strip().lower(); temp_target = target_part.strip(); canonical_browser_key = ALIAS_MAP.get(potential_browser_key, potential_browser_key);
                        if canonical_browser_key in APP_MAPPINGS or canonical_browser_key == "google": search_on_google = True;
                        if canonical_browser_key in APP_MAPPINGS: browser_key = canonical_browser_key;
                        break
                song_title = temp_target
                if not search_on_google:
                    if " trên google" in song_title.lower(): search_on_google = True; song_title = song_title.lower().replace(" trên google", "").strip()
                    elif song_title.lower().endswith(" google"): search_on_google = True; song_title = song_title.rsplit(' ', 1)[0].strip()
                if not song_title: response = "Bạn muốn tìm bài nhạc nào?"
                else:
                    final_url = ""
                    if search_on_google:
                        try: search_query = urllib.parse.quote_plus(song_title); final_url = f"https://www.google.com/search?q={search_query}"
                        except Exception as e: response = f"Lỗi tạo URL Google: {e}"; final_url=None
                    else:
                        try: search_query = urllib.parse.quote_plus(song_title); final_url = f"https://www.youtube.com/results?search_query={search_query}"
                        except Exception as e: response = f"Lỗi tạo URL YouTube: {e}"; final_url=None
                    if final_url:
                         if hasattr(self, 'web_thread') and self.web_thread and self.web_thread.is_alive(): response = "Bot: Đang bận xử lý yêu cầu web trước đó..."
                         else: self.display_message("Bot: Đang mở web...", sender="Bot"); self.web_thread = threading.Thread(target=self._handle_open_website_thread, args=(final_url, browser_key), daemon=True); self.web_thread.start(); response = None
        if not executed: # Web/Search Chung
            web_search_keywords_no_music = tuple(kw for kw in KW_SPACED_WEB_SEARCH if kw != "tìm nhạc ")
            target_web = get_target_from_command(command_lower, web_search_keywords_no_music)
            if target_web is not None:
                executed = True; browser_key = None; target_to_use = target_web; browser_specified = False
                for prep in BROWSER_PREPOSITIONS:
                     if prep in target_web.lower():
                         parts = target_web.rsplit(prep, 1);
                         if len(parts) == 2: browser_specified=True; target_part, browser_part = parts; potential_browser_key = browser_part.strip().lower(); target_to_use = target_part.strip(); canonical_browser_key = ALIAS_MAP.get(potential_browser_key, potential_browser_key);
                         if canonical_browser_key in APP_MAPPINGS: browser_key = canonical_browser_key;
                         break
                if hasattr(self, 'web_thread') and self.web_thread and self.web_thread.is_alive(): response = "Bot: Đang bận xử lý yêu cầu web trước đó..."
                else: self.display_message("Bot: Đang xử lý yêu cầu web...", sender="Bot"); self.web_thread = threading.Thread(target=self._handle_open_website_thread, args=(target_to_use, browser_key), daemon=True); self.web_thread.start(); response = None
        if not executed: # Mở Chung
            target_open = get_target_from_command(command_lower, KW_SPACED_OPEN)
            if target_open is not None:
                executed = True; browser_key = None; target_to_use = target_open; browser_specified = False
                for prep in BROWSER_PREPOSITIONS:
                     if prep in target_open.lower():
                         browser_specified = True; parts = target_open.rsplit(prep, 1);
                         if len(parts) == 2: target_part, browser_part = parts; potential_browser_key = browser_part.strip().lower(); target_to_use = target_part.strip(); canonical_browser_key = ALIAS_MAP.get(potential_browser_key, potential_browser_key);
                         if canonical_browser_key in APP_MAPPINGS: browser_key = canonical_browser_key;
                         break
                target_lower = target_to_use.lower(); canonical_name = ALIAS_MAP.get(target_lower, target_lower); print(f"Debug 'mở': target='{target_to_use}', alias='{target_lower}', canonical='{canonical_name}'")
                is_web_target = False; final_target_for_web = target_to_use
                if browser_key: is_web_target = True; print(f"Reason: Browser '{browser_key}' specified.")
                elif canonical_name in WEBSITE_ALIASES:
                    is_web_target = True; print(f"Reason: Canonical name '{canonical_name}' is in WEBSITE_ALIASES.")
                    if canonical_name in APP_MAPPINGS and 'open_cmd' in APP_MAPPINGS[canonical_name]: cmd_parts = APP_MAPPINGS[canonical_name]['open_cmd'].split();
                    if cmd_parts[-1].startswith('http'): final_target_for_web = cmd_parts[-1]; print(f"Using defined URL for alias: {final_target_for_web}")
                    else:
                        if canonical_name == "google": final_target_for_web = "https://www.google.com"
                        elif canonical_name == "youtube": final_target_for_web = "https://www.youtube.com"
                        else:
                            if canonical_name == "google": final_target_for_web = "https://www.google.com"
                            elif canonical_name == "youtube": final_target_for_web = "https://www.youtube.com"
                elif canonical_name in APP_MAPPINGS: is_web_target = False; print(f"Reason: Canonical name '{canonical_name}' is in APP_MAPPINGS.")
                else:
                     print(f"Reason: Checking if '{target_to_use}' is URL/Search...")
                     try:
                         parsed = urllib.parse.urlparse(target_to_use)
                         if (parsed.scheme and parsed.netloc) or \
                            (not parsed.scheme and parsed.netloc and '.' in parsed.netloc and ' ' not in target_to_use) or \
                            (not parsed.scheme and not parsed.netloc and parsed.path and '.' in parsed.path and ' ' not in parsed.path): is_web_target = True
                         elif '.' in target_to_use or ' ' in target_to_use:
                             if not browser_specified: print(f"Heuristic: '{target_to_use}' not in Map/Aliases, looks like web/search -> treat as web."); is_web_target = True
                             else: print(f"Heuristic: '{target_to_use}' has invalid browser specified -> treat as potential unknown app."); is_web_target = False
                         else: print(f"Heuristic: '{target_to_use}' doesn't look like URL/Search -> treat as potential unknown app."); is_web_target = False
                     except ValueError: print(f"Parse Error: '{target_to_use}' is not URL -> treat as potential unknown app."); is_web_target = False
                if is_web_target:
                     if hasattr(self, 'web_thread') and self.web_thread and self.web_thread.is_alive(): response = "Bot: Đang bận xử lý yêu cầu web trước đó..."
                     else: self.display_message("Bot: Đang xử lý yêu cầu web...", sender="Bot"); self.web_thread = threading.Thread(target=self._handle_open_website_thread, args=(final_target_for_web, browser_key), daemon=True); self.web_thread.start(); response = None
                else: response = self._handle_open_app(target_to_use)

        if response: self.display_message(f"Bot: {response}", sender="Bot")

    # === V6.6: Hàm mới để phân tích vị trí phức tạp ===
    def _parse_complex_location(self, location_str): # Giữ nguyên logic V6.6
        loc_lower = location_str.lower().strip(); print(f"Parsing complex location: '{loc_lower}'")
        if loc_lower in LOCATION_MAP: print(f"Direct match found in LOCATION_MAP: '{loc_lower}' -> '{LOCATION_MAP[loc_lower]}'"); return LOCATION_MAP[loc_lower]
        base_path = None; relative_folder = ""; found_base_key = None; sorted_map_keys = sorted(LOCATION_MAP.keys(), key=len, reverse=True)
        for base_key in sorted_map_keys:
            if base_key in loc_lower:
                 start_idx = loc_lower.find(base_key); end_idx = start_idx + len(base_key); is_standalone = True
                 if start_idx > 0 and loc_lower[start_idx-1].isalnum(): is_standalone = False
                 if end_idx < len(loc_lower) and loc_lower[end_idx].isalnum(): is_standalone = False
                 if is_standalone:
                     base_path = LOCATION_MAP[base_key]; found_base_key = base_key; print(f"Found base location key: '{base_key}' -> '{base_path}'")
                     remaining_str = loc_lower.replace(base_key, "").strip(); connectors = ["của", "trên", "tại", "ở", "thư mục", "folder", "trong"]
                     for conn in connectors: remaining_str = remaining_str.replace(conn, "").strip()
                     relative_folder = remaining_str; print(f"Potential relative folder: '{relative_folder}'"); break
        if base_path and relative_folder:
            relative_folder = relative_folder.strip('"\'')
            try:
                full_path = os.path.join(base_path, relative_folder); print(f"Constructed path: '{full_path}'")
                if os.path.isdir(full_path): print("Path verified."); return full_path
                else:
                     print("Path does not exist or is not a directory.")
                     if os.path.exists(base_path):
                         for item in os.listdir(base_path):
                             item_path = os.path.join(base_path, item)
                             if os.path.isdir(item_path) and item.lower() == relative_folder.lower(): print(f"Found case-insensitive match: '{item_path}'"); return item_path
                         print("Case-insensitive match not found.")
            except Exception as e: print(f"Error joining or checking path: {e}"); return None
        elif base_path: print("Only base path found and verified."); return base_path
        print("Could not parse complex location."); return None

    # === V6.6.2: Hàm thực thi tìm file trong luồng riêng (Sửa callback) ===
    def _find_file_thread(self, pattern, search_paths, location_name):
        print(f"Starting find file thread for pattern: '{pattern}'")
        search_result_data = self._handle_find_file_logic(pattern, search_paths, location_name)
        # === SỬA LỖI V6.6.1/V6.6.2: Truyền các tham số tường minh ===
        results_list, pattern_returned, scope_or_error = search_result_data
        print(f"Thread preparing to callback. Passing pattern: '{pattern_returned}', scope: '{scope_or_error}', list_len: {len(results_list) if isinstance(results_list, list) else 'N/A'}")
        self.after(0, self._process_and_display_find_results, results_list, pattern_returned, scope_or_error)
        print(f"Find file thread finished for pattern: '{pattern}'") # In pattern gốc ban đầu

    # === V6.6: Hàm logic tìm file (Giữ nguyên) ===
    def _handle_find_file_logic(self, pattern, search_paths=None, location_name=None): # Giữ nguyên
        print(f"Logic: Searching for pattern/type: '{pattern}'");
        if search_paths: print(f"Logic: Specified search paths: {search_paths}")
        else: print("Logic: No specific paths provided, using defaults.")
        found_files_with_time = []; final_search_paths = []; search_scope_display = ""
        if search_paths:
            final_search_paths = [p for p in search_paths if os.path.isdir(p)]
            if not final_search_paths: return ([], pattern, f"Lỗi: Vị trí '{location_name or 'được chỉ định'}' không hợp lệ.")
            search_scope_display = location_name if location_name else ", ".join(final_search_paths)
        else:
            home_dir = os.path.expanduser("~"); default_dirs = ["Desktop", "Documents", "Downloads", "Pictures", "Music", "Videos"]
            final_search_paths = [os.path.join(home_dir, d) for d in default_dirs if os.path.isdir(os.path.join(home_dir, d))]
            if not final_search_paths: return ([], pattern, "Lỗi: Không tìm thấy thư mục mặc định.")
            search_scope_display = ", ".join([os.path.basename(p) for p in final_search_paths])
        print(f"Logic: Final search paths: {final_search_paths}"); print(f"Logic: Search scope display name: {search_scope_display}")
        pattern_lower = pattern.lower(); target_extensions = None; search_mode = "name"
        canonical_pattern = ALIAS_MAP.get(pattern_lower, pattern_lower)
        if canonical_pattern in FILE_TYPE_EXTENSIONS: target_extensions = FILE_TYPE_EXTENSIONS[canonical_pattern]; search_mode = "type"; print(f"Logic: Search mode: type ('{pattern}' -> {canonical_pattern}), extensions: {target_extensions}")
        elif pattern_lower in FILE_TYPE_EXTENSIONS: target_extensions = FILE_TYPE_EXTENSIONS[pattern_lower]; search_mode = "type"; print(f"Logic: Search mode: type ('{pattern}'), extensions: {target_extensions}")
        else: print(f"Logic: Search mode: name/pattern ('{pattern}')")
        try:
            max_search_count = 200; current_count = 0
            for search_dir in final_search_paths:
                print(f"Logic: Walking through: {search_dir}")
                try:
                     for root, dirs, files in os.walk(search_dir, topdown=True, onerror=lambda err: print(f"Error walking directory: {err}")):
                         dirs[:] = [d for d in dirs if not d.startswith('.') and not d.startswith('$') and '$Recycle.Bin' not in root]
                         files = [f for f in files if not f.startswith('.')]
                         for filename in files:
                            match = False; filename_lower = filename.lower()
                            if search_mode == "type":
                                if filename_lower.endswith(target_extensions): match = True
                            else:
                                use_wildcard = '*' in pattern or '?' in pattern
                                if use_wildcard:
                                    if fnmatch.fnmatch(filename_lower, pattern_lower): match = True
                                else:
                                    if pattern_lower in filename_lower: match = True
                            if match:
                                try: full_path = os.path.join(root, filename); mod_time = os.path.getmtime(full_path); found_files_with_time.append((full_path, mod_time)); current_count += 1;
                                except OSError as e: print(f"Skipping file due to OS error: {filename} - {e}"); continue
                            if current_count >= max_search_count: break
                         if current_count >= max_search_count: break
                except OSError as walk_error: print(f"Permission or OS error walking {search_dir}: {walk_error}. Skipping."); continue
                if current_count >= max_search_count: print(f"Reached max search limit ({max_search_count})."); break
        except Exception as e: print(f"Lỗi không xác định khi tìm file: {e}"); return ([], pattern, f"Lỗi không xác định.")
        if found_files_with_time: print(f"Logic: Sorting {len(found_files_with_time)} results..."); found_files_with_time.sort(key=lambda item: item[1], reverse=True)
        # Quan trọng: Trả về pattern GỐC đã nhận được và scope name đã xác định
        return (found_files_with_time, pattern, search_scope_display)

    # === V6.6.2: Hàm xử lý và hiển thị kết quả tìm kiếm (Sửa tham số + Thêm Debug) ===
    def _process_and_display_find_results(self, results_list, pattern_received, scope_or_error):
        """Nhận kết quả từ luồng tìm kiếm, lưu trữ, format và hiển thị."""
        print("\n--- Debug _process_and_display_find_results ---"); print(f"Callback received pattern: '{pattern_received}'"); print(f"Callback received scope_or_error: '{scope_or_error}'"); print(f"Callback received num results: {len(results_list) if isinstance(results_list, list) else 'N/A'}") # Thêm print này
        if not isinstance(results_list, list): self.display_message(f"Bot: {scope_or_error}", sender="Bot"); self.show_more_button.grid_remove(); print("--- End Debug ---"); return
        self.last_search_results = results_list; self.last_search_display_index = 0; scope_display_name = scope_or_error
        formatted_response, more_available = self._format_search_results(pattern_received, scope_display_name) # Dùng pattern_received
        self.display_message(f"Bot: {formatted_response}", sender="Bot")
        if more_available: self.show_more_button.grid(**self.show_more_button_grid_info); self.show_more_button.configure(state="normal"); print("Set Show More: NORMAL/SHOWN")
        else: self.show_more_button.grid_remove(); print("Set Show More: REMOVED")
        print("--- End Debug ---")


    # === Các hàm còn lại giữ nguyên ===
    # (_handle_show_more_results, _format_search_results, _handle_open_website_thread, ...)
    def _handle_show_more_results(self):
        print("\n--- Debug _handle_show_more_results ---"); print(f"Current index: {self.last_search_display_index}, Total: {len(self.last_search_results)}")
        if not self.last_search_results: return "Không có kết quả tìm kiếm trước đó.", False
        start_index = self.last_search_display_index
        if start_index >= len(self.last_search_results): return "Đã hiển thị tất cả kết quả.", False
        end_index = start_index + self.display_limit; results_chunk = self.last_search_results[start_index:end_index]; print(f"End index: {end_index}, Chunk size: {len(results_chunk)}")
        if not results_chunk: return "Không có thêm kết quả nào.", False
        self.last_search_display_index = end_index
        result_str = f"--- Kết quả tiếp theo ({start_index + 1}-{min(end_index, len(self.last_search_results))}/{len(self.last_search_results)}) ---\n"
        for f_path, _ in results_chunk: result_str += f"- {f_path}\n"
        more_available = self.last_search_display_index < len(self.last_search_results)
        if more_available: remaining = len(self.last_search_results) - self.last_search_display_index; result_str += f"... (Còn {remaining} file khác. Nhấn 'Xem thêm' hoặc gõ 'thêm')"
        else: result_str += "--- Đã hết kết quả ---"
        print(f"Next index: {self.last_search_display_index}, More available: {more_available}"); print("--- End Debug _handle_show_more_results ---\n"); return result_str.strip(), more_available
    def _format_search_results(self, pattern, scope):
        if not self.last_search_results: return f"Không tìm thấy file nào khớp với '{pattern}' trong {scope}.", False
        else:
            total_found = len(self.last_search_results); results_to_show = self.last_search_results[:self.display_limit]; self.last_search_display_index = len(results_to_show)
            result_str = f"---\nTìm thấy {total_found} file khớp với '{pattern}' trong {scope} (mới nhất trước):\n"
            for f_path, _ in results_to_show: result_str += f"- {f_path}\n"
            more_available = total_found > self.display_limit
            if more_available: remaining = total_found - self.display_limit; result_str += f"... (Còn {remaining} file khác. Nhấn 'Xem thêm' hoặc gõ 'thêm')"
            return result_str.strip(), more_available
    def _handle_open_website_thread(self, target, browser_key):
        response = self._handle_open_website(target, browser_key)
        self.after(0, self.display_message, f"Bot: {response}", "Bot")
    def _handle_open_website(self, target, browser_key=None):
        print(f"--- Debug _handle_open_website (Non-Selenium) ---"); print(f"Input Target: '{target}'"); print(f"Input Browser Key: '{browser_key}'"); final_url = ""; is_search = False
        try:
            target_cleaned = target.strip();
            if not target_cleaned: return "Lỗi: Không có URL hoặc nội dung tìm kiếm được cung cấp."
            if target_cleaned.startswith("https://www.youtube.com/results?search_query="): is_search = False; final_url = target_cleaned; print(f"Result: Determined as pre-made Youtube URL -> '{final_url}'")
            else:
                parsed_url = urllib.parse.urlparse(target_cleaned); print(f"Parsed URL components: {parsed_url}"); is_url = False
                if parsed_url.scheme and parsed_url.netloc: is_url = True; print("Reason: Scheme and Netloc found.")
                elif not parsed_url.scheme and parsed_url.netloc and '.' in parsed_url.netloc: is_url = True; print("Reason: No Scheme, but Netloc with '.' found.")
                elif not parsed_url.scheme and not parsed_url.netloc and parsed_url.path and '.' in parsed_url.path and ' ' not in parsed_url.path: is_url = True; print("Reason: No Scheme/Netloc, but Path looks like domain.")
                if is_url: final_url = target_cleaned; print(f"Result: Determined as URL -> '{final_url}'")
                else: is_search = True; print("Result: Determined as Google Search Query.")
        except ValueError: is_search = True; print(f"Result: URL Parsing Error, treating as Search Query.")
        if is_search:
            try: search_query = urllib.parse.quote_plus(target_cleaned); final_url = f"https://www.google.com/search?q={search_query}"; response_msg = f"Đang tìm kiếm '{target_cleaned}' trên Google..."; print(f"Created Google Search URL: {final_url}")
            except Exception as e: return f"Lỗi khi tạo URL tìm kiếm Google: {e}"
        elif final_url.startswith("https://www.youtube.com/results?search_query="):
             try: actual_query = urllib.parse.unquote_plus(final_url.split("search_query=")[1]); response_msg = f"Đang tìm '{actual_query}' trên YouTube..."
             except: response_msg = f"Đang mở kết quả tìm kiếm YouTube..."
        else:
             if not urllib.parse.urlparse(final_url).scheme: final_url = "http://" + final_url
             response_msg = f"Đang mở trang web: {final_url}"
        try:
            browser_display_name = browser_key if browser_key else "mặc định"; canonical_browser_key = ALIAS_MAP.get(browser_key.lower(), browser_key) if browser_key else None; browser_to_use_msg = f"bằng trình duyệt {browser_display_name}." ; browser_opened = False
            if canonical_browser_key and canonical_browser_key in APP_MAPPINGS:
                browser_info = APP_MAPPINGS[canonical_browser_key]; open_command_base = browser_info.get("open_cmd")
                if open_command_base:
                     if platform.system() == "Windows" and open_command_base.startswith("start "): full_command = f'{open_command_base} "{final_url}"'
                     elif platform.system() != "Windows": full_command = f'{open_command_base} "{final_url}"'
                     else: full_command = f'"{open_command_base}" "{final_url}"'
                     print(f"Executing specific browser command: {full_command}");
                     try: subprocess.Popen(full_command, shell=True); browser_opened = True
                     except Exception as sub_e: print(f"Error executing specific browser: {sub_e}. Falling back."); browser_opened = False
                else: print(f"Warning: No 'open_cmd' found for '{canonical_browser_key}'. Falling back.")
            if not browser_opened: print(f"Opening with default browser: {final_url}"); webbrowser.open(final_url, new=2)
            return response_msg + " " + browser_to_use_msg
        except Exception as e: return f"Lỗi khi mở trang web/tìm kiếm: {e}"
        finally: print(f"--- End Debug _handle_open_website ---")
    def _handle_open_app(self, app_name_key): # (Giữ nguyên)
        original_input = app_name_key; app_name_lower = app_name_key.lower(); canonical_name = ALIAS_MAP.get(app_name_lower, app_name_lower); print(f"Debug _handle_open_app: input='{original_input}', lower='{app_name_lower}', canonical='{canonical_name}'")
        if canonical_name in APP_MAPPINGS:
            app_info = APP_MAPPINGS[canonical_name]; open_command = app_info.get("open_cmd")
            if open_command:
                try: print(f"Executing open command for {canonical_name}: {open_command}"); subprocess.Popen(open_command, shell=True); feedback_name = canonical_name if canonical_name != app_name_lower else original_input; return f"Đã khởi chạy {feedback_name}." + (f" (từ '{original_input}')" if canonical_name != app_name_lower else "")
                except FileNotFoundError: return f"Lỗi: Không tìm thấy lệnh '{open_command}' cho {canonical_name}. Kiểm tra cài đặt PATH."
                except Exception as e: return f"Lỗi khi mở {canonical_name}: {e}"
            else: return f"Lỗi: Thiếu lệnh mở ('open_cmd') cho '{canonical_name}' trong cấu hình."
        else: return f"Xin lỗi, tôi không biết cách mở '{original_input}'. Không tìm thấy ứng dụng hoặc alias được định nghĩa."
    def _handle_close_app(self, app_name_key): # (Giữ nguyên)
        original_input = app_name_key; app_name_lower = app_name_key.lower(); canonical_name = ALIAS_MAP.get(app_name_lower, app_name_lower); print(f"Debug _handle_close_app: input='{original_input}', lower='{app_name_lower}', canonical='{canonical_name}'")
        if canonical_name in APP_MAPPINGS:
            app_info = APP_MAPPINGS[canonical_name]; process_name = app_info.get("process_name")
            if not process_name: return f"Lỗi: Thiếu 'process_name' để đóng '{canonical_name}'."
            feedback_name = canonical_name if canonical_name != app_name_lower else original_input; system = platform.system(); command_to_run = []; success_msg = f"Đã gửi yêu cầu đóng {feedback_name}..."; error_msg = f"Không thể đóng {feedback_name}."
            try:
                if system == "Windows": command_to_run = ["taskkill", "/F", "/IM", process_name]; result = subprocess.run(command_to_run, capture_output=True, text=True, check=False, shell=True); print(f"Taskkill result for {process_name}: {result.returncode}\nStdout: {result.stdout}\nStderr: {result.stderr}");
                elif system == "Linux" or system == "Darwin": command_to_run = ["pkill", "-f", process_name]; result = subprocess.run(command_to_run, capture_output=True, text=True, check=False); print(f"Pkill result for {process_name}: {result.returncode}\nStdout: {result.stdout}\nStderr: {result.stderr}");
                else: return f"Hệ điều hành '{system}' chưa được hỗ trợ đóng ứng dụng."
                if result.returncode == 0: return success_msg + (" (từ '%s')" % original_input if canonical_name != app_name_lower else "")
                elif "không tìm thấy tiến trình" in result.stderr.lower() or "process not found" in result.stderr.lower(): return f"{feedback_name} ({process_name}) dường như chưa chạy."
                else: return f"{error_msg} Lỗi: {result.stderr.strip()}"
            except FileNotFoundError: return f"Lỗi: Lệnh hệ thống ({command_to_run[0]}) không tìm thấy."
            except Exception as e: return f"{error_msg} Lỗi không xác định: {e}"
        else: return f"Xin lỗi, tôi không biết cách đóng '{original_input}'. Không tìm thấy ứng dụng hoặc alias được định nghĩa."
    def toggle_theme(self): new_mode = "Light" if self._current_theme == "Dark" else "Dark"; ctk.set_appearance_mode(new_mode); self._current_theme = new_mode; self.theme_button.configure(text="💡" if new_mode == "Dark" else "🌙")
    def display_message(self, message, sender):
        if sender == "User": anchor_side = "e"; justify_text = "right"; bubble_color = ctk.ThemeManager.theme["CTkButton"]["fg_color"]; text_color = ctk.ThemeManager.theme["CTkButton"]["text_color"]
        else: anchor_side = "w"; justify_text = "left"; bubble_color = ("#E5E5E5", "#2B2B2B")[1 if ctk.get_appearance_mode() == "Dark" else 0]; text_color = ctk.ThemeManager.theme["CTkLabel"]["text_color"]
        bubble_frame = ctk.CTkFrame(self.chat_display_frame, fg_color=bubble_color, corner_radius=15)
        try: scrollable_width = self.chat_display_frame.winfo_width() - 40
        except Exception: scrollable_width = 300
        if scrollable_width < 100: scrollable_width = 300
        wraplength = scrollable_width * 0.75
        message_label = ctk.CTkLabel(bubble_frame, text=message, font=("Segoe UI", 14), text_color=text_color, justify=justify_text, wraplength=wraplength); message_label.grid(row=0, column=0, padx=12, pady=10, sticky="w")
        bubble_frame.grid(row=self.chat_display_frame.grid_size()[1], column=0, padx=15, pady=(6, 3), sticky=anchor_side); self.after(50, self._scroll_to_bottom)
    def _scroll_to_bottom(self): self.chat_display_frame._parent_canvas.yview_moveto(1.0)
    def send_message_event(self, event=None):
        user_input = self.entry_message.get().strip();
        if user_input: self.display_message(user_input, sender="User"); self.entry_message.delete(0, tk.END);
        if not self.message_history or self.message_history[-1] != user_input: self.message_history.append(user_input)
        self.history_index = len(self.message_history); self.process_command(user_input)
        return "break"
    def recall_previous_message(self, event=None):
        if self.message_history and self.history_index > 0: self.history_index -= 1; previous_message = self.message_history[self.history_index]; self.entry_message.delete(0, tk.END); self.entry_message.insert(0, previous_message); self.entry_message.icursor(tk.END)
        return "break"
    def recall_next_message(self, event=None):
        if self.history_index < len(self.message_history):
            if self.history_index < len(self.message_history) - 1: self.history_index += 1; next_message = self.message_history[self.history_index]; self.entry_message.delete(0, tk.END); self.entry_message.insert(0, next_message)
            else: self.history_index += 1; self.entry_message.delete(0, tk.END)
            self.entry_message.icursor(tk.END)
        return "break"
    def paste_on_right_click(self, event=None):
        try: clipboard_content = self.clipboard_get();
        except tk.TclError: return "break"
        if clipboard_content: insert_pos = self.entry_message.index(tk.INSERT); self.entry_message.insert(insert_pos, clipboard_content)
        return "break"

# --- Chạy ứng dụng ---
if __name__ == "__main__":
    app = ChatApp()
    app.mainloop()