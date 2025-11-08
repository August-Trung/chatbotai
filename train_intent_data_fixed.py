# -*- coding: utf-8 -*-
"""
Sinh dữ liệu huấn luyện Intent cho PhoBERT (text-classification).
Định dạng: TRAIN_DATA = [{"text": "...", "label": "intent_name"}, ...]
"""

from itertools import product
import random

random.seed(42)

# --------- Ý định (intents) phủ rộng dự án ----------
INTENTS = {
    # Ứng dụng
    "open_app": [
        "mở {app}",
        "khởi chạy {app}",
        "bật {app}",
        "chạy {app}",
        "mở ứng dụng {app}",
        "mở app {app}",
    ],
    "close_app": [
        "đóng {app}",
        "tắt {app}",
        "thoát {app}",
        "đóng ứng dụng {app}",
        "tắt ứng dụng {app}",
        "đóng trình duyệt {app}",
        "tắt trình duyệt {app}",
    ],
    "open_website": [
        "vào {site}",
        "truy cập {site}",
        "mở trang {site}",
        "đi tới {site}",
    ],
    # File cơ bản
    "find_file": [
        "tìm file {file}",
        "tìm {file}",
        "tìm tài liệu {file}",
        "tìm tập tin {file}",
        "tìm tệp {file}",
    ],
    "open_file": [
        "mở file {file}",
        "mở {file}",
        "mở tài liệu {file}",
        "mở tập tin {file}",
    ],
    "delete_file": ["xóa file {file}", "xóa {file}", "xóa tập tin {file}"],
    "copy_file": [
        "sao chép file {file} đến {dest}",
        "copy file {file} sang {dest}",
        "chép {file} vào {dest}",
        # NEW:
        "sao chép {file} vào {dest}",
    ],
    "rename_file": [
        "đổi tên file {file} thành {newname}",
        "rename file {file} {newname}",
        # NEW:
        "đổi tên {file} {newname}",
        "đổi tên {file} -> {newname}",
    ],
    "compress_file": [
        "nén thư mục {folder}",
        "tạo file zip từ thư mục {folder}",
        "đóng gói {folder}",
    ],
    "extract_file": ["giải nén file {zip}", "giải nén {zip}", "mở nén {zip}"],
    # Gửi & web & thông tin
    "send_email": [
        "gửi email cho {person} kèm file {file}",
        "gửi thư cho {person}",
        "soạn email cho {person}",
    ],
    "search_web": ["tìm kiếm {query}", "tra cứu {query}", "tìm thông tin về {query}"],
    "get_weather": [
        "thời tiết {loc} hôm nay",
        "dự báo thời tiết {loc}",
        "trời ở {loc} thế nào",
    ],
    "get_news": ["tin tức {query}", "tin công nghệ mới", "tin nóng hôm nay"],
    # Ghi chú / nhắc việc / hệ thống
    "create_note": ["ghi chú {query}", "tạo ghi chú {query}"],
    "read_note": ["đọc ghi chú {query}", "mở ghi chú {query}"],
    "set_reminder": ["nhắc tôi {query} lúc {time}", "đặt nhắc nhở {query} vào {time}"],
    "get_time": ["mấy giờ rồi", "bây giờ là mấy giờ", "giờ hiện tại"],
    "get_system_info": ["xem tình trạng máy", "xem cpu ram", "kiểm tra hệ thống"],
    "set_system_setting": [
        "giảm âm lượng xuống {percent}",
        "tăng độ sáng lên {percent}",
        "tắt âm lượng",
        "bật âm lượng",
    ],
    # Small talk / fallback
    "greeting": ["chào", "xin chào", "hello"],
    "goodbye": ["tạm biệt", "bye", "hẹn gặp lại"],
    "thanks": ["cảm ơn", "thanks", "đội ơn"],
    "help": ["giúp tôi với", "trợ giúp", "hướng dẫn sử dụng"],
    "chitchat": ["bạn khỏe không", "hôm nay thế nào", "kể chuyện đi"],
}

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
DESTS = ["Desktop", "Tài liệu", "Documents", "Downloads", "ổ D", "ổ E"]
FOLDERS = ["báo_cáo_tháng_11", "tai_lieu_quan_trong", "anh_du_lich"]
ZIPS = ["data.zip", "anh.zip", "tai_lieu.zip"]
PERSONS = ["thầy Trung", "chị Lan", "anh Minh", "bạn Huy"]
LOCATIONS = ["Hà Nội", "Hồ Chí Minh", "Đà Nẵng"]
QUERIES = ["thời tiết hôm nay", "Elon Musk", "AI mới nhất", "bóng đá", "lịch thi đấu"]
PERCENTS = ["20%", "50%", "80%"]
TIMES = ["8 giờ tối", "9:30 sáng", "15h30"]
NEWNAMES = ["bao_cao_moi.docx", "report_v2.xlsx", "check_v2.txt"]
SITES = [
    "google",
    "facebook",
    "wiki",
    "wikipedia",
    "bing",
    "edge",
    "gg",
    "me",
    "fb",
    "face",
]


