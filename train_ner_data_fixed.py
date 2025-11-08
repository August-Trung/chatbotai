# -*- coding: utf-8 -*-
"""
Sinh dữ liệu NER cho spaCy.
Định dạng: TRAIN_DATA = [
  ("câu ...", {"entities":[(start, end, "LABEL"), ...]}),
  ...
]
LABELS dùng: ACTION, APP, FILE, LOCATION, PERSON, EMAIL, QUERY
"""

import random

random.seed(42)

APPS = [
    "zalo",
    "chrome",
    "word",
    "excel",
    "powerpoint",
    "vscode",
    "telegram",
    "canva",
    "postman",
    "youtube",
    "notepad",
    "paint",
    "explorer",
    "outlook",
]
FILES = [
    "báo cáo.docx",
    "report.xlsx",
    "check.txt",
    "ảnh.png",
    "thuyet_trinh.pptx",
    "Thiết kế chưa có tên.rar",
    "data.zip",
    "README.md",
    "script.py",
]
LOCATIONS = [
    "Desktop",
    "Tài liệu",
    "Documents",
    "Downloads",
    "ổ D",
    "ổ E",
    "Hà Nội",
    "Hồ Chí Minh",
    "Đà Nẵng",
]
PERSONS = ["thầy Trung", "chị Lan", "anh Minh", "bạn Huy"]
EMAILS = ["lan@gmail.com", "minh@company.com", "contact@example.org"]
QUERIES = [
    "thời tiết hôm nay",
    "tin tức công nghệ",
    "Elon Musk",
    "AI mới nhất",
    "bóng đá",
]

ACTIONS_OPEN = ["mở", "khởi chạy", "bật", "chạy"]
ACTIONS_CLOSE = ["đóng", "tắt", "thoát"]
ACTIONS_FILE = ["mở", "xóa", "sao chép", "đổi tên", "nén", "giải nén", "copy", "rename"]


def pack(parts):
    """
    parts: list of tuples (text, label_or_None)
    trả về: (full_text, entities) với offset chính xác
    """
    s = ""
    ents = []
    cursor = 0
    for txt, lab in parts:
        if s and not s.endswith(" "):
            s += " "
            cursor += 1
        start = cursor
        s += txt
        end = cursor + len(txt)
        if lab:
            ents.append((start, end, lab))
        cursor = end
    return s, {"entities": ents}


def gen_app_samples():
    out = []
    for act in ACTIONS_OPEN:
        for app in APPS:
            out.append(pack([(act, "ACTION"), (app, "APP")]))
            out.append(pack([(act, "ACTION"), ("ứng dụng", None), (app, "APP")]))
    for act in ACTIONS_CLOSE:
        for app in APPS:
            out.append(pack([(act, "ACTION"), (app, "APP")]))
    return out


def gen_file_open_delete_copy_rename():
    out = []
    for act in ACTIONS_FILE:
        for f in FILES:
            if act in ["mở", "copy", "rename", "xóa", "sao chép", "đổi tên"]:
                # mở/xóa/sao chép/đổi tên file X
                out.append(pack([(act, "ACTION"), ("file", None), (f, "FILE")]))
                # chỉ tên file
                out.append(pack([(act, "ACTION"), (f, "FILE")]))
    # sao chép đến vị trí
    for dest in LOCATIONS[:6]:  # desktop/docs/downloads/ổ D/E
        out.append(
            pack(
                [
                    ("sao chép", "ACTION"),
                    ("file", None),
                    (FILES[0], "FILE"),
                    ("đến", None),
                    (dest, "LOCATION"),
                ]
            )
        )
        out.append(
            pack(
                [
                    ("copy", "ACTION"),
                    ("file", None),
                    (FILES[1], "FILE"),
                    ("sang", None),
                    (dest, "LOCATION"),
                ]
            )
        )
    # đổi tên có "thành"
    out.append(
        pack(
            [
                ("đổi tên", "ACTION"),
                ("file", None),
                (FILES[2], "FILE"),
                ("thành", None),
                ("check_v2.txt", "FILE"),
            ]
        )
    )
    out.append(
        pack(
            [
                ("rename", "ACTION"),
                ("file", None),
                (FILES[0], "FILE"),
                ("check_v3.docx", "FILE"),
            ]
        )
    )
    return out


