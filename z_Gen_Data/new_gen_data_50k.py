import json
import random
from itertools import product

INTENT_TEMPLATES = {
    "OPEN_APP": [
        "mở {app}",
        "khởi động {app}",
        "chạy {app}",
        "bật {app}",
        "mở ứng dụng {app}",
        "giúp tôi mở {app}",
        "tôi muốn dùng {app}",
        "có thể mở {app} không",
        "mở {app} lên",
        "bật {app} lên",
    ],
    "CLOSE_APP": [
        "tắt {app}",
        "đóng {app}",
        "thoát {app}",
        "dừng {app}",
        "tắt {app} giúp tôi",
    ],
    "SEARCH_FILE": [
        "tìm file {filename}",
        "tìm kiếm {filename}",
        "{filename} ở đâu",
        "search {filename}",
        "kiếm file {filename}",
    ],
    "OPEN_WEBSITE": [
        "mở {website}",
        "vào {website}",
        "truy cập {website}",
        "mở link {website}",
    ],
    "SYSTEM_CONTROL": [
        "{action} máy",
        "{action} máy tính",
        "{action} hệ thống",
        "làm ơn {action} máy",
    ],
    "CREATE_FILE": [
        "tạo file {filename}",
        "tạo {filename}",
        "tạo thư mục {filename}",
        "tạo file {filename} giúp tôi",
    ],
    "DELETE_FILE": [
        "xóa file {filename}",
        "delete {filename}",
        "xóa {filename} đi",
    ],
}

ENTITIES = {
    "app": [
        "chrome",
        "firefox",
        "edge",
        "cốc cốc",
        "brave",
        "notepad",
        "word",
        "excel",
        "powerpoint",
        "vscode",
        "pycharm",
        "skype",
        "discord",
        "spotify",
        "vlc",
        "photoshop",
        "illustrator",
        "premiere",
        "paint",
        "cmd",
        "terminal",
        "powershell",
    ],
    "filename": [
        "document.pdf",
        "baocao.docx",
        "dulieu.xlsx",
        "thuyettrinh.pptx",
        "hinhanh.jpg",
        "video.mp4",
        "photo.png",
        "data.json",
        "code.py",
        "script.js",
        "project.zip",
        "backup.rar",
    ],
    "website": [
        "google.com",
        "facebook.com",
        "youtube.com",
        "gmail.com",
        "github.com",
        "stackoverflow.com",
        "vnexpress.net",
        "shopee.vn",
        "tiki.vn",
        "wikipedia.org",
    ],
    "action": ["tắt", "khóa", "sleep", "hibernate", "restart", "shut down"],
}

NATURAL_ADD = [
    "",
    " giúp tôi",
    " với",
    " đi",
    " nha",
    " nhé",
    " cho tôi",
    " nhanh lên",
    " được không",
]

AUG_VARIATIONS = {
    "mở": ["khởi động", "bật", "chạy"],
    "tắt": ["đóng", "thoát", "ngừng"],
    "tìm": ["search", "kiếm", "tìm kiếm"],
    "file": ["tệp", "tập tin"],
}

# --------------------------------------------------------
# TẠO CÂU
# --------------------------------------------------------


def smart_augment(text):
    for word, repls in AUG_VARIATIONS.items():
        if word in text and random.random() > 0.6:
            text = text.replace(word, random.choice(repls), 1)
    if random.random() > 0.5:
        text += random.choice(NATURAL_ADD)
    return text.strip()


def generate_sentences(target_size=50000):
    generated = set()
    data = []

    while len(generated) < target_size:
        intent = random.choice(list(INTENT_TEMPLATES.keys()))
        template = random.choice(INTENT_TEMPLATES[intent])

        # Xác định entity type
        entity_type = None
        for et in ENTITIES.keys():
            if "{" + et + "}" in template:
                entity_type = et
                break

        value = random.choice(ENTITIES[entity_type])
        sentence = template.replace("{" + entity_type + "}", value)

        # Augment
        sentence = smart_augment(sentence)

        if sentence not in generated:
            generated.add(sentence)
            data.append(
                {"text": sentence, "intent": intent, "entities": {entity_type: value}}
            )

    return data


# --------------------------------------------------------
# TẠO NER DATA
# --------------------------------------------------------


def create_ner(data):
    ner_data = []
    for item in data:
        t = item["text"]
        ents = []
        for et, val in item["entities"].items():
            start = t.find(val)
            if start != -1:
                ents.append(
                    {"start": start, "end": start + len(val), "label": et.upper()}
                )
        ner_data.append({"text": t, "entities": ents})
    return ner_data


# --------------------------------------------------------
# MAIN
# --------------------------------------------------------


def main():
    print("⏳ Generating 50,000 samples...")
    data = generate_sentences(50000)
    print("✅ Done generating intent data!")

    ner = create_ner(data)
    print("🏷️ Done generating NER data!")

    json.dump(
        data,
        open("intent_50k.json", "w", encoding="utf-8"),
        ensure_ascii=False,
        indent=2,
    )
    json.dump(
        ner, open("ner_50k.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2
    )

    print("\n🎉 COMPLETED!")
    print("📂 intent_50k.json")
    print("📂 ner_50k.json")


if __name__ == "__main__":
    main()