def expand():
    data = []
    # Tạo biến thể có tham số
    for tmpl in INTENTS["open_app"]:
        for app in APPS:
            data.append({"text": tmpl.format(app=app), "label": "open_app"})
    for tmpl in INTENTS["close_app"]:
        for app in APPS:
            data.append({"text": tmpl.format(app=app), "label": "close_app"})

    for tmpl in INTENTS["find_file"]:
        for f in FILES:
            data.append({"text": tmpl.format(file=f), "label": "find_file"})
    for tmpl in INTENTS["open_file"]:
        for f in FILES:
            data.append({"text": tmpl.format(file=f), "label": "open_file"})
    for tmpl in INTENTS["delete_file"]:
        for f in FILES:
            data.append({"text": tmpl.format(file=f), "label": "delete_file"})
    for tmpl in INTENTS["copy_file"]:
        for f, d in product(FILES, DESTS):
            data.append({"text": tmpl.format(file=f, dest=d), "label": "copy_file"})
    for tmpl in INTENTS["rename_file"]:
        for f, n in product(FILES, NEWNAMES):
            data.append(
                {"text": tmpl.format(file=f, newname=n), "label": "rename_file"}
            )
    for tmpl in INTENTS["compress_file"]:
        for folder in FOLDERS:
            data.append({"text": tmpl.format(folder=folder), "label": "compress_file"})
    for tmpl in INTENTS["extract_file"]:
        for z in ZIPS:
            data.append({"text": tmpl.format(zip=z), "label": "extract_file"})

    for tmpl in INTENTS["send_email"]:
        for p in PERSONS:
            for f in ["", FILES[0]]:
                text = tmpl.format(person=p, file=f).replace("  ", " ").strip()
                data.append({"text": text, "label": "send_email"})

    for tmpl in INTENTS["search_web"]:
        for q in QUERIES:
            data.append({"text": tmpl.format(query=q), "label": "search_web"})
    for tmpl in INTENTS["get_weather"]:
        for loc in LOCATIONS:
            data.append({"text": tmpl.format(loc=loc), "label": "get_weather"})
    for tmpl in INTENTS["get_news"]:
        for q in ["công nghệ", "kinh tế", "thế giới"]:
            data.append({"text": tmpl.format(query=q), "label": "get_news"})

    for tmpl in INTENTS["create_note"]:
        for q in QUERIES:
            data.append({"text": tmpl.format(query=q), "label": "create_note"})
    for tmpl in INTENTS["read_note"]:
        for q in QUERIES:
            data.append({"text": tmpl.format(query=q), "label": "read_note"})
    for tmpl in INTENTS["set_reminder"]:
        for q, t in product(["nộp bài", "họp", "đi học"], TIMES):
            data.append({"text": tmpl.format(query=q, time=t), "label": "set_reminder"})

    for tmpl in INTENTS["get_time"]:
        data.extend({"text": x, "label": "get_time"} for x in tmpl)
    for tmpl in INTENTS["get_system_info"]:
        data.extend({"text": x, "label": "get_system_info"} for x in tmpl)
    for tmpl in INTENTS["open_website"]:
        for s in SITES:
            data.append({"text": tmpl.format(site=s), "label": "open_website"})
    for tmpl in INTENTS["set_system_setting"]:
        # percent có / không có
        for p in PERCENTS + [""]:
            data.append(
                {
                    "text": tmpl.format(percent=p).replace("  ", " ").strip(),
                    "label": "set_system_setting",
                }
            )

    for k in ["greeting", "goodbye", "thanks", "help", "chitchat"]:
        for x in INTENTS[k]:
            data.append({"text": x, "label": k})

    # Xáo trộn nhẹ
    random.shuffle(data)
    return data


TRAIN = expand()

# Tương thích tên biến cũ nếu cần
INTENT_DATA = TRAIN
