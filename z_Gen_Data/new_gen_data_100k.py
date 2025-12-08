# generate_nlu_dataset.py
import json
import random
import os
from collections import defaultdict
from itertools import combinations

random.seed(42)

# ---------------------------
# CONFIG
# ---------------------------
TARGET_SAMPLES = 100_000  # đổi thành 200_000 hoặc 500_000 nếu cần
MULTI_TURN_SESSIONS = 5000  # số session multi-turn
MAX_UTTERANCES_PER_SESSION = 6
OUTPUT_DIR = "generated_dataset"

# ---------------------------
# TEMPLATES & ENTITIES (mở rộng)
# ---------------------------
INTENT_TEMPLATES = {
    "OPEN_APP": [
        "mở {app}",
        "khởi động {app}",
        "chạy {app}",
        "bật {app}",
        "mở ứng dụng {app}",
    ],
    "CLOSE_APP": ["tắt {app}", "đóng {app}", "thoát {app}", "tắt {app} giúp tôi"],
    "SEARCH_FILE": [
        "tìm file {filename}",
        "tìm {filename}",
        "file {filename} ở đâu",
        "search {filename}",
    ],
    "OPEN_WEBSITE": [
        "mở {website}",
        "vào {website}",
        "truy cập {website}",
        "mở link {website}",
    ],
    "SYSTEM_CONTROL": ["{action} máy", "{action} máy tính", "làm ơn {action} máy"],
    "CREATE_FILE": [
        "tạo file {filename}",
        "tạo thư mục {filename}",
        "tạo {filename} giúp tôi",
    ],
    "DELETE_FILE": ["xóa file {filename}", "xóa {filename} đi", "delete {filename}"],
    "MOVE_FILE": [
        "di chuyển {filename} tới {filename_dest}",
        "chuyển {filename} sang thư mục {filename_dest}",
    ],
    "DOWNLOAD": ["tải {filename} từ {website}", "download {filename} từ {website}"],
    "ASK_HELP": ["giúp tôi {task}", "làm sao để {task}", "hướng dẫn tôi {task}"],
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
        "telegram",
        "zalo",
        "discord",
        "spotify",
        "vlc",
        "photoshop",
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
        "report_v1.pdf",
        "ketqua.xlsx",
    ],
    "filename_dest": ["Backup", "ProjectX", "Photos", "Downloads", "Reports"],
    "website": [
        "google.com",
        "facebook.com",
        "youtube.com",
        "github.com",
        "stackoverflow.com",
        "vnexpress.net",
        "shopee.vn",
        "tiki.vn",
        "wikipedia.org",
    ],
    "action": ["tắt", "khóa", "sleep", "hibernate", "restart", "shut down"],
    "task": ["cài đặt python", "kết nối wifi", "sao lưu dữ liệu", "cài đặt driver"],
}

NATURAL_ADDITIONS = [
    "",
    " giúp tôi",
    " với",
    " đi",
    " nha",
    " nhé",
    " cho tôi",
    " nhanh",
    " được không",
    " giùm",
]

VARIATIONS = {
    "mở": ["khởi động", "bật", "chạy"],
    "tắt": ["đóng", "thoát", "ngừng"],
    "tìm": ["tìm kiếm", "search", "kiếm"],
    "file": ["tệp", "tập tin"],
    "giúp tôi": ["cho tôi", "giúp mình", "dùm tôi"],
}


# ---------------------------
# UTIL
# ---------------------------
def smart_replace_once(text, src, dst):
    idx = text.find(src)
    if idx == -1:
        return text
    return text[:idx] + dst + text[idx + len(src) :]


def apply_variations(text):
    for key, opts in VARIATIONS.items():
        if key in text and random.random() > 0.5:
            text = smart_replace_once(text, key, random.choice(opts))
    if random.random() > 0.4:
        text = text + random.choice(NATURAL_ADDITIONS)
    return text.strip()


def choose_entity_value(entity_type):
    return random.choice(ENTITIES[entity_type])


