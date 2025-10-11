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

# Optional imports - will work with or without these libraries
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

try:
    from underthesea import word_tokenize
    UNDERTHESEA_AVAILABLE = True
except ImportError:
    UNDERTHESEA_AVAILABLE = False

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

# Voice imports
try:
    import speech_recognition as sr
    from gtts import gTTS
    from playsound import playsound
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False

# Configure logging
logging.basicConfig(
    filename="chatbot.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)

# Application mappings for command processing
APP_MAPPINGS = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "paint": "mspaint.exe",
    "browser": "start chrome",
    "chrome": "start chrome",
    "firefox": "start firefox",
    "edge": "start msedge",
    "explorer": "explorer.exe",
    "cmd": "cmd.exe",
    "powershell": "powershell.exe",
    "task manager": "taskmgr.exe",
    "control panel": "control.exe",
    "settings": "ms-settings:",
}

ALIAS_MAP = {
    "ghi chú": "notepad",
    "máy tính": "calculator",
    "vẽ": "paint",
    "trình duyệt": "browser",
    "file explorer": "explorer",
    "dòng lệnh": "cmd",
    "quản lý tác vụ": "task manager",
    "bảng điều khiển": "control panel",
    "cài đặt": "settings",
}

class ChatApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Initialize theme first - MUST be done before using _current_theme
        self._current_theme = "Dark"
        ctk.set_appearance_mode(self._current_theme.lower())
        
        # Window configuration
        self.title("ChatBot GUI - Enhanced with Voice (V7.3.1)")
        self.geometry("900x700")
        self.minsize(800, 600)
        
        # Initialize state variables
        self.nlp = None
        self.message_history = []
        self.history_index = 0
        self.message_widgets = []
        self.max_messages = 100
        self.is_recognizing_speech = False
        
        # Configure main layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        
        # Create chat display area
        self.setup_chat_display()
        
        # Create bottom control panel
        self.setup_bottom_panel()
        
        # Load NLP models in background
        if SPACY_AVAILABLE or TRANSFORMERS_AVAILABLE:
            threading.Thread(target=self._load_nlp_models, daemon=True).start()
        
        # Display welcome message
        welcome_msg = "Bot: Chào bạn! Giao diện đã được nâng cấp với NLP (V7.3.1)."
        if VOICE_AVAILABLE:
            welcome_msg += " Sẵn sàng nhận lệnh thoại!"
        else:
            welcome_msg += " (Chức năng thoại không khả dụng - thiếu thư viện)"
        
        self.display_message(welcome_msg, sender="Bot")
    
    def setup_chat_display(self):
        """Setup the scrollable chat display area."""
        self.chat_display_frame = ctk.CTkScrollableFrame(
            self, corner_radius=0, fg_color="transparent"
        )
        self.chat_display_frame.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="nsew")
        self.chat_display_frame.grid_columnconfigure(0, weight=1)
    
    def setup_bottom_panel(self):
        """Setup the bottom control panel with buttons and input."""
        self.bottom_frame = ctk.CTkFrame(
            self, height=75, corner_radius=0, fg_color="transparent", border_width=1,
            border_color=("gray80", "gray25")
        )
        self.bottom_frame.grid(row=1, column=0, padx=0, pady=0, sticky="ew")
        
        # Configure column weights
        self.bottom_frame.grid_columnconfigure(0, weight=0)  # Theme button
        self.bottom_frame.grid_columnconfigure(1, weight=0)  # Mic button
        self.bottom_frame.grid_columnconfigure(2, weight=1)  # Entry message
        self.bottom_frame.grid_columnconfigure(3, weight=0)  # Send button
        self.bottom_frame.grid_columnconfigure(4, weight=0)  # Show more button
        self.bottom_frame.grid_columnconfigure(5, weight=0)  # Clear history button
        
        # Color schemes
        initial_text_color = ("#333333", "#FFFFFF")
        initial_fg_color = ("#F0F0F0", "#2C2C2E")
        
        # Theme toggle button
        self.theme_button = ctk.CTkButton(
            self.bottom_frame,
            text="💡" if self._current_theme == "Dark" else "🌙",
            width=40, height=40, command=self.toggle_theme, font=("Segoe UI Emoji", 18),
            text_color=initial_text_color[0] if self._current_theme == "Light" else initial_text_color[1],
            fg_color=initial_fg_color[0] if self._current_theme == "Light" else initial_fg_color[1],
            hover_color=("#4A90E2", "#E5E5E5"), corner_radius=10
        )
        self.theme_button.grid(row=0, column=0, padx=(15, 5), pady=15)
        
        # Microphone button
        mic_text = "🎤" if VOICE_AVAILABLE else "🚫"
        self.mic_button = ctk.CTkButton(
            self.bottom_frame,
            text=mic_text,
            width=40, height=40,
            command=self.start_voice_input_thread if VOICE_AVAILABLE else None,
            font=("Segoe UI Emoji", 18),
            text_color=initial_text_color[0] if self._current_theme == "Light" else initial_text_color[1],
            fg_color=initial_fg_color[0] if self._current_theme == "Light" else initial_fg_color[1],
            hover_color=("#4A90E2", "#E5E5E5") if VOICE_AVAILABLE else ("gray70", "gray40"),
            corner_radius=10,
            state="normal" if VOICE_AVAILABLE else "disabled"
        )
        self.mic_button.grid(row=0, column=1, padx=(0, 10), pady=15)
        
        # Message input field
        placeholder = "Nhập tin nhắn" + (" hoặc nhấn 🎤" if VOICE_AVAILABLE else "")
        self.entry_message = ctk.CTkEntry(
            self.bottom_frame, placeholder_text=placeholder,
            font=("Segoe UI", 15), height=40, border_width=1,
            fg_color=("white", "gray25"), corner_radius=15,
            border_color=("#D3D3D3", "#555555")
        )
        self.entry_message.grid(row=0, column=2, padx=0, pady=15, sticky="ew")
        self.entry_message.bind("<Return>", self.send_message_event)
        self.entry_message.bind("<Up>", self.navigate_history)
        self.entry_message.bind("<Down>", self.navigate_history)
        
        # Send button
        self.send_button = ctk.CTkButton(
            self.bottom_frame, text="Gửi", width=80, height=40, command=self.send_message_event,
            font=("Segoe UI", 15, "bold"), corner_radius=15,
            fg_color=("#4A90E2", "#1E90FF"), hover_color=("#4682B4", "#87CEFA")
        )
        self.send_button.grid(row=0, column=3, padx=(10, 5), pady=15)
        
        # Show more button (initially hidden)
        self.show_more_button = ctk.CTkButton(
            self.bottom_frame, text="Xem thêm", width=100, height=40,
            command=self._on_show_more_button_click, font=("Segoe UI", 15, "bold"),
            text_color_disabled="gray60", corner_radius=15, fg_color=("#4A90E2", "#1E90FF")
        )
        self.show_more_button_grid_info = {"row": 0, "column": 4, "padx": (0, 5), "pady": 15, "sticky": "e"}
        self.show_more_button.grid_remove()
        
        # Clear entry button
        self.clear_button = ctk.CTkButton(
            self.bottom_frame, text="✖", width=30, height=30, font=("Segoe UI", 12),
            corner_radius=0, command=lambda: self.entry_message.delete(0, tk.END),
            fg_color=("white", "gray25"), text_color=("gray50", "gray60"),
        )
        self.clear_button.grid(row=0, column=2, padx=(0, 10), pady=15, sticky="e")
        
        # Clear history button
        self.clear_history_button = ctk.CTkButton(
            self.bottom_frame, text="Xóa lịch sử", width=100, height=40, command=self.clear_chat_history,
            font=("Segoe UI", 15, "bold"), corner_radius=15,
            fg_color=("#FF4040", "#FF6666"), hover_color=("#CC3333", "#FF9999")
        )
        self.clear_history_button.grid(row=0, column=5, padx=(0, 15), pady=15)
    
    def toggle_theme(self):
        """Toggle between light and dark themes."""
        try:
            if self._current_theme == "Dark":
                self._current_theme = "Light"
                ctk.set_appearance_mode("light")
                self.theme_button.configure(text="🌙", text_color="#333333", fg_color="#F0F0F0")
                if VOICE_AVAILABLE:
                    self.mic_button.configure(text_color="#333333", fg_color="#F0F0F0")
            else:
                self._current_theme = "Dark"
                ctk.set_appearance_mode("dark")
                self.theme_button.configure(text="💡", text_color="#FFFFFF", fg_color="#2C2C2E")
                if VOICE_AVAILABLE:
                    self.mic_button.configure(text_color="#FFFFFF", fg_color="#2C2C2E")
            
            log.info(f"Theme switched to: {self._current_theme}")
            
        except Exception as e:
            log.error(f"Error toggling theme: {e}", exc_info=True)
    
    def navigate_history(self, event):
        """Navigate through message history with Up/Down arrows."""
        try:
            if event.keysym == "Up" and self.history_index > 0:
                self.history_index -= 1
                self.entry_message.delete(0, tk.END)
                if self.history_index < len(self.message_history):
                    self.entry_message.insert(0, self.message_history[self.history_index])
            elif event.keysym == "Down" and self.history_index < len(self.message_history):
                self.history_index += 1
                self.entry_message.delete(0, tk.END)
                if self.history_index < len(self.message_history):
                    self.entry_message.insert(0, self.message_history[self.history_index])
        except Exception as e:
            log.error(f"Error navigating history: {e}")
    
    def _on_show_more_button_click(self):
        """Handle show more button click."""
        self.display_message("Bot: Chức năng 'Xem thêm' sẽ được phát triển trong tương lai.", sender="Bot")
    
    def clear_chat_history(self):
        """Clear the chat history display."""
        try:
            for widget in self.message_widgets:
                widget.destroy()
            self.message_widgets.clear()
            self.display_message("Bot: Lịch sử chat đã được xóa.", sender="Bot")
            log.info("Chat history cleared")
        except Exception as e:
            log.error(f"Error clearing chat history: {e}")
    
    def _load_nlp_models(self):
        """Load NLP models in background thread."""
        try:
            log.info("Loading NLP models...")
            
            if SPACY_AVAILABLE:
                try:
                    # Try to load Vietnamese spaCy model
                    import spacy
                    self.nlp = spacy.load("vi_core_news_sm")
                    log.info("Vietnamese spaCy model loaded successfully")
                except OSError:
                    log.warning("Vietnamese spaCy model not found. Using English model as fallback.")
                    try:
                        self.nlp = spacy.load("en_core_web_sm")
                        log.info("English spaCy model loaded successfully")
                    except OSError:
                        log.warning("No spaCy models found")
            
            if TRANSFORMERS_AVAILABLE:
                try:
                    # You can initialize transformers models here
                    log.info("Transformers library available")
                except Exception as e:
                    log.warning(f"Error initializing transformers: {e}")
            
            log.info("NLP initialization completed")
            
        except Exception as e:
            log.error(f"Error loading NLP models: {e}")
    
    def display_message(self, message, sender="User", speak_this_message=True):
        """Display a message in the chat area and optionally speak it."""
        if threading.current_thread() is not threading.main_thread():
            log.warning(f"display_message called from non-main thread ({threading.current_thread().name}). Scheduling on main thread.")
            self.after(0, self.display_message, message, sender, speak_this_message)
            return
        
        try:
            # Remove oldest messages if limit exceeded
            if len(self.message_widgets) >= self.max_messages:
                oldest_widget = self.message_widgets.pop(0)
                oldest_widget.destroy()
            
            # Create message frame
            frame = ctk.CTkFrame(self.chat_display_frame, fg_color=("gray95", "gray20"), corner_radius=10)
            
            # Configure frame based on sender
            if sender == "User":
                frame.grid(row=len(self.message_widgets), column=0, padx=(50, 10), pady=5, sticky="e")
                text_color = ("#2E86C1", "#5DADE2")
            else:  # Bot
                frame.grid(row=len(self.message_widgets), column=0, padx=(10, 50), pady=5, sticky="w")
                text_color = ("#28B463", "#58D68D")
            
            # Create message label
            label = ctk.CTkLabel(
                frame,
                text=message,
                font=("Segoe UI", 14),
                text_color=text_color,
                wraplength=400,
                justify="left"
            )
            label.grid(row=0, column=0, padx=10, pady=8, sticky="w")
            
            self.message_widgets.append(frame)
            self.update_idletasks()
            
            # Scroll to bottom
            self.chat_display_frame._parent_canvas.yview_moveto(1.0)
            
            # Text-to-speech for bot messages
            if sender == "Bot" and speak_this_message and VOICE_AVAILABLE:
                text_for_speech = message
                if message.startswith("Bot: "):
                    text_for_speech = message[len("Bot: "):]
                self.speak(text_for_speech)
                
        except Exception as e:
            log.error(f"Error displaying message: {e}", exc_info=True)
    
    def send_message_event(self, event=None):
        """Handle sending a message."""
        message = self.entry_message.get().strip()
        if message:
            # Add to history
            if not self.message_history or self.message_history[-1] != message:
                self.message_history.append(message)
            self.history_index = len(self.message_history)
            
            # Display user message
            self.display_message(message, sender="User", speak_this_message=False)
            self.entry_message.delete(0, tk.END)
            
            # Process command in background thread
            threading.Thread(target=self.process_command, args=(message,), daemon=True).start()
    
    def process_command(self, message):
        """Process user command and generate response."""
        try:
            message_lower = message.lower().strip()
            
            # Check for app launch commands
            app_launched = self.try_launch_application(message_lower)
            if app_launched:
                return
            
            # Check for web search
            if any(keyword in message_lower for keyword in ["tìm kiếm", "search", "google", "tra cứu"]):
                self.handle_web_search(message)
                return
            
            # Check for system commands
            if any(keyword in message_lower for keyword in ["mở", "open", "khởi động", "chạy"]):
                self.handle_system_command(message_lower)
                return
            
            # Default chatbot response
            self.generate_chatbot_response(message)
            
        except Exception as e:
            log.error(f"Error processing command: {e}", exc_info=True)
            error_response = f"Bot: Xin lỗi, có lỗi xảy ra khi xử lý lệnh của bạn: {e}"
            self.after(0, self.display_message, error_response, "Bot")
    
    def try_launch_application(self, message_lower):
        """Try to launch an application based on the message."""
        try:
            # Check direct mappings
            for app_name, command in APP_MAPPINGS.items():
                if app_name in message_lower:
                    subprocess.Popen(command, shell=True)
                    response = f"Bot: Đã mở {app_name}."
                    self.after(0, self.display_message, response, "Bot")
                    return True
            
            # Check aliases
            for alias, app_name in ALIAS_MAP.items():
                if alias in message_lower and app_name in APP_MAPPINGS:
                    subprocess.Popen(APP_MAPPINGS[app_name], shell=True)
                    response = f"Bot: Đã mở {alias}."
                    self.after(0, self.display_message, response, "Bot")
                    return True
            
            return False
            
        except Exception as e:
            log.error(f"Error launching application: {e}")
            return False
    
    def handle_web_search(self, message):
        """Handle web search requests."""
        try:
            # Extract search query
            search_terms = ["tìm kiếm", "search", "google", "tra cứu"]
            query = message
            for term in search_terms:
                if term in message.lower():
                    query = message.lower().replace(term, "").strip()
                    break
            
            if query:
                search_url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
                webbrowser.open(search_url)
                response = f"Bot: Đã mở tìm kiếm Google cho: {query}"
            else:
                response = "Bot: Vui lòng cung cấp từ khóa tìm kiếm."
            
            self.after(0, self.display_message, response, "Bot")
            
        except Exception as e:
            log.error(f"Error handling web search: {e}")
            self.after(0, self.display_message, "Bot: Lỗi khi thực hiện tìm kiếm.", "Bot")
    
    def handle_system_command(self, message_lower):
        """Handle system-level commands."""
        try:
            if "thư mục" in message_lower or "folder" in message_lower:
                subprocess.Popen("explorer.exe")
                response = "Bot: Đã mở File Explorer."
            elif "website" in message_lower or "web" in message_lower:
                webbrowser.open("https://www.google.com")
                response = "Bot: Đã mở trình duyệt web."
            else:
                response = "Bot: Không hiểu lệnh hệ thống này."
            
            self.after(0, self.display_message, response, "Bot")
            
        except Exception as e:
            log.error(f"Error handling system command: {e}")
            self.after(0, self.display_message, "Bot: Lỗi khi thực hiện lệnh hệ thống.", "Bot")
    
    def generate_chatbot_response(self, message):
        """Generate a chatbot response using available NLP tools."""
        try:
            # Simple rule-based responses
            message_lower = message.lower()
            
            greetings = ["xin chào", "chào", "hello", "hi", "chào bạn"]
            farewells = ["tạm biệt", "bye", "goodbye", "chào tạm biệt"]
            thanks = ["cảm ơn", "thank you", "thanks", "cám ơn"]
            
            if any(greeting in message_lower for greeting in greetings):
                response = "Bot: Xin chào! Tôi có thể giúp gì cho bạn?"
            elif any(farewell in message_lower for farewell in farewells):
                response = "Bot: Tạm biệt! Hẹn gặp lại bạn!"
            elif any(thank in message_lower for thank in thanks):
                response = "Bot: Không có gì! Tôi luôn sẵn sàng giúp đỡ bạn."
            elif "bạn là ai" in message_lower or "you are" in message_lower:
                response = "Bot: Tôi là trợ lý ảo được tạo để giúp đỡ bạn với các tác vụ hàng ngày."
            elif "giúp" in message_lower or "help" in message_lower:
                response = ("Bot: Tôi có thể giúp bạn:\n"
                           "- Mở các ứng dụng (notepad, calculator, paint, browser)\n"
                           "- Tìm kiếm trên Google\n"
                           "- Trò chuyện đơn giản\n"
                           "- Nhận lệnh thoại (nếu có mic)")
            else:
                # Use NLP if available
                if self.nlp and SPACY_AVAILABLE:
                    response = self.generate_nlp_response(message)
                else:
                    response = f"Bot: Tôi hiểu bạn nói '{message}'. Tôi đang học cách trả lời tốt hơn!"
            
            self.after(0, self.display_message, response, "Bot")
            
        except Exception as e:
            log.error(f"Error generating chatbot response: {e}")
            self.after(0, self.display_message, "Bot: Xin lỗi, tôi gặp khó khăn trong việc hiểu câu hỏi của bạn.", "Bot")
    
    def generate_nlp_response(self, message):
        """Generate response using NLP models."""
        try:
            if self.nlp:
                doc = self.nlp(message)
                
                # Extract entities
                entities = [(ent.text, ent.label_) for ent in doc.ents]
                
                if entities:
                    entity_info = ", ".join([f"{text} ({label})" for text, label in entities])
                    return f"Bot: Tôi nhận ra các thực thể trong câu của bạn: {entity_info}"
                else:
                    return f"Bot: Tôi đã phân tích câu của bạn bằng NLP. Bạn có thể hỏi tôi điều gì khác?"
            
            return "Bot: Tôi đang xử lý thông tin của bạn..."
            
        except Exception as e:
            log.error(f"Error in NLP response generation: {e}")
            return "Bot: Có lỗi trong quá trình xử lý ngôn ngữ tự nhiên."
    
    # Voice-related methods
    def speak(self, message_text):
        """Convert text to speech."""
        if not VOICE_AVAILABLE:
            return
        
        threading.Thread(target=self._speak_thread_target, args=(message_text,), daemon=True).start()
    
    def _speak_thread_target(self, text_to_speak):
        """Text-to-speech thread target."""
        try:
            log.info(f"TTS: Attempting to speak: {text_to_speak[:50]}...")
            tts = gTTS(text=text_to_speak, lang='vi', slow=False)
            temp_audio_file = "temp_bot_response.mp3"
            tts.save(temp_audio_file)
            playsound(temp_audio_file)
            
            # Clean up
            try:
                os.remove(temp_audio_file)
            except:
                pass
                
            log.info("TTS: Playback complete.")
            
        except Exception as e:
            log.error(f"TTS Error: {e}", exc_info=True)
            self.after(0, self.display_message, f"Bot: Lỗi TTS: {e}", "Bot", speak_this_message=False)
    
    def start_voice_input_thread(self):
        """Start voice input in a separate thread."""
        if not VOICE_AVAILABLE:
            self.display_message("Bot: Chức năng thoại không khả dụng. Vui lòng cài đặt: speech_recognition, gtts, playsound", "Bot")
            return
        
        if not self.is_recognizing_speech:
            self.is_recognizing_speech = True
            threading.Thread(target=self._recognize_speech_thread_target, daemon=True).start()
        else:
            log.info("STT: Recognition already in progress.")
    
    def _recognize_speech_thread_target(self):
        """Speech recognition thread target."""
        recognizer = sr.Recognizer()
        
        try:
            with sr.Microphone() as source:
                self.after(0, self.mic_button.configure, {"text": "🎙️...", "state": "disabled"})
                self.after(0, self.display_message, "Bot: Đang nghe...", "Bot", True)
                
                # Adjust for ambient noise
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                log.info("STT: Listening for voice input...")
                
                try:
                    audio = recognizer.listen(source, timeout=7, phrase_time_limit=15)
                except sr.WaitTimeoutError:
                    log.warning("STT: No speech detected within timeout.")
                    self.after(0, self.display_message, "Bot: Không nhận được tín hiệu.", "Bot", True)
                    return
                
                # Process speech
                self.after(0, self.display_message, "Bot: Đang nhận dạng...", "Bot", False)
                recognized_text = recognizer.recognize_google(audio, language="vi-VN")
                log.info(f"STT: Recognized: {recognized_text}")
                
                # Update UI with recognized text
                def update_entry_and_send():
                    self.entry_message.delete(0, tk.END)
                    self.entry_message.insert(0, recognized_text)
                    self.send_message_event()
                
                self.after(0, update_entry_and_send)
                
        except sr.UnknownValueError:
            log.warning("STT: Could not understand audio.")
            self.after(0, self.display_message, "Bot: Xin lỗi, tôi không hiểu bạn nói gì.", "Bot", True)
        except sr.RequestError as e:
            log.error(f"STT: Request error: {e}")
            self.after(0, self.display_message, f"Bot: Lỗi dịch vụ nhận dạng: {e}", "Bot", True)
        except Exception as e:
            log.error(f"STT: Unexpected error: {e}", exc_info=True)
            self.after(0, self.display_message, f"Bot: Lỗi STT: {e}", "Bot", True)
        finally:
            self.is_recognizing_speech = False
            self.after(0, self.mic_button.configure, {"text": "🎤", "state": "normal"})


def main():
    """Main application entry point."""
    try:
        # Set up Windows console encoding if needed
        if platform.system() == "Windows":
            try:
                # This might help with Unicode display in Windows console
                os.system("chcp 65001 > nul")
            except:
                pass
        
        # Create and run the application
        app = ChatApp()
        app.mainloop()
        
    except Exception as e:
        print(f"Error starting application: {e}")
        log.error(f"Fatal error: {e}", exc_info=True)


if __name__ == "__main__":
    main()