# -*- coding: utf-8 -*-
import json
import random
from pathlib import Path
from faker import Faker

fake = Faker("vi_VN")

# -----------------------------
# 1️⃣ Templates, Intents, Entities
# -----------------------------
INTENTS = {
    "open_app": ["mở {app}", "chạy {app}", "khởi động {app}"],
    "close_app": ["tắt {app}", "đóng {app}"],
    "open_file": ["mở file {file} bằng {app}", "chạy {file} trên {app}"],
    "delete_file": ["xóa file {file}", "delete {file}"],
    "rename_file": ["đổi tên {file} thành {new_file}", "rename {file} {new_file}"],
    "play_music": ["phát bài {query} trên {app}", "nghe {query} bằng {app}"],
    "send_message": ["gửi tin nhắn cho {contact}: {text}"],
    "read_email": ["đọc email từ {contact}"],
    "write_email": ["viết email tới {contact}: {text}"],
    "calendar_event": ["tạo lịch hẹn {text} vào {date} {time}"],
}

ENTITIES = {
    "app": ["Chrome", "Excel", "Word", "VLC", "Spotify", "Notepad", "Photoshop"],
    "file": ["bao_cao.xlsx", "thuyet_trinh.pptx", "code.py", "data.json"],
    "new_file": ["bao_cao_moi.xlsx", "thuyet_trinh2.pptx", "code_v2.py"],
    "query": ["Faded", "Shape of You", "Despacito"],
    "contact": ["Minh", "Lan", "Huy", "Trang"],
    "text": ["Xin chào, bạn có khỏe không?", "Gửi tài liệu mới nhất"],
    "date": ["25/12/2025", "01/01/2026"],
    "time": ["14:30", "08:00"],
}

NATURAL_ADDITIONS = ["", " giúp tôi", " đi", " nào", " làm ơn", " nhanh lên"]


# -----------------------------
# 2️⃣ Generate multi-entity NLU
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
# 3️⃣ Multi-turn dialogues với logic context
# -----------------------------
def generate_multi_turn(session_count=100000):
    sessions = []
    for i in range(session_count):
        turns = []
        # Chọn intent session chính
        main_intent = random.choice(list(INTENTS.keys()))
        # Quyết định số turn
        num_turns = random.randint(2, 6)

        context = {}
        for t in range(num_turns):
            role = "user" if t % 2 == 0 else "assistant"

            if role == "user":
                # Nếu user cần reply bot question
                if context.get("awaiting_entity"):
                    ent_type = context["awaiting_entity"]
                    value = random.choice(ENTITIES[ent_type])
                    text = value
                    context.pop("awaiting_entity")
                else:
                    template = random.choice(INTENTS[main_intent])
                    text = template
                    # Check nếu template cần entity mà chưa có → bot hỏi
                    for ent_type in ENTITIES:
                        placeholder = "{" + ent_type + "}"
                        if placeholder in text:
                            if (
                                random.random() < 0.5
                            ):  # simulate missing entity → bot will ask
                                text = text.replace(placeholder, "")
                                context["awaiting_entity"] = ent_type
                            else:
                                value = random.choice(ENTITIES[ent_type])
                                text = text.replace(placeholder, value)
            else:
                # assistant reply
                if context.get("awaiting_entity"):
                    text = f"Bạn chưa cung cấp {context['awaiting_entity']}, vui lòng cho biết."
                else:
                    text = f"Đã thực hiện: {main_intent.replace('_',' ')}"

            turns.append({"role": role, "text": text})
        sessions.append({"session_id": f"sess_{i:06d}", "turns": turns})
    return sessions


# -----------------------------
# 4️⃣ Lưu files
# -----------------------------
output_dir = Path("dataset")
(output_dir / "nlu").mkdir(parents=True, exist_ok=True)
(output_dir / "multi_turn").mkdir(parents=True, exist_ok=True)
(output_dir / "domain").mkdir(parents=True, exist_ok=True)

# NLU JSONL
nlu_data = generate_nlu_data(3000000)  # 1M câu, chỉnh lên 3M nếu muốn
with open(
    output_dir / "nlu" / "nlu_rasa_multi_entity.jsonl", "w", encoding="utf-8"
) as f:
    for item in nlu_data:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

# Multi-turn JSON
multi_turn_data = generate_multi_turn(100000)  # 100k session
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

print("✅ Full multi-entity + multi-turn dataset generated!")
