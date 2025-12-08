import os, json, subprocess, sys
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from tkinter import Tk, filedialog
from assistant_logger import setup_logger

log = setup_logger("apps")

DEFAULT_ALIASES = {
    "zalo": ["zalo", "ja lo", "za lô", "gia lô"],
    "facebook": ["facebook", "phây búc", "phây", "fb"],
    "chrome": ["chrome", "cờ rôm", "google chrome", "trình duyệt google"],
    "edge": ["edge", "êch", "microsoft edge"],
    "vscode": ["vscode", "code", "visual studio code"],
    "word": ["word", "microsoft word", "winword"],
    "excel": ["excel", "microsoft excel"],
    "powerpoint": ["powerpoint", "ppt", "microsoft powerpoint"],
    "telegram": ["telegram", "tele"],
    "discord": ["discord"],
    "messenger": ["messenger", "mes"],
    "tiktok": ["tiktok", "tik tok", "tíc tóc"],
    "youtube": ["youtube", "you tube", "yútub"],
}

DEFAULT_APPS = {
    "zalo": ["start", "zalo"],
    "facebook": ["start", "chrome", "https://www.facebook.com"],
    "chrome": ["start", "chrome"],
    "edge": ["start", "msedge"],
    "vscode": ["start", "code"],
    "word": ["start", "winword"],
    "excel": ["start", "excel"],
    "powerpoint": ["start", "powerpnt"],
    "telegram": ["start", "telegram"],
    "discord": ["start", "discord"],
    "messenger": ["start", "chrome", "https://www.messenger.com"],
    "tiktok": ["start", "chrome", "https://www.tiktok.com"],
    "youtube": ["start", "chrome", "https://www.youtube.com"],
}


class AppManager:
    def __init__(
        self, apps_json: str = "apps_index.json", alias_json: str = "alias_map.json"
    ):
        self.apps_path = Path(apps_json)
        self.alias_path = Path(alias_json)
        self.alias = self._load_json(self.alias_path, fallback=DEFAULT_ALIASES)
        self.apps = self._load_json(self.apps_path, fallback=DEFAULT_APPS)

    def _load_json(self, path: Path, fallback: Dict) -> Dict:
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    return data
            except Exception as e:
                log.warning("Invalid JSON at %s: %s", path, e)
        return dict(fallback)

    def save(self):
        """Ghi lại danh sách app và alias vào file."""
        try:
            self.apps_path.write_text(
                json.dumps(self.apps, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            self.alias_path.write_text(
                json.dumps(self.alias, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except Exception as e:
            log.error("Lỗi ghi file app index: %s", e)

    def normalize(self, s: str) -> str:
        return (s or "").strip().lower()

    def resolve_app_name(self, text: str) -> Optional[str]:
        """Tìm tên chuẩn hóa của ứng dụng từ alias hoặc text."""
        t = self.normalize(text)
        if t in self.apps:
            return t
        for canon, alist in self.alias.items():
            for a in alist:
                a_norm = self.normalize(a)
                if a_norm in t or t in a_norm:
                    return canon
        for canon in self.apps.keys():
            if canon in t:
                return canon
        return None

    def _ask_user_for_app_path(self, app_name: str) -> Optional[str]:
        """Hiển thị hộp thoại để người dùng chọn file .exe cho ứng dụng mới."""
        try:
            root = Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            file_path = filedialog.askopenfilename(
                title=f"Chọn file .exe cho ứng dụng '{app_name}'",
                filetypes=[("Ứng dụng Windows", "*.exe"), ("Tất cả", "*.*")],
            )
            root.destroy()
            if file_path:
                log.info(f"Người dùng đã chọn đường dẫn cho {app_name}: {file_path}")
            return file_path if file_path else None
        except Exception as e:
            log.error(f"Lỗi khi chọn file cho {app_name}: {e}")
            return None

    def open_app(self, name_or_phrase: str) -> Tuple[bool, str]:
        """Mở ứng dụng. Nếu chưa biết thì hỏi người dùng để học."""
        canon = self.resolve_app_name(name_or_phrase)
        if not canon:
            canon = self.normalize(name_or_phrase)

        cmd = self.apps.get(canon)
        if not cmd:
            log.warning(
                f"Ứng dụng '{canon}' chưa có trong danh sách. Hỏi người dùng chọn file..."
            )
            path = self._ask_user_for_app_path(canon)
            if not path:
                return (
                    False,
                    f"Không tìm thấy hoặc người dùng không chọn ứng dụng '{canon}'.",
                )
            self.apps[canon] = ["start", path]
            self.alias.setdefault(canon, [canon])
            self.save()
            cmd = self.apps[canon]
            log.info(f"Đã thêm mới app '{canon}' vào apps_index.json → {path}")

        try:
            if sys.platform.startswith("win"):
                subprocess.Popen(cmd, shell=True)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", cmd[-1]])
            else:
                subprocess.Popen(cmd)
            return True, f"Đang mở {canon}."
        except Exception as e:
            log.error(f"Lỗi khi mở app '{canon}': {e}")
            return False, f"Lỗi khi mở {canon}: {e}"