# ---------------------------
# GENERATE SINGLE-TURN SENTENCES
# ---------------------------
def generate_single_turn_sample():
    # pick an intent
    intent = random.choice(list(INTENT_TEMPLATES.keys()))
    template = random.choice(INTENT_TEMPLATES[intent])

    # support templates with multiple placeholders (filename_dest, website...)
    text = template
    entity_map = {}
    for ent in ENTITIES.keys():
        placeholder = "{" + ent + "}"
        if placeholder in template:
            val = choose_entity_value(ent)
            text = text.replace(placeholder, val, 1)
            entity_map[ent] = val

    # randomly add another entity into sentence to create multi-entity examples
    if random.random() < 0.25:
        # select another entity type different from already used
        available = [k for k in ENTITIES.keys() if k not in entity_map]
        if available:
            ent2 = random.choice(available)
            # append phrase with that entity
            addition_templates = [
                " và {ent2}",
                " cùng với {ent2}",
                " rồi {ent2}",
                " kèm theo {ent2}",
            ]
            add_t = random.choice(addition_templates)
            val2 = choose_entity_value(ent2)
            add_phrase = add_t.replace("{ent2}", val2)
            text = text + add_phrase
            entity_map[ent2] = val2

    # apply text variations and natural additions
    text = apply_variations(text)

    return {"text": text, "intent": intent, "entities": entity_map}


# ---------------------------
# CREATE BIO TAGS (NER)
# ---------------------------
def create_bio_annotations(text, entities):
    tokens = text.split()
    # We'll map token indices to character positions to allow BIO tagging per token
    char_to_token = []
    cur = 0
    for t in tokens:
        start = text.find(t, cur)
        end = start + len(t)
        char_to_token.append((start, end, t))
        cur = end

    bio_tags = ["O"] * len(tokens)
    # For each entity (value), find substring(s) and map to tokens — this is approximate but common
    for label, val in entities.items():
        # find val inside text (may be multiple times) — we handle first occurrence per design
        start = text.find(val)
        if start == -1:
            # try lower
            start = text.lower().find(val.lower())
        if start == -1:
            continue
        end = start + len(val)
        # mark tokens that overlap
        first_idx = None
        last_idx = None
        for i, (s, e, tok) in enumerate(char_to_token):
            if not (e <= start or s >= end):  # overlap
                if first_idx is None:
                    first_idx = i
                last_idx = i
        if first_idx is not None:
            bio_tags[first_idx] = "B-" + label.upper()
            for j in range(first_idx + 1, last_idx + 1):
                bio_tags[j] = "I-" + label.upper()
    # return list of (token, tag)
    return list(zip(tokens, bio_tags))


# ---------------------------
# MULTI-TURN DIALOGUE GENERATOR
# ---------------------------
ASSISTANT_TEMPLATES = {
    "ACK": ["Đã mở giúp bạn", "Xong rồi nhé", "Hoàn tất", "Đã xử lý"],
    "ASK_CLARIFY": [
        "Bạn muốn mở phiên bản nào?",
        "Bạn cần tôi mở thư mục nào?",
        "Bạn muốn lưu vào đâu?",
    ],
    "PROVIDE_HELP": [
        "Bạn có thể làm theo các bước: ...",
        "Mình sẽ hướng dẫn từng bước",
    ],
    "ERROR": [
        "Mình không tìm thấy file đó",
        "Không có ứng dụng như vậy trên hệ thống của bạn",
    ],
}


