import json
import random
from itertools import product

# =============================================================================
# PHẦN 1: ĐỊNH NGHĨA TEMPLATES VÀ ENTITIES
# =============================================================================

INTENT_TEMPLATES = {
    "OPEN_APP": [
        "mở {app}",
        "khởi động {app}",
        "chạy {app}",
        "bật {app}",
        "mở ứng dụng {app}",
        "{app} giúp tôi",
        "tôi muốn dùng {app}",
        "có thể mở {app} không",
        "giúp tôi mở {app}",
        "mở {app} lên",
        "bật {app} lên đi",
        "chạy {app} cho tôi",
        "{app} đi",
        "mở {app} giúp với",
    ],
    "CLOSE_APP": [
        "tắt {app}",
        "đóng {app}",
        "thoát {app}",
        "kill {app}",
        "dừng {app}",
        "{app} tắt đi",
        "tắt {app} giúp tôi",
        "đóng {app} lại",
        "ngừng {app}",
        "thoát {app} đi",
    ],
    "SEARCH_FILE": [
        "tìm file {filename}",
        "tìm {filename}",
        "file {filename} ở đâu",
        "tìm kiếm {filename}",
        "{filename} ở đâu",
        "tìm giúp tôi file {filename}",
        "có file {filename} không",
        "tìm file tên {filename}",
        "search {filename}",
        "kiếm file {filename}",
    ],
    "OPEN_WEBSITE": [
        "mở {website}",
        "vào {website}",
        "truy cập {website}",
        "mở trang {website}",
        "{website} giúp tôi",
        "vào trang {website}",
        "mở link {website}",
        "truy cập trang {website}",
    ],
    "SYSTEM_CONTROL": [
        "{action} máy",
        "{action} máy tính",
        "{action} hệ thống",
        "làm ơn {action} máy",
        "{action} computer",
        "{action} pc",
        "{action} laptop",
    ],
    "CREATE_FILE": [
        "tạo file {filename}",
        "tạo {filename}",
        "tạo file mới tên {filename}",
        "tạo folder {filename}",
        "tạo thư mục {filename}",
        "tạo file {filename} giúp tôi",
    ],
    "DELETE_FILE": [
        "xóa file {filename}",
        "xóa {filename}",
        "delete {filename}",
        "xóa file {filename} đi",
        "xóa bỏ {filename}",
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
        "access",
        "vscode",
        "visual studio",
        "pycharm",
        "sublime text",
        "atom",
        "telegram",
        "zalo",
        "messenger",
        "skype",
        "discord",
        "spotify",
        "vlc",
        "winamp",
        "itunes",
        "photoshop",
        "illustrator",
        "lightroom",
        "premiere",
        "winrar",
        "7zip",
        "unikey",
        "paint",
        "calculator",
        "cmd",
        "terminal",
        "powershell",
        "task manager",
    ],
    "filename": [
        "document.pdf",
        "baocao.docx",
        "dulieu.xlsx",
        "thuyettrinh.pptx",
        "hinhanh.jpg",
        "anh.png",
        "video.mp4",
        "phim.avi",
        "nhac.mp3",
        "audio.wav",
        "code.py",
        "script.js",
        "index.html",
        "style.css",
        "data.json",
        "config.xml",
        "report.pdf",
        "ketqua.xlsx",
        "bangdiem.xlsx",
        "project.zip",
        "backup.rar",
        "photo.jpg",
    ],
    "website": [
        "google.com",
        "facebook.com",
        "youtube.com",
        "gmail.com",
        "github.com",
        "stackoverflow.com",
        "reddit.com",
        "vnexpress.net",
        "dantri.com.vn",
        "zalo.me",
        "shopee.vn",
        "lazada.vn",
        "tiki.vn",
        "wikipedia.org",
        "twitter.com",
        "linkedin.com",
    ],
    "action": ["tắt", "khóa", "sleep", "hibernate", "restart", "shut down"],
}

# Các từ ghép thêm để tạo biến thể tự nhiên
NATURAL_ADDITIONS = [
    "",
    " giúp tôi",
    " với",
    " đi",
    " nào",
    " cho tôi",
    " giúp với",
    " được không",
    " giúp mình",
    " nhanh lên",
]

# =============================================================================
# PHẦN 2: HÀM TẠO DATA CƠ BẢN
# =============================================================================


def generate_basic_data():
    """Tạo data cơ bản từ templates"""
    data = []

    for intent, templates in INTENT_TEMPLATES.items():
        for template in templates:
            # Tìm entity type trong template
            entity_type = None
            for etype in ENTITIES.keys():
                placeholder = f"{{{etype}}}"
                if placeholder in template:
                    entity_type = etype
                    break

            if entity_type:
                # Generate với mọi giá trị của entity
                for value in ENTITIES[entity_type]:
                    text = template.replace(f"{{{entity_type}}}", value)

                    data.append(
                        {
                            "text": text,
                            "intent": intent,
                            "entities": {entity_type: value},
                        }
                    )

    return data


