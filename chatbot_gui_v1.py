# -*- coding: utf-8 -*-
import customtkinter as ctk
import tkinter as tk
import subprocess
import os
import platform
import webbrowser
import urllib.parse
# import threading # Đã bỏ threading
# import time      # Đã bỏ time

# --- Cài đặt Giao diện ---
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# --- Ánh xạ tên gọi thân thiện sang lệnh thực thi ---
# (Giữ nguyên APP_MAPPINGS từ V4.6.1)
APP_MAPPINGS = { "notepad": {"open_cmd": "notepad.exe", "process_name": "notepad.exe"}, "edge": {"open_cmd": "start msedge", "process_name": "msedge.exe"}, "chrome": {"open_cmd": "start chrome", "process_name": "chrome.exe"}, "firefox": {"open_cmd": "start firefox", "process_name": "firefox.exe"}, "cmd": {"open_cmd": "start cmd.exe" if platform.system() == "Windows" else "gnome-terminal", "process_name": "cmd.exe"}, "terminal": {"open_cmd": "start wt.exe" if platform.system() == "Windows" else "gnome-terminal", "process_name": "WindowsTerminal.exe" if platform.system() == "Windows" else "gnome-terminal-"}, "calculator": {"open_cmd": "calc.exe", "process_name": "CalculatorApp.exe"}, "explorer": {"open_cmd": "explorer.exe", "process_name": "explorer.exe"}, "google": {"open_cmd": "start chrome https://www.google.com", "process_name": "chrome.exe"}, "youtube": {"open_cmd": "start chrome https://www.youtube.com", "process_name": "chrome.exe"}, "facebook": {"open_cmd": "start chrome https://www.facebook.com", "process_name": "chrome.exe"}, "gemini": {"open_cmd": "start chrome https://gemini.google.com/app", "process_name": "chrome.exe"}, "chatgpt": {"open_cmd": "start chrome https://chatgpt.com/", "process_name": "chrome.exe"}, }

# (Giữ nguyên ALIAS_MAP, WEBSITE_ALIASES từ V4.6.1)
ALIAS_MAP = { "note": "notepad", "me": "edge", "gg": "google", "ytb": "youtube", "yt": "youtube", "cal": "calculator", "exp": "explorer", "fb": "facebook", "face": "facebook", "gem": "gemini", "gemini": "gemini", "gpt": "chatgpt", }
WEBSITE_ALIASES = {"google", "youtube", "facebook", "gg", "ytb", "yt", "fb", "face", "gem", "gemini", "gpt", "chatgpt"}
KW_BASE_OPEN = ("mở", "khởi động"); KW_BASE_CLOSE = ("đóng", "tắt"); KW_BASE_WEB_SEARCH = ("truy cập", "vào web", "mở web", "mở trang", "tìm kiếm", "search", "tìm", "vào", "tìm nhạc")
KW_SPACED_OPEN = tuple(kw + " " for kw in KW_BASE_OPEN); KW_SPACED_CLOSE = tuple(kw + " " for kw in KW_BASE_CLOSE); KW_SPACED_WEB_SEARCH = tuple(kw + " " for kw in KW_BASE_WEB_SEARCH)
PREPOSITIONS = (" trong ", " bằng ", " trên ")

class ChatApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Trợ lý AI Desktop - V5.4.1") # Đổi tên version
        # === V5.4.1: Bỏ các thuộc tính không cần thiết ===
        # self.web_thread = None
        # ... (rest of __init__ GUI setup) ...
        self.geometry("750x600"); self._current_theme = ctk.get_appearance_mode(); self.message_history = []; self.history_index = 0
        self.grid_columnconfigure(0, weight=1); self.grid_rowconfigure(0, weight=1); self.grid_rowconfigure(1, weight=0)
        self.chat_display_frame = ctk.CTkScrollableFrame(self, label_text="Lịch sử Chat", label_font=("Segoe UI", 11, "italic"), fg_color="transparent")
        self.chat_display_frame.grid(row=0, column=0, padx=10, pady=(0, 5), sticky="nsew"); self.chat_display_frame.grid_columnconfigure(0, weight=1)
        self.bottom_frame = ctk.CTkFrame(self, height=60, corner_radius=0, fg_color="transparent")
        self.bottom_frame.grid(row=1, column=0, padx=0, pady=(5, 10), sticky="ew"); self.bottom_frame.grid_columnconfigure(0, weight=0); self.bottom_frame.grid_columnconfigure(1, weight=1); self.bottom_frame.grid_columnconfigure(2, weight=0)
        self.theme_button = ctk.CTkButton(self.bottom_frame, text="💡" if self._current_theme == "Dark" else "🌙", width=40, command=self.toggle_theme, font=("Segoe UI Emoji", 16))
        self.theme_button.grid(row=0, column=0, padx=(10, 5), pady=10)
        self.entry_message = ctk.CTkEntry(self.bottom_frame, placeholder_text="Nhập lệnh của bạn...", font=("Segoe UI", 14))
        self.entry_message.grid(row=0, column=1, padx=5, pady=10, sticky="ew"); self.entry_message.bind("<Return>", self.send_message_event); self.entry_message.bind("<Up>", self.recall_previous_message); self.entry_message.bind("<Down>", self.recall_next_message); self.entry_message.bind("<Button-3>", self.paste_on_right_click)
        self.send_button = ctk.CTkButton(self.bottom_frame, text="Gửi", width=80, command=self.send_message_event, font=("Segoe UI", 14, "bold"))
        self.send_button.grid(row=0, column=2, padx=(5, 10), pady=10, sticky="e")
        self.display_message("Bot: Đã cập nhật V5.4.1", sender="Bot") # Đổi message
        # === V5.4.1: Bỏ protocol ===
        # self.protocol("WM_DELETE_WINDOW", self.on_closing)


    # --- HÀM XỬ LÝ LỆNH CHÍNH (V5.4.1 - Bỏ threading cho web) ---
    def process_command(self, command):
        """Phân tích và thực thi lệnh của người dùng."""
        command_lower = command.lower()
        response = f"Xin lỗi, tôi chưa hiểu lệnh: '{command}'"
        executed = False

        # --- Helper ---
        def get_target_from_command(cmd_lower_full, kw_spaced_tuple):
            for kw in kw_spaced_tuple:
                if cmd_lower_full.startswith(kw): return command[len(kw):].strip()
            return None

        # 1. Lệnh đơn
        if command_lower in KW_BASE_OPEN: response = "Bạn muốn mở ứng dụng/web nào?"; executed = True
        elif command_lower in KW_BASE_CLOSE: response = "Bạn muốn đóng ứng dụng nào?"; executed = True
        elif command_lower in KW_BASE_WEB_SEARCH:
            if command_lower == "tìm nhạc": response = "Bạn muốn tìm bài nhạc nào?"
            else: response = "Bạn muốn truy cập web nào hoặc tìm kiếm gì?"
            executed = True

        # Xử lý lệnh có target
        if not executed:
            # 2. Lệnh Đóng
            target_close = get_target_from_command(command_lower, KW_SPACED_CLOSE)
            if target_close is not None: executed = True; response = self._handle_close_app(target_close)

        if not executed:
            # 3. Lệnh Tìm Nhạc (Dùng lại _handle_open_website)
            song_target_full = get_target_from_command(command_lower, ("tìm nhạc ",))
            if song_target_full is not None:
                executed = True
                song_title = song_target_full; browser_key = None; search_on_google = False; browser_specified = False
                # Tách browser (nếu có)
                temp_target = song_target_full
                for prep in PREPOSITIONS:
                    if prep in song_target_full.lower():
                        parts = song_target_full.rsplit(prep, 1);
                        if len(parts) == 2: browser_specified = True; target_part, browser_part = parts; potential_browser_key = browser_part.strip().lower(); temp_target = target_part.strip(); canonical_browser_key = ALIAS_MAP.get(potential_browser_key, potential_browser_key);
                        if canonical_browser_key in APP_MAPPINGS or canonical_browser_key == "google": search_on_google = True;
                        if canonical_browser_key in APP_MAPPINGS: browser_key = canonical_browser_key;
                        break
                song_title = temp_target
                # Check explicit google request
                if not search_on_google:
                    if " trên google" in song_title.lower(): search_on_google = True; song_title = song_title.lower().replace(" trên google", "").strip()
                    elif song_title.lower().endswith(" google"): search_on_google = True; song_title = song_title.rsplit(' ', 1)[0].strip()
                if not song_title: response = "Bạn muốn tìm bài nhạc nào?"
                else:
                    final_url = ""
                    if search_on_google:
                        try: search_query = urllib.parse.quote_plus(song_title); final_url = f"https://www.google.com/search?q={search_query}"
                        except Exception as e: response = f"Lỗi tạo URL Google: {e}"; final_url=None
                    else: # Tìm YouTube
                        try: search_query = urllib.parse.quote_plus(song_title); final_url = f"https://www.youtube.com/results?search_query={search_query}"
                        except Exception as e: response = f"Lỗi tạo URL YouTube: {e}"; final_url=None
                    # Gọi hàm mở web thông thường (chạy trực tiếp)
                    if final_url:
                         response = self._handle_open_website(final_url, browser_key)
                    # else: response đã được gán lỗi

        if not executed:
            # 4. Lệnh Web/Search Chung (Trừ 'tìm nhạc')
            web_search_keywords_no_music = tuple(kw for kw in KW_SPACED_WEB_SEARCH if kw != "tìm nhạc ")
            target_web = get_target_from_command(command_lower, web_search_keywords_no_music)
            if target_web is not None:
                executed = True; browser_key = None; target_to_use = target_web; browser_specified = False
                for prep in PREPOSITIONS:
                     if prep in target_web.lower():
                         parts = target_web.rsplit(prep, 1);
                         if len(parts) == 2: browser_specified=True; target_part, browser_part = parts; potential_browser_key = browser_part.strip().lower(); target_to_use = target_part.strip(); canonical_browser_key = ALIAS_MAP.get(potential_browser_key, potential_browser_key);
                         if canonical_browser_key in APP_MAPPINGS: browser_key = canonical_browser_key;
                         break
                # Gọi trực tiếp, không cần thread
                response = self._handle_open_website(target_to_use, browser_key=browser_key)

        if not executed:
            # 5. Lệnh MỞ CHUNG CHUNG
            target_open = get_target_from_command(command_lower, KW_SPACED_OPEN)
            if target_open is not None:
                executed = True; browser_key = None; target_to_use = target_open; browser_specified = False
                for prep in PREPOSITIONS:
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
                    # Gọi trực tiếp, không cần thread
                    response = self._handle_open_website(final_target_for_web, browser_key=browser_key)
                else: # Mở app vẫn chạy trực tiếp
                    response = self._handle_open_app(target_to_use)


        # Hiển thị phản hồi của Bot
        if response:
             self.display_message(f"Bot: {response}", sender="Bot")

    # === V5.4: Bỏ hàm thread ===
    # def _handle_open_website_thread(self, target, browser_key): ...

    # --- Các hàm cũ (_handle_open_website, _handle_open_app, _handle_close_app) ---
    # (Giữ nguyên các hàm này)
    def _handle_open_website(self, target, browser_key=None):
        print(f"--- Debug _handle_open_website (Non-Selenium) ---"); print(f"Input Target: '{target}'"); print(f"Input Browser Key: '{browser_key}'"); final_url = ""; is_search = False
        try:
            target_cleaned = target.strip();
            if not target_cleaned: return "Lỗi: Không có URL hoặc nội dung tìm kiếm được cung cấp."
            if target_cleaned.startswith("https://www.youtube.com/results?search_query="): is_search = False; final_url = target_cleaned; print(f"Result: Determined as pre-made YouTube Search URL -> '{final_url}'")
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


    # --- Các hàm giao diện còn lại (Giữ nguyên) ---
    def toggle_theme(self): new_mode = "Light" if self._current_theme == "Dark" else "Dark"; ctk.set_appearance_mode(new_mode); self._current_theme = new_mode; self.theme_button.configure(text="💡" if new_mode == "Dark" else "🌙")
    def display_message(self, message, sender):
        if sender == "User": anchor_side = "e"; justify_text = "right"; bubble_color = ctk.ThemeManager.theme["CTkButton"]["fg_color"]; text_color = ctk.ThemeManager.theme["CTkButton"]["text_color"]
        else: anchor_side = "w"; justify_text = "left"; bubble_color = ctk.ThemeManager.theme["CTkFrame"]["fg_color"]; text_color = ctk.ThemeManager.theme["CTkLabel"]["text_color"]
        bubble_frame = ctk.CTkFrame(self.chat_display_frame, fg_color=bubble_color, corner_radius=15)
        try: scrollable_width = self.chat_display_frame.winfo_width() - 30
        except Exception: scrollable_width = 300
        if scrollable_width < 100: scrollable_width = 300
        wraplength = scrollable_width * 0.7
        message_label = ctk.CTkLabel(bubble_frame, text=message, font=("Segoe UI", 14), text_color=text_color, justify=justify_text, wraplength=wraplength); message_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        bubble_frame.grid(row=self.chat_display_frame.grid_size()[1], column=0, padx=10, pady=(5, 2), sticky=anchor_side); self.after(50, self._scroll_to_bottom)
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