def gen_zip_samples():
    out = []
    # nén thư mục (coi tên thư mục như FILE)
    for folder in ["báo_cáo_tháng_11", "tai_lieu_quan_trong", "anh_du_lich"]:
        out.append(pack([("nén", "ACTION"), ("thư mục", None), (folder, "FILE")]))
        out.append(
            pack(
                [
                    ("tạo", "ACTION"),
                    ("file", None),
                    ("zip", None),
                    ("từ", None),
                    ("thư mục", None),
                    (folder, "FILE"),
                ]
            )
        )
    # giải nén file zip/rar
    for z in ["data.zip", "anh.zip", "tai_lieu.zip", "Thiết kế chưa có tên.rar"]:
        out.append(pack([("giải nén", "ACTION"), (z, "FILE")]))
        out.append(pack([("mở", "ACTION"), ("nén", None), (z, "FILE")]))
    return out


def gen_email_web_weather_news():
    out = []
    # gửi email
    for p in PERSONS:
        out.append(
            pack([("gửi", "ACTION"), ("email", "APP"), ("cho", None), (p, "PERSON")])
        )
    for e in EMAILS:
        out.append(
            pack([("gửi", "ACTION"), ("email", "APP"), ("tới", None), (e, "EMAIL")])
        )
    # web/search
    for q in QUERIES:
        out.append(pack([("tìm", "ACTION"), (q, "QUERY")]))
        out.append(pack([("tra cứu", "ACTION"), (q, "QUERY")]))
    # weather
    for loc in ["Hà Nội", "Hồ Chí Minh", "Đà Nẵng"]:
        out.append(pack([("thời tiết", None), (loc, "LOCATION"), ("hôm nay", None)]))
        out.append(pack([("dự báo", None), ("thời tiết", None), (loc, "LOCATION")]))
    # news
    out.append(pack([("tin tức", None), ("công nghệ", "QUERY")]))
    out.append(pack([("tin nóng", None), ("hôm nay", "QUERY")]))
    return out


def gen_misc():
    out = []
    # small talk
    out.append(pack([("chào", None)]))
    out.append(pack([("xin chào", None)]))
    out.append(pack([("cảm ơn", None)]))
    # system
    out.append(pack([("mấy giờ", "QUERY"), ("rồi", None)]))
    out.append(pack([("xem", "ACTION"), ("tình trạng", None), ("máy", None)]))
    # youtube as APP
    out.append(pack([("mở", "ACTION"), ("youtube", "APP")]))
    out.append(
        pack(
            [
                ("xem", "ACTION"),
                ("video", None),
                ("Yesterday", "QUERY"),
                ("trên", None),
                ("youtube", "APP"),
            ]
        )
    )
    return out


def gen_path_samples():
    out = []
    # Các thư mục quen thuộc → PATH
    known_paths = ["Desktop", "Tài liệu", "Documents", "Downloads"]
    for p in known_paths:
        out.append(pack([("trong", None), ("thư mục", None), (p, "PATH")]))
        out.append(pack([("trong", None), (p, "PATH")]))
        out.append(pack([("ở", None), (p, "PATH")]))

    # Ổ đĩa → PATH (ổ D/E) và mẫu có drive literal
    for drv in ["ổ D", "ổ E"]:
        out.append(pack([("trong", None), (drv, "PATH")]))
        out.append(pack([("ở", None), (drv, "PATH")]))

    # Drive literal ví dụ "D:\"
    out.append(pack([("trong", None), ("D:\\", "PATH")]))
    out.append(pack([("ở", None), ("E:\\", "PATH")]))

    # Kết hợp cùng FILE/ACTION để mô hình hóa ngữ cảnh
    out.append(
        pack(
            [
                ("mở", "ACTION"),
                ("file", None),
                ("báo cáo.docx", "FILE"),
                ("trong", None),
                ("Tài liệu", "PATH"),
            ]
        )
    )
    out.append(
        pack(
            [("tìm", "ACTION"), ("check.txt", "FILE"), ("ở", None), ("Desktop", "PATH")]
        )
    )
    out.append(
        pack(
            [("tìm", "ACTION"), ("ảnh.png", "FILE"), ("trong", None), ("D:\\", "PATH")]
        )
    )
    return out


def build_dataset():
    data = []
    data += gen_app_samples()
    data += gen_file_open_delete_copy_rename()
    data += gen_zip_samples()
    data += gen_email_web_weather_news()
    data += gen_misc()
    data += gen_path_samples()

    # mở rộng nhẹ bằng cách lặp lại ngẫu nhiên  (tăng size ~1200+)
    extra = []
    for _ in range(300):
        extra.append(random.choice(data))
    data += extra

    return data


TRAIN_DATA = build_dataset()
# tương thích tên biến cũ nếu cần
NER_TRAIN_DATA = TRAIN_DATA