# =============================================================================
# PHẦN 3: AUGMENTATION - TẠO BIẾN THỂ TỰ NHIÊN
# =============================================================================


def augment_data(data, multiplier=2):
    """Tạo biến thể tự nhiên của data"""
    augmented = []

    for item in data:
        # Giữ bản gốc
        augmented.append(item)

        # Tạo biến thể
        for _ in range(multiplier - 1):
            new_text = item["text"]

            # Thêm từ tự nhiên
            addition = random.choice(NATURAL_ADDITIONS)
            if addition:
                new_text = new_text + addition

            # Biến đổi một số từ
            new_text = augment_vietnamese_text(new_text)

            augmented.append(
                {
                    "text": new_text,
                    "intent": item["intent"],
                    "entities": item["entities"],
                }
            )

    return augmented


def augment_vietnamese_text(text):
    """Tạo biến thể tiếng Việt"""
    variations = {
        "mở": ["khởi động", "chạy", "bật"],
        "tắt": ["đóng", "thoát", "ngừng"],
        "tìm": ["tìm kiếm", "search", "kiếm"],
        "giúp tôi": ["cho tôi", "giúp mình", "dùm tôi"],
        "file": ["tệp", "tập tin"],
        "folder": ["thư mục"],
    }

    for word, replacements in variations.items():
        if word in text and random.random() > 0.5:
            replacement = random.choice(replacements)
            text = text.replace(word, replacement, 1)

    return text


# =============================================================================
# PHẦN 4: TẠO NER DATA (ANNOTATED ENTITIES)
# =============================================================================


def create_ner_data(intent_data):
    """Tạo NER data với vị trí entities"""
    ner_data = []

    for item in intent_data:
        text = item["text"]
        entities_list = []

        # Tìm vị trí của entities
        for entity_type, entity_value in item["entities"].items():
            start = text.find(entity_value)
            if start != -1:
                end = start + len(entity_value)
                entities_list.append(
                    {"start": start, "end": end, "label": entity_type.upper()}
                )

        ner_data.append({"text": text, "entities": entities_list})

    return ner_data


# =============================================================================
# PHẦN 5: MAIN - CHẠY VÀ LƯU DATA
# =============================================================================


def main():
    print("🚀 BẮT ĐẦU TẠO DATASET...")

    # 1. Tạo data cơ bản
    print("\n📝 Tạo data cơ bản từ templates...")
    basic_data = generate_basic_data()
    print(f"✅ Đã tạo {len(basic_data)} samples cơ bản")

    # 2. Augmentation
    print("\n🔄 Tạo biến thể tự nhiên (augmentation)...")
    augmented_data = augment_data(basic_data, multiplier=2)
    print(f"✅ Đã tạo {len(augmented_data)} samples sau augmentation")

    # 3. Shuffle
    random.shuffle(augmented_data)

    # 4. Tạo NER data
    print("\n🏷️  Tạo NER data...")
    ner_data = create_ner_data(augmented_data)
    print(f"✅ Đã tạo {len(ner_data)} NER samples")

    # 5. Lưu file
    print("\n💾 Lưu data vào files...")

    # Intent classification data
    with open("intent_data.json", "w", encoding="utf-8") as f:
        json.dump(augmented_data, f, ensure_ascii=False, indent=2)
    print("✅ Đã lưu: intent_data.json")

    # NER data
    with open("ner_data.json", "w", encoding="utf-8") as f:
        json.dump(ner_data, f, ensure_ascii=False, indent=2)
    print("✅ Đã lưu: ner_data.json")

    # Statistics
    print("\n📊 THỐNG KÊ:")
    print(f"- Tổng số samples: {len(augmented_data)}")
    intent_counts = {}
    for item in augmented_data:
        intent = item["intent"]
        intent_counts[intent] = intent_counts.get(intent, 0) + 1

    print("\n- Phân bố theo Intent:")
    for intent, count in sorted(intent_counts.items()):
        print(f"  {intent}: {count} samples")

    # Mẫu data
    print("\n📋 MẪU DATA:")
    for i in range(5):
        print(f"\nSample {i+1}:")
        print(f"  Text: {augmented_data[i]['text']}")
        print(f"  Intent: {augmented_data[i]['intent']}")
        print(f"  Entities: {augmented_data[i]['entities']}")

    print("\n✨ HOÀN THÀNH! Data đã sẵn sàng để train.")
    print("\n📂 Files đã tạo:")
    print("  - intent_data.json (cho Intent Classification)")
    print("  - ner_data.json (cho Named Entity Recognition)")


if __name__ == "__main__":
    main()
