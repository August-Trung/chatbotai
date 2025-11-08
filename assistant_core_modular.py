# -*- coding: utf-8 -*-
import os, threading, queue, datetime as dt
import tkinter as tk
import customtkinter as ctk
import re
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

from typing import Optional
from assistant_logger import setup_logger
from assistant_nlp import NLPProcessor
from assistant_apps import AppManager
from assistant_files import FileManager
from tkinter import messagebox

log = setup_logger("core")


class AssistantApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        self.title("Assistant Core (Modular)")
        self.geometry("920x580")

        self.chat_display = ctk.CTkTextbox(self, wrap="word")
        self.chat_display.pack(fill="both", expand=True, padx=12, pady=(12, 6))

        bottom = ctk.CTkFrame(self)
        bottom.pack(fill="x", padx=12, pady=(0, 12))

        self.entry = ctk.CTkEntry(bottom, placeholder_text="Nhập lệnh...")
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 8), pady=8)
        self.entry.bind("<Return>", self.on_send)

        self.btn_send = ctk.CTkButton(bottom, text="Gửi", command=self.on_send)
        self.btn_send.pack(side="left", padx=(0, 8), pady=8)

        self.btn_reload_nlp = ctk.CTkButton(
            bottom, text="Reload NLP", command=self.reload_nlp
        )
        self.btn_reload_nlp.pack(side="left", padx=(0, 8), pady=8)

        self.status = ctk.CTkLabel(bottom, text="Idle")
        self.status.pack(side="right", padx=6)

        self.nlp = NLPProcessor()
        self.apps = AppManager()
        self.files = FileManager()

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

    def get_weather(self, location: str) -> str:
    # Stub an toàn: sau này tích hợp API thật (OpenWeather,...)
        return "chưa tích hợp API thời tiết (demo)"


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

    def _detect_file_action(self, text: str, entities) -> Optional[str]:
        t = (text or "").lower()
        acts = [e["text"].lower() for e in entities if e.get("label") == "ACTION"]
        hay = " ".join([t] + acts)

        if any(k in hay for k in ["đổi tên", "rename"]):
            return "rename"
        if any(k in hay for k in ["sao chép", "copy"]):
            return "copy"
        if any(k in hay for k in ["xóa", "delete"]):
            return "delete"
        if any(k in hay for k in ["mở", "open"]):
            return "open"
        return None

    def _extract_new_name(self, text: str) -> Optional[str]:
        """
        Trích tên mới từ câu lệnh đổi tên.
        Hỗ trợ cả dạng có và không có từ 'thành':
        - 'đổi tên file a.txt thành b.txt'
        - 'đổi tên file a.txt b.txt'
        """
        text = text.strip()
        m = re.search(r"\bthành[: ]+\s*([^\s]+)", text, flags=re.IGNORECASE)
        if m:
            return m.group(1)

        # nếu không có 'thành', bắt tên file cuối câu
        parts = text.split()
        if len(parts) >= 2:
            last = parts[-1]
            if not m and len(parts) < 3:
                return None
            # lọc bỏ các từ không phải tên hợp lệ
            if "." in last or last.isalpha():
                return last
        return None

    def _extract_destination(self, text: str) -> Optional[str]:
        # lấy thư mục sau "đến" hoặc "vào"
        m = re.search(r"\b(đến|vao|vào)[: ]+\s*([^\s]+)", text, flags=re.IGNORECASE)
        if not m:
            return None
        word = m.group(2).lower()
        home = Path.home()
        mapping = {
            "desktop": home / "Desktop",
            "màn hình": home / "Desktop",
            "documents": home / "Documents",
            "tài liệu": home / "Documents",
            "downloads": home / "Downloads",
            "tải về": home / "Downloads",
        }
        return str(mapping.get(word, home / "Desktop"))

    def process_command(self, command: str):
        self.status.configure(text="Processing...")
        ok, msg = self.nlp.ensure_loaded()
        if msg:
            self._sys_msg(msg)

        analysis = self.nlp.analyze(command)
        intent = (analysis.get("intent") or "").lower()
        entities = analysis.get("entities") or []

        low = command.lower()
        if (not intent) or analysis.get("score", 0) < 0.6:
            if low.startswith(("đóng", "tắt", "thoát")):
                intent = "close_app"
            elif low.startswith(("vào", "truy cập", "mở trang", "đi tới")):
                intent = "open_website"

        log.info(
            "Analysis: intent=%s | entities=%s | text=%s", intent, entities, command
        )

        if intent in {"get_time", "time"}:
            now = dt.datetime.now()
            reply = f"Bây giờ là {now:%H:%M} ngày {now:%d/%m/%Y}."
            self.cmd_q.put(("bot", reply))

        elif intent in {"open_app", "open"}:
            app_name = self.nlp.extract_app(analysis) or command
            ok, msg = self.apps.open_app(app_name)
            self.cmd_q.put(("bot", msg))

        elif intent in {"close_app", "close"}:
            # TODO: nếu bạn đã có hàm close_app trong AppManager, gọi ở đây.
            app_name = self.nlp.extract_app(analysis) or command
            # ví dụ:
            # ok, msg = self.apps.close_app(app_name)
            # self.cmd_q.put(("bot", msg))
            self.cmd_q.put(("bot", f"Tính năng đóng ứng dụng sẽ được bổ sung."))

        elif (
            intent
            in {"find_file", "open_file", "copy_file", "rename_file", "delete_file"}
            or any(e.get("label") == "ACTION" for e in entities)
            or (
                intent == "open_app" and any(e.get("label") == "FILE" for e in entities)
            )
        ):
            # 1) Quyết định hành động trước
            action = self._detect_file_action(command, entities)

            # 2) Ưu tiên keyword từ ENTITY=FILE nếu có
            file_ents = [e["text"] for e in entities if e.get("label") == "FILE"]
            query_for_search = file_ents[0] if file_ents else command

            # 3) Tìm file
            found = self.files.smart_find_from_query(query_for_search)
            if not found:
                self.cmd_q.put(("bot", "Không tìm thấy file nào phù hợp."))
                return

            target = found[0]
            log.info(f"Đã chọn file đầu tiên: {target}")

            # 4) Thực thi theo action
            if action == "open":
                ok, msg = self.files.open_file(target)
                self.cmd_q.put(("bot", msg))
                return

            if action == "delete":
                if not messagebox.askyesno(
                    "Xác nhận", f"Bạn có chắc muốn xóa file:\n{target}?"
                ):
                    self.cmd_q.put(("bot", "Đã hủy xóa file."))
                    return
                ok, msg = self.files.delete_file(target)
                self.cmd_q.put(("bot", msg))
                return

            if action == "copy":
                dest = self._extract_destination(command) or str(
                    Path.home() / "Desktop"
                )
                ok, msg = self.files.copy_file(target, dest)
                self.cmd_q.put(("bot", f"{msg}"))
                return

            if action == "rename":
                new_name = self._extract_new_name(command)
                if not new_name:
                    self.cmd_q.put(
                        (
                            "bot",
                            "Bạn muốn đổi tên file này thành gì? (VD: đổi tên file báo cáo thành bao_cao_moi.docx)",
                        )
                    )
                    return
                ok, msg = self.files.rename_file(target, new_name)
                self.cmd_q.put(("bot", msg))
                return

            # Nếu người dùng chỉ nói "file báo cáo" → hiển thị danh sách để người dùng chọn
            top = "\n".join(f"- {p}" for p in found[:5])
            self.cmd_q.put(
                (
                    "bot",
                    f"Đã tìm thấy {len(found)} kết quả, hiển thị 5 kết quả đầu:\n{top}",
                )
            )
        elif intent == "open_website":
            site = self.nlp.extract_app(analysis) or command.split()[-1]
            site = site.lower().replace(" ", "")
            if not site.startswith("http"):
                url = f"https://www.{site}.com"
            else:
                url = site
            try:
                os.startfile(url)
                self.cmd_q.put(("bot", f"Đang mở {url}"))
            except Exception as e:
                self.cmd_q.put(("bot", f"Không thể mở trang {url}: {e}"))

        elif intent == "get_weather":
            location = next(
                (e["text"] for e in entities if e["label"] in ["LOCATION", "PATH"]),
                "Hà Nội",
            )
            weather = self.get_weather(location)
            self.cmd_q.put(("bot", f"Thời tiết tại {location}: {weather}"))

        else:
            self.cmd_q.put(
                (
                    "bot",
                    f"Mình đã nhận: “{command}”. Bạn muốn mở app, tìm file hay làm gì thêm?",
                )
            )

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