def generate_multi_turn_session(max_utterances=6):
    # simple session builder mixing user intents and assistant replies
    session = []
    # choose a starting intent for user
    user_turns = random.randint(1, max_utterances // 2)
    for i in range(user_turns):
        user_sample = generate_single_turn_sample()
        session.append(
            {
                "role": "user",
                "text": user_sample["text"],
                "intent": user_sample["intent"],
                "entities": user_sample["entities"],
            }
        )
        # assistant reacts
        # choose assistant act
        act = random.choices(
            list(ASSISTANT_TEMPLATES.keys()), weights=[0.4, 0.2, 0.3, 0.1]
        )[0]
        reply = random.choice(ASSISTANT_TEMPLATES[act])
        # sometimes include an entity or clarification
        if act == "ASK_CLARIFY":
            # pick a clarifying question referencing an entity
            if user_sample["entities"]:
                ent_key = random.choice(list(user_sample["entities"].keys()))
                reply = reply + " (" + ent_key + "?)"
        session.append({"role": "assistant", "text": reply, "act": act})
    return session


# ---------------------------
# DRIVER: CREATE LARGE DATASET
# ---------------------------
def generate_dataset(target_size=TARGET_SAMPLES):
    samples = []
    seen_texts = set()
    attempts = 0
    max_attempts = target_size * 10

    print(f"Start generating {target_size} single-turn samples...")
    while len(samples) < target_size and attempts < max_attempts:
        s = generate_single_turn_sample()
        t = s["text"]
        attempts += 1
        # normalize whitespace
        t_norm = " ".join(t.split())
        if t_norm in seen_texts:
            continue
        seen_texts.add(t_norm)
        s["text"] = t_norm
        samples.append(s)
        if len(samples) % 10000 == 0:
            print(f"  generated {len(samples)} samples...")

    print(f"Generated {len(samples)} samples (attempts {attempts}).")
    return samples


# ---------------------------
# EXPORT FUNCTIONS
# ---------------------------
def export_intent_json(samples, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(samples, f, ensure_ascii=False, indent=2)


def export_bio(samples, path):
    # write token TAB tag per line, blank line between sentences
    with open(path, "w", encoding="utf-8") as f:
        for s in samples:
            bio = create_bio_annotations(s["text"], s["entities"])
            for token, tag in bio:
                f.write(f"{token}\t{tag}\n")
            f.write("\n")


def export_rasa_style(samples, path):
    # basic Rasa-style: intent -> list of examples
    rasa = {
        "rasa_nlu_data": {
            "common_examples": [],
            "regex_features": [],
            "entity_synonyms": [],
        }
    }
    for s in samples:
        rasa["rasa_nlu_data"]["common_examples"].append(
            {
                "text": s["text"],
                "intent": s["intent"],
                "entities": [
                    {
                        "start": s["text"].find(v),
                        "end": s["text"].find(v) + len(v),
                        "value": v,
                        "entity": k,
                    }
                    for k, v in s["entities"].items()
                    if s["text"].find(v) != -1
                ],
            }
        )
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rasa, f, ensure_ascii=False, indent=2)


def export_multi_turn(sessions, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(sessions, f, ensure_ascii=False, indent=2)


# ---------------------------
# MAIN
# ---------------------------
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    samples = generate_dataset(TARGET_SAMPLES)
    # exports
    export_intent_json(
        samples, os.path.join(OUTPUT_DIR, f"intent_{TARGET_SAMPLES}.json")
    )
    export_bio(samples, os.path.join(OUTPUT_DIR, f"ner_bio_{TARGET_SAMPLES}.txt"))
    export_rasa_style(samples, os.path.join(OUTPUT_DIR, f"rasa_{TARGET_SAMPLES}.json"))
    print("Exported single-turn formats.")

    # multi-turn sessions
    sessions = []
    print(f"Generating {MULTI_TURN_SESSIONS} multi-turn sessions...")
    for i in range(MULTI_TURN_SESSIONS):
        sess = generate_multi_turn_session(
            random.randint(2, MAX_UTTERANCES_PER_SESSION)
        )
        sessions.append({"session_id": i + 1, "dialogue": sess})
        if (i + 1) % 1000 == 0:
            print(f"  sessions generated: {i+1}")
    export_multi_turn(
        sessions, os.path.join(OUTPUT_DIR, f"multi_turn_{MULTI_TURN_SESSIONS}.json")
    )
    print("Exported multi-turn sessions.")

    print("\nAll files saved to:", OUTPUT_DIR)
    print("Files:")
    for fn in os.listdir(OUTPUT_DIR):
        print(" -", fn)


if __name__ == "__main__":
    main()
