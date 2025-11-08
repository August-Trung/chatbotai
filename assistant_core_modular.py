
# -*- coding: utf-8 -*-
import os, threading, queue, datetime as dt
import tkinter as tk
import customtkinter as ctk

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from assistant_logger import setup_logger
from assistant_nlp import NLPProcessor
from assistant_apps import AppManager

log = setup_logger("core")

class AssistantApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        self.title("Assistant Core (Modular)")
        self.geometry("920x580")

        self.chat_display = ctk.CTkTextbox(self, wrap="word")
        self.chat_display.pack(fill="both", expand=True, padx=12, pady=(12,6))

        bottom = ctk.CTkFrame(self)
        bottom.pack(fill="x", padx=12, pady=(0,12))

        self.entry = ctk.CTkEntry(bottom, placeholder_text="Nhập lệnh...")
        self.entry.pack(side="left", fill="x", expand=True, padx=(0,8), pady=8)
        self.entry.bind("<Return>", self.on_send)

        self.btn_send = ctk.CTkButton(bottom, text="Gửi", command=self.on_send)
        self.btn_send.pack(side="left", padx=(0,8), pady=8)

        self.btn_reload_nlp = ctk.CTkButton(bottom, text="Reload NLP", command=self.reload_nlp)
        self.btn_reload_nlp.pack(side="left", padx=(0,8), pady=8)

        self.status = ctk.CTkLabel(bottom, text="Idle")
        self.status.pack(side="right", padx=6)

        self.nlp = NLPProcessor()
        self.apps = AppManager()

        self.cmd_q = queue.Queue()
        self.after(60, self._poll_queue)

        self._sys_msg("Chào bạn! Mình sẵn sàng nhận lệnh.")

    def _append(self, text: str):
        self.chat_display.insert("end", text + "\n")
        self.chat_display.see("end")

    def _user_msg(self, text: str):
        self._append(f"Bạn: {text}")

    def _bot_msg(self, text: str):
        self._append(f"Bot: {text}")

    def _sys_msg(self, text: str):
        self._append(f"[Hệ thống] {text}")

    def on_send(self, event=None):
        txt = self.entry.get().strip()
        if not txt:
            return
        self.entry.delete(0, "end")
        self._user_msg(txt)
        threading.Thread(target=self.process_command, args=(txt,), daemon=True).start()

    def reload_nlp(self):
        ok, msg = self.nlp.ensure_loaded()
        self._bot_msg(msg if msg else ("Đã reload NLP" if ok else "Không thể load NLP"))

    def process_command(self, command: str):
        self.status.configure(text="Processing...")
        ok, msg = self.nlp.ensure_loaded()
        if msg:
            self._sys_msg(msg)
        analysis = self.nlp.analyze(command)

        intent = (analysis.get("intent") or "").lower()
        entities = analysis.get("entities") or []
        log.info("Analysis: intent=%s | entities=%s | text=%s", intent, entities, command)

        if intent in {"get_time", "time"}:
            now = dt.datetime.now()
            reply = f"Bây giờ là {now:%H:%M} ngày {now:%d/%m/%Y}."
            self.cmd_q.put(("bot", reply))
        elif intent in {"open_app", "open"}:
            app_name = self.nlp.extract_app(analysis) or command
            ok, msg = self.apps.open_app(app_name)
            self.cmd_q.put(("bot", msg))
        else:
            self.cmd_q.put(("bot", f"Mình đã nhận: “{command}”. Bạn muốn mở app hay làm gì thêm?"))

        self.status.configure(text="Idle")

    def _poll_queue(self):
        try:
            while True:
                who, payload = self.cmd_q.get_nowait()
                if who == "bot":
                    self._bot_msg(payload)
                else:
                    self._append(str(payload))
        except queue.Empty:
            pass
        self.after(60, self._poll_queue)

if __name__ == "__main__":
    app = AssistantApp()
    app.mainloop()
