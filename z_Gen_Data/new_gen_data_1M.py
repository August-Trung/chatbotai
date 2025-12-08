# -*- coding: utf-8 -*-
import json
import random
import os
from pathlib import Path
from itertools import product
from faker import Faker

fake = Faker("vi_VN")

# -----------------------------
# 1️⃣ Cấu hình intents, entities, templates
# -----------------------------
INTENTS = {
    "open_app": ["mở {app}", "khởi động {app}", "chạy {app}", "bật {app}"],
    "close_app": ["tắt {app}", "đóng {app}", "thoát {app}"],
    "find_file": ["tìm file {file}", "mở {file}", "file {file} ở đâu"],
    "delete_file": ["xóa {file}", "delete {file}"],
    "rename_file": ["đổi tên {file} thành {new_file}", "rename {file} {new_file}"],
    "play_music": ["phát bài {query} trên {app}", "nghe {query} trên {app}"],
    "open_website": ["mở {website}", "truy cập {website}", "vào {website}"],
    "send_message": ["gửi tin nhắn cho {contact}: {text}"],
    "read_email": ["đọc email từ {contact}"],
    "write_email": ["viết email tới {contact}: {text}"],
    "calendar_event": ["tạo lịch hẹn {text} vào {date} {time}"],
    "system_control": ["{action} máy tính", "{action} hệ thống"],
    "network_control": ["bật {action}", "tắt {action}"],
    "screen_control": ["chia màn hình", "full screen"],
    "automation": ["chạy script {file}", "thực thi {file}"],
    "media_control": ["tăng âm lượng", "giảm âm lượng", "dừng nhạc"],
    "file_management": ["sao chép {file} đến {path}", "di chuyển {file} đến {path}"],
    "search_web": ["tìm kiếm {query}", "search {query} trên Google"],
    "miscellaneous": ["thời tiết ở {location}", "mấy giờ rồi?"],
}

ENTITIES = {
    "app": ["Chrome", "Excel", "Word", "VLC", "Spotify", "Notepad", "Photoshop"],
    "file": ["bao_cao.xlsx", "thuyet_trinh.pptx", "code.py", "data.json"],
    "new_file": ["bao_cao_moi.xlsx", "thuyet_trinh2.pptx", "code_v2.py"],
    "query": ["Faded", "Shape of You", "Despacito"],
    "contact": ["Minh", "Lan", "Huy", "Trang"],
    "website": ["google.com", "facebook.com", "youtube.com"],
    "text": ["Xin chào, bạn có khỏe không?", "Gửi tài liệu mới nhất"],
    "date": ["25/12/2025", "01/01/2026"],
    "time": ["14:30", "08:00"],
    "action": ["tắt", "khởi động lại", "sleep", "restart"],
    "path": ["C:/Users/Admin/Desktop", "C:/Users/Admin/Documents"],
    "location": ["Hà Nội", "TP.HCM", "Đà Nẵng"],
}

NATURAL_ADDITIONS = ["", " giúp tôi", " đi", " nào", " làm ơn", " nhanh lên"]


# -----------------------------
# 2️⃣ Generate NLU data
# -----------------------------
def generate_nlu_data(num_samples=1000000):
    data = []
    intents_list = list(INTENTS.keys())
    for _ in range(num_samples):
        intent = random.choice(intents_list)
        template = random.choice(INTENTS[intent])
        text = template
        entities_list = []

        for ent_type in ENTITIES:
            placeholder = "{" + ent_type + "}"
            if placeholder in text:
                value = random.choice(ENTITIES[ent_type])
                start = text.find(placeholder)
                text = text.replace(placeholder, value)
                end = start + len(value)
                entities_list.append(
                    {"start": start, "end": end, "label": ent_type.upper()}
                )

        # Thêm từ tự nhiên
        text += random.choice(NATURAL_ADDITIONS)

        data.append({"text": text, "intent": intent, "entities": entities_list})
    return data


# -----------------------------
# 3️⃣ Generate multi-turn dialogues
# -----------------------------
def generate_multi_turn(session_count=100000):
    sessions = []
    for i in range(session_count):
        turns = []
        num_turns = random.randint(2, 6)
        for j in range(num_turns):
            intent = random.choice(list(INTENTS.keys()))
            template = random.choice(INTENTS[intent])
            text = template
            for ent_type in ENTITIES:
                placeholder = "{" + ent_type + "}"
                if placeholder in text:
                    value = random.choice(ENTITIES[ent_type])
                    text = text.replace(placeholder, value)
            role = "user" if j % 2 == 0 else "assistant"
            if role == "assistant":
                text = f"Đã thực hiện: {text}"
            turns.append({"role": role, "text": text})
        sessions.append({"session_id": f"sess_{i:06d}", "turns": turns})
    return sessions


# -----------------------------
# 4️⃣ Save files
# -----------------------------
output_dir = Path("dataset")
(output_dir / "nlu").mkdir(parents=True, exist_ok=True)
(output_dir / "multi_turn").mkdir(parents=True, exist_ok=True)
(output_dir / "domain").mkdir(parents=True, exist_ok=True)

# NLU JSONL
nlu_data = generate_nlu_data(1000000)  # chỉnh số lượng: 1M–3M
with open(output_dir / "nlu" / "nlu_rasa_1000000.jsonl", "w", encoding="utf-8") as f:
    for item in nlu_data:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

# Multi-turn JSON
multi_turn_data = generate_multi_turn(100000)
with open(
    output_dir / "multi_turn" / "multi_turn_100k.json", "w", encoding="utf-8"
) as f:
    json.dump(multi_turn_data, f, ensure_ascii=False, indent=2)

# Domain.yml
domain_content = {
    "version": "3.1",
    "intents": list(INTENTS.keys()),
    "entities": [e.upper() for e in ENTITIES.keys()],
    "slots": {e.upper(): {"type": "text"} for e in ENTITIES.keys()},
    "responses": {
        "utter_default": [{"text": "Mình đã nhận: {text}, bạn muốn làm gì tiếp theo?"}]
    },
    "actions": [f"action_{i}" for i in INTENTS.keys()],
}
with open(output_dir / "domain" / "domain.yml", "w", encoding="utf-8") as f:
    import yaml

    yaml.dump(domain_content, f, allow_unicode=True)

print("✅ Dataset generated successfully!")
