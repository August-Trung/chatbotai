import os
import re
import shutil
import zipfile
import fnmatch
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple
from assistant_logger import setup_logger
from send2trash import send2trash

log = setup_logger("files")


class FileManager:
    def __init__(self):
        """Khởi tạo FileManager."""
        self.default_dirs = [
            str(Path.home() / "Documents"),
            str(Path.home() / "Downloads"),
            str(Path.home() / "Desktop"),
            "D:\\",
            "E:\\",
            "C:\\",
        ]

    # ===============================
    # 🔍 TÌM FILE
    # ===============================
    def find_file(
        self,
        keyword: str,
        search_dirs: Optional[List[str]] = None,
        exts: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Tìm file hoặc thư mục theo từ khóa.
        :param keyword: Tên hoặc từ khóa (VD: "báo cáo", "report.xlsx").
        :param search_dirs: Danh sách thư mục để tìm.
        :param exts: Bộ lọc phần mở rộng (VD: [".docx", ".xlsx"])
        :return: Danh sách đường dẫn tìm thấy.
        """
        keyword = keyword.lower().strip()
        search_dirs = search_dirs or self.default_dirs
        found = []

        log.info(f"Đang tìm file chứa từ khóa: '{keyword}'")

        for base_dir in search_dirs:
            base = Path(base_dir)
            if not base.exists():
                continue
            for root, dirs, files in os.walk(base):
                for name in files + dirs:
                    nlow = name.lower()
                    if keyword in nlow:
                        if not exts or any(nlow.endswith(ext) for ext in exts):
                            path = str(Path(root) / name)
                            found.append(path)
            if found:
                break  # tìm thấy sớm thì dừng luôn

        log.info(f"Tìm thấy {len(found)} kết quả cho '{keyword}'.")
        return found

    # ===============================
    # 📂 MỞ FILE
    # ===============================
    def open_file(self, path: str) -> Tuple[bool, str]:
        """Mở file hoặc thư mục bằng ứng dụng mặc định."""
        path = str(Path(path))
        if not os.path.exists(path):
            return False, f"Không tìm thấy: {path}"

        try:
            log.info(f"Mở file: {path}")
            os.startfile(path)
            return True, f"Đã mở {path}"
        except Exception as e:
            log.error(f"Lỗi mở file: {e}")
            return False, f"Lỗi mở file: {e}"

    # ===============================
    # 📋 SAO CHÉP FILE
    # ===============================
    def copy_file(self, src: str, dest_dir: str) -> Tuple[bool, str]:
        """Sao chép file tới thư mục đích."""
        try:
            src_path = Path(src)
            dest_dir = Path(dest_dir)
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / src_path.name
            shutil.copy2(src_path, dest)
            log.info(f"Đã sao chép {src} -> {dest}")
            return True, f"Đã sao chép đến {dest}"
        except Exception as e:
            log.error(f"Lỗi sao chép: {e}")
            return False, str(e)

    # ===============================
    # ✏️ ĐỔI TÊN FILE
    # ===============================
    def rename_file(self, src: str, new_name: str) -> Tuple[bool, str]:
        """Đổi tên file."""
        try:
            src_path = Path(src)
            new_path = src_path.with_name(new_name)
            src_path.rename(new_path)
            log.info(f"Đã đổi tên {src_path} -> {new_path}")
            return True, f"Đã đổi tên thành {new_name}"
        except Exception as e:
            log.error(f"Lỗi đổi tên: {e}")
            return False, str(e)

    # ===============================
    # ❌ XÓA FILE
    # ===============================


    def delete_file(self, path: str) -> Tuple[bool, str]:
        """Xóa file hoặc thư mục (an toàn, đưa vào thùng rác)."""
        try:
            p = Path(path)
            if not p.exists():
                return False, f"Không tìm thấy {path}"
            send2trash(str(p))
            log.info(f"Đã đưa {path} vào thùng rác")
            return True, f"Đã đưa {p.name} vào thùng rác (bạn có thể khôi phục sau)."
        except Exception as e:
            log.error(f"Lỗi xóa file: {e}")
            return False, str(e)

    # ===============================
    # 📦 NÉN / GIẢI NÉN
    # ===============================
    def compress(
        self, src_path: str, output_path: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Nén file hoặc thư mục thành .zip."""
        try:
            src = Path(src_path)
            output_path = output_path or (str(src) + ".zip")
            log.info(f"Đang nén {src} -> {output_path}")
            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                if src.is_file():
                    zipf.write(src, arcname=src.name)
                else:
                    for root, _, files in os.walk(src):
                        for f in files:
                            full_path = os.path.join(root, f)
                            rel_path = os.path.relpath(full_path, src)
                            zipf.write(full_path, rel_path)
            return True, f"Đã nén thành {output_path}"
        except Exception as e:
            log.error(f"Lỗi nén: {e}")
            return False, str(e)

    def extract(
        self, zip_path: str, dest_dir: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Giải nén file .zip."""
        try:
            dest_dir = dest_dir or str(Path(zip_path).with_suffix(""))
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(dest_dir)
            log.info(f"Đã giải nén {zip_path} vào {dest_dir}")
            return True, f"Đã giải nén vào {dest_dir}"
        except Exception as e:
            log.error(f"Lỗi giải nén: {e}")
            return False, str(e)

    def _map_known_folder(self, name: str) -> Optional[str]:
        name = (name or "").strip().lower()
        home = Path.home()
        mapping = {
            "desktop": home / "Desktop",
            "màn hình": home / "Desktop",
            "documents": home / "Documents",
            "tài liệu": home / "Documents",
            "downloads": home / "Downloads",
            "tải về": home / "Downloads",
            "picture": home / "Pictures",
            "pictures": home / "Pictures",
            "ảnh": home / "Pictures",
            "music": home / "Music",
            "video": home / "Videos",
            "videos": home / "Videos",
        }
        p = mapping.get(name)
        return str(p) if p else None

    def _clean_keyword(self, query: str) -> Tuple[str, Optional[str]]:
        """
        Trả về (keyword, drive_hint) đã được làm sạch.
        - Loại bỏ từ hành động: mở, xóa, sao chép, đổi tên, tìm…
        - Bắt drive: 'ổ D', 'trong ổ E', 'D:\'… -> drive_hint = 'D:\\'
        """
        q = (query or "").strip()

        # Chuẩn hóa dấu sái (như 't́m') -> chỉ bỏ tổ hợp dấu lẻ, giữ chữ cái
        q = re.sub(r"[\u0300-\u036f]", "", q)

        low = q.lower()

        # 1) Bắt drive kiểu 'ổ D' hoặc 'o D'
        m = re.search(r"\bổ\s*([a-z])\b", low)
        drive = None
        if m:
            drive = m.group(1).upper() + ":\\"
        # 2) Bắt drive kiểu 'C:\' / 'D:\'
        m2 = re.search(r"\b([a-zA-Z]):\\", q)
        if m2:
            drive = m2.group(1).upper() + ":\\"

        # 3) Nếu có cụm thư mục “trong thư mục <Tên>”
        #    thì coi <Tên> là thư mục chuẩn (Desktop/Tài liệu/Downloads…)
        folder_hint = None
        m3 = re.search(r"trong\s+(th[uư] m[uu]c|folder)\s+([^\s]+)", low)
        if m3:
            folder_hint = self._map_known_folder(m3.group(2))

        # 4) Bỏ từ dừng/hành động
        stopwords = [
            "mở",
            "xóa",
            "xoa",
            "sao chép",
            "copy",
            "đổi",
            "đổi tên",
            "rename",
            "tìm",
            "tim",
            "file",
            "tập tin",
            "tệp",
            "trong",
            "ở",
            "o",
            "ổ",
            "bằng",
            "thành",
            "đến",
            "vao",
            "vào",
            "to",
        ]
        cleaned = low
        for sw in sorted(stopwords, key=len, reverse=True):
            cleaned = re.sub(rf"\b{re.escape(sw)}\b", " ", cleaned)

        # 5) Ưu tiên bắt cụm "tên có đuôi"
        mext = re.search(r"([^\s]+?\.[a-z0-9]{1,6})", q, flags=re.IGNORECASE)
        if mext:
            kw = mext.group(1)
        else:
            # Không có đuôi -> lấy phần còn lại (loại bỏ khoảng trắng thừa)
            kw = re.sub(r"\s+", " ", cleaned).strip()

        # 6) Nếu từ khóa quá ngắn, fallback về bản gốc q (tránh rỗng)
        if not kw:
            kw = q

        # Drive ưu tiên folder_hint nếu có
        if folder_hint:
            drive = folder_hint

        return kw, drive

    def smart_find_from_query(self, query: str) -> List[str]:
        """
        Phân tích truy vấn tiếng Việt để tìm file 1 cách ổn định.
        - Hiểu 'mở/xóa/sao chép/đổi tên file ...'
        - Bắt drive (ổ C/D/E) và thư mục phổ biến (Desktop, Tài liệu, Downloads)
        - Ưu tiên cụm có đuôi (.txt, .xlsx, .docx, .png…)
        """
        keyword, drive = self._clean_keyword(query)
        search_dirs = [drive] if drive else None

        # Nếu keyword là tên thư mục mặc định, coi như path tìm trong đó
        folder_mapped = self._map_known_folder(keyword)
        if folder_mapped:
            return [folder_mapped]

        return self.find_file(keyword, search_dirs=search_dirs)
