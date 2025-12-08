# -*- coding: utf-8 -*-
import json, random, re
from pathlib import Path
import yaml
from typing import List, Dict, Tuple, Set
from collections import defaultdict

# ---------------------------
# 1️⃣ ENHANCED INTENTS, ENTITIES & TEMPLATES
# ---------------------------

INTENTS = {
    "open_app": [
        "mở {app}",
        "chạy {app}",
        "khởi động {app}",
        "bật {app}",
        "{app}",
        "start {app}",
        "launch {app}",
    ],
    "close_app": [
        "tắt {app}",
        "đóng {app}",
        "kill {app}",
        "thoát {app}",
        "stop {app}",
        "end {app}",
    ],
    "open_file": [
        "mở file {file}",
        "mở {file}",
        "chạy file {file}",
        "bật file {file}",
        "{file}",
        "xem {file}",
        "load {file}",
        "mở {file} bằng {app}",
        "dùng {app} mở {file}",
    ],
    "delete_file": [
        "xóa file {file}",
        "delete {file}",
        "xóa {file}",
        "remove {file}",
        "gỡ {file}",
    ],
    "copy_file": [
        "sao chép {file}",
        "copy {file}",
        "nhân bản {file}",
        "duplicate {file}",
    ],
    "rename_file": [
        "đổi tên {file} thành {new_file}",
        "rename {file} sang {new_file}",
        "đổi {file} thành {new_file}",
        "chuyển tên {file} thành {new_file}",
    ],
    "play_music": [
        "phát nhạc {query}",
        "nghe bài {query}",
        "play {query}",
        "cho tôi nghe {query}",
        "bật nhạc {query}",
        "mở bài {query}",
        "chạy nhạc {query}",
    ],
    "search_web": [
        "tìm {query} trên web",
        "search {query}",
        "google {query}",
        "tìm kiếm {query}",
        "tra {query}",
        "look up {query}",
    ],
    "send_email": [
        "gửi email đến {contact}",
        "mail {contact}",
        "gửi mail cho {contact}",
        "send email to {contact}",
        "email {contact}",
    ],
    "system_control": [
        "{action} máy",
        "{action} máy tính",
        "{action} pc",
        "{action} laptop",
        "{action} computer",
    ],
    "open_website": [
        "mở trang {website}",
        "vào {website}",
        "truy cập {website}",
        "{website}",
        "open {website}",
        "browse {website}",
    ],
}

# ✅ TĂNG DIVERSITY - Entities nhiều hơn gấp 3-4 lần
ENTITIES = {
    "file": [
        # Excel files
        "report.xlsx",
        "data.xlsx",
        "budget.xlsx",
        "sales.xlsx",
        "expense.xlsx",
        "inventory.xlsx",
        "payroll.xlsx",
        "bao_cao.xlsx",
        "du_lieu.xlsx",
        "bang_luong.xlsx",
        # Documents
        "presentation.pptx",
        "proposal.pptx",
        "slides.pptx",
        "document.docx",
        "contract.docx",
        "resume.docx",
        "tai_lieu.docx",
        "hop_dong.docx",
        "cv.docx",
        # Data files
        "data.json",
        "config.json",
        "settings.json",
        "database.db",
        "backup.sql",
        "log.txt",
        # Media
        "image.png",
        "photo.jpg",
        "screenshot.png",
        "video.mp4",
        "movie.avi",
        "clip.mkv",
        "hinh_anh.png",
        "anh.jpg",
        "video_clip.mp4",
        # Archives
        "backup.rar",
        "archive.zip",
        "package.tar.gz",
        "project.7z",
        "data_backup.zip",
        # Common Vietnamese names
        "bao_cao_thang_12.xlsx",
        "du_an_2024.docx",
        "anh_dai_dien.jpg",
        "video_huong_dan.mp4",
    ],
    "new_file": [
        "report_new.xlsx",
        "report_v2.xlsx",
        "report_final.xlsx",
        "data_updated.json",
        "data_2024.json",
        "data_backup.json",
        "presentation_final.pptx",
        "slides_v2.pptx",
        "bao_cao_moi.xlsx",
        "du_lieu_cap_nhat.json",
    ],
    "app": [
        # Microsoft
        "Excel",
        "Word",
        "PowerPoint",
        "Outlook",
        "Teams",
        "Microsoft Excel",
        "MS Word",
        "MS PowerPoint",
        # Browsers
        "Chrome",
        "Firefox",
        "Edge",
        "Safari",
        "Opera",
        "Google Chrome",
        "Cốc Cốc",
        # Media
        "VLC",
        "Spotify",
        "iTunes",
        "Windows Media Player",
        "Zing MP3",
        "NhacCuaTui",
        # Design
        "Photoshop",
        "Illustrator",
        "Figma",
        "Canva",
        # Other
        "Notepad",
        "Notepad++",
        "VS Code",
        "Sublime Text",
        "Calculator",
        "Paint",
        "Zoom",
        "Skype",
        "Zalo",
    ],
    "query": [
        # English songs
        "Faded",
        "Despacito",
        "Shape of You",
        "Hello",
        "Believer",
        "Someone Like You",
        "Closer",
        "Perfect",
        "Havana",
        # Vietnamese songs
        "Lạc Trôi",
        "Anh Ơi Ở Lại",
        "Nơi Này Có Anh",
        "Hãy Trao Cho Anh",
        "Chúng Ta Không Thuộc Về Nhau",
        # Searches
        "weather today",
        "news",
        "python tutorial",
        "thời tiết hôm nay",
        "tin tức",
        "cách nấu phở",
    ],
    "contact": [
        "Alice",
        "Bob",
        "Charlie",
        "David",
        "Emma",
        "John",
        "Mary",
        "Peter",
        "Sarah",
        "Tom",
        "An",
        "Bình",
        "Chi",
        "Dũng",
        "Hoa",
        "boss",
        "manager",
        "team",
        "client",
        "sếp",
        "quản lý",
        "khách hàng",
    ],
    "action": [
        "tắt",
        "khởi động lại",
        "sleep",
        "hibernate",
        "restart",
        "shutdown",
        "reboot",
        "log out",
        "đăng xuất",
        "khóa màn hình",
        "lock",
    ],
    "website": [
        "google.com",
        "facebook.com",
        "youtube.com",
        "github.com",
        "twitter.com",
        "linkedin.com",
        "instagram.com",
        "vnexpress.net",
        "dantri.com.vn",
        "zing.vn",
        "shopee.vn",
        "lazada.vn",
        "tiki.vn",
    ],
}

# ✅ TĂNG DIVERSITY - Prefixes & Suffixes gấp 3 lần
PREFIXES = [
    "",
    "em ",
    "tôi ",
    "mình ",
    "tôi muốn ",
    "em muốn ",
    "mình muốn ",
    "cho tôi ",
    "cho em ",
    "cho mình ",
    "giúp tôi ",
    "giúp em ",
    "giúp mình ",
    "làm ơn ",
    "xin ",
    "hãy ",
    "anh ơi ",
    "chị ơi ",
    "bạn ơi ",
    "có thể ",
    "cần ",
    "đang cần ",
]

SUFFIXES = [
    "",
    " đi",
    " nào",
    " ơi",
    " nhé",
    " nha",
    " được không",
    " được chứ",
    " được hem",
    " giúp tôi",
    " giúp em",
    " giúp mình",
    " với",
    " ngay",
    " luôn",
    " bây giờ",
    " đi nào",
    " nhanh lên",
    " đê",
    " đấy",
    " kìa",
    " à",
    " ạ",
]

# ✅ TĂNG Typo patterns
TYPO_PATTERNS = [
    (r"\bmở\b", ["mo", "mor", "mow"]),
    (r"\btắt\b", ["tat", "tatt", "tawt"]),
    (r"\bchạy\b", ["chay", "chaj", "chai"]),
    (r"\bfile\b", ["fiel", "fale", "fil"]),
    (r"\bđổi\b", ["doi", "doir", "doj"]),
    (r"\bphát\b", ["phat", "fat", "phatt"]),
    (r"\bnghe\b", ["nge", "ngeh", "nghe"]),
]

# ---------------------------
# 2️⃣ IMPROVED VARIANT GENERATION WITH DEDUPLICATION
# ---------------------------


def calculate_max_variants(template: str, entity_dict: dict) -> int:
    """Tính số unique combinations thực tế có thể"""
    placeholders = re.findall(r"\{(\w+)\}", template)

    entity_combos = 1
    for key in placeholders:
        if key in entity_dict:
            entity_combos *= len(entity_dict[key])

    prefix_suffix_combos = len(PREFIXES) * len(SUFFIXES)
    typo_multiplier = 1.2

    max_variants = int(entity_combos * prefix_suffix_combos * typo_multiplier)
    return max_variants


def apply_typo_safe(
    text: str, entity_positions: List[Dict], prob: float = 0.08
) -> Tuple[str, List[Dict]]:
    """Apply typos SAFELY without breaking entity positions"""
    if random.random() > prob or not TYPO_PATTERNS:
        return text, entity_positions

    pattern, typos = random.choice(TYPO_PATTERNS)
    matches = list(re.finditer(pattern, text))

    if not matches:
        return text, entity_positions

    # Filter safe matches
    safe_matches = []
    for match in matches:
        match_start, match_end = match.span()
        is_safe = True
        for ent in entity_positions:
            if not (match_end <= ent["start"] or match_start >= ent["end"]):
                is_safe = False
                break
        if is_safe:
            safe_matches.append(match)

    if not safe_matches:
        return text, entity_positions

    match = random.choice(safe_matches)
    typo = random.choice(typos)
    match_start, match_end = match.span()

    new_text = text[:match_start] + typo + text[match_end:]
    length_diff = len(typo) - (match_end - match_start)

    new_positions = []
    for ent in entity_positions:
        new_ent = ent.copy()
        if ent["start"] >= match_end:
            new_ent["start"] += length_diff
            new_ent["end"] += length_diff
        new_positions.append(new_ent)

    return new_text, new_positions


def add_natural_variations(text: str) -> List[str]:
    """Tạo biến thể ngữ pháp tự nhiên"""
    variations = [text]

    # Thêm từ nhấn mạnh
    if random.random() < 0.15:
        if not any(word in text for word in ["chính là", "đấy", "ấy"]):
            variations.append(f"{text} đấy")

    if random.random() < 0.1:
        variations.append(f"{text} luôn")

    # Thêm stopwords
    if random.random() < 0.15:
        stopwords = ["à", "ạ", "ý", "nè", "kìa", "nhỉ"]
        word = random.choice(stopwords)
        if word not in text:
            variations.append(f"{text} {word}")

    return variations


def generate_variants(
    template: str, entity_dict: dict, intent_name: str, n_variants: int = 500
) -> List[Dict]:
    """Generate variants with DEDUPLICATION and quality control"""

    # Calculate realistic max
    max_possible = calculate_max_variants(template, entity_dict)
    target_variants = min(n_variants, max_possible)

    # Use set for deduplication
    seen_texts = set()
    variants = []

    placeholder_pattern = r"\{(\w+)\}"
    placeholders = re.findall(placeholder_pattern, template)

    if not placeholders:
        # No entities - just text variations
        for _ in range(target_variants):
            prefix = random.choice(PREFIXES)
            suffix = random.choice(SUFFIXES)
            text = (prefix + template + suffix).strip()

            if text not in seen_texts:
                seen_texts.add(text)
                variants.append({"text": text, "intent": intent_name, "entities": []})
        return variants

    max_attempts = target_variants * 5
    attempts = 0

    while len(variants) < target_variants and attempts < max_attempts:
        attempts += 1

        # Select entity values (avoid duplicates in same template)
        entity_values = {}
        used_values = set()

        for key in placeholders:
            if key not in entity_dict:
                continue

            available = [v for v in entity_dict[key] if v not in used_values]
            if not available:
                available = entity_dict[key]

            value = random.choice(available)
            entity_values[key] = value
            used_values.add(value)

        # Replace placeholders and track positions
        text = template
        entities = []
        offset = 0

        for match in re.finditer(placeholder_pattern, template):
            placeholder = match.group(0)
            key = match.group(1)

            if key not in entity_values:
                continue

            value = entity_values[key]
            original_start = match.start()
            current_start = original_start + offset

            before = text[:current_start]
            after = text[current_start + len(placeholder) :]
            text = before + value + after

            entities.append(
                {
                    "start": current_start,
                    "end": current_start + len(value),
                    "entity": key.upper(),
                    "value": value,
                }
            )

            offset += len(value) - len(placeholder)

        # Add prefix/suffix
        prefix = random.choice(PREFIXES)
        suffix = random.choice(SUFFIXES)

        for ent in entities:
            ent["start"] += len(prefix)
            ent["end"] += len(prefix)

        text = prefix + text + suffix

        # Strip and adjust
        text_before_strip = text
        text = text.strip()
        left_strip = len(text_before_strip) - len(text_before_strip.lstrip())

        for ent in entities:
            ent["start"] -= left_strip
            ent["end"] -= left_strip

        # Apply typos
        text, entities = apply_typo_safe(text, entities)

        # Add natural variations
        text_variations = add_natural_variations(text)

        for var_text in text_variations:
            if var_text not in seen_texts and len(variants) < target_variants:
                seen_texts.add(var_text)
                variants.append(
                    {
                        "text": var_text,
                        "intent": intent_name,
                        "entities": entities.copy(),
                    }
                )

    return variants


# ---------------------------
# 3️⃣ GENERATE NLU DATA WITH STATS
# ---------------------------


def generate_nlu_data(
    intents: Dict, entities: Dict, n_per_template: int = 300
) -> Tuple[List[Dict], Dict]:
    """Generate NLU data with detailed statistics"""
    nlu_data = []
    stats = {
        "intents": {},
        "total_samples": 0,
        "unique_texts": 0,
        "duplicate_rate": 0,
    }

    all_texts = set()

    for intent_name, templates in intents.items():
        print(f"  → {intent_name:20s}", end=" ", flush=True)
        intent_samples = 0
        intent_unique = set()

        for template in templates:
            variants = generate_variants(
                template, entities, intent_name, n_per_template
            )

            for variant in variants:
                all_texts.add(variant["text"])
                intent_unique.add(variant["text"])

            nlu_data.extend(variants)
            intent_samples += len(variants)

        stats["intents"][intent_name] = {
            "samples": intent_samples,
            "unique": len(intent_unique),
            "templates": len(templates),
        }

        print(
            f"│ {intent_samples:>6,} samples │ {len(intent_unique):>6,} unique",
            flush=True,
        )

    stats["total_samples"] = len(nlu_data)
    stats["unique_texts"] = len(all_texts)
    stats["duplicate_rate"] = (
        (1 - len(all_texts) / len(nlu_data)) * 100 if nlu_data else 0
    )

    random.shuffle(nlu_data)
    return nlu_data, stats


# ---------------------------
# 4️⃣ VALIDATION & EXPORT
# ---------------------------


def validate_nlu_sample(sample: Dict) -> Tuple[bool, str]:
    """Validate NLU sample"""
    text = sample.get("text", "")
    entities = sample.get("entities", [])

    if not text or not text.strip():
        return False, "Empty text"

    for ent in entities:
        start = ent.get("start", -1)
        end = ent.get("end", -1)
        value = ent.get("value", "")

        if start < 0 or end > len(text) or start >= end:
            return False, f"Invalid position: [{start}:{end}]"

        actual_value = text[start:end]
        if actual_value != value:
            return False, f"Mismatch: expected '{value}' got '{actual_value}'"

    return True, ""


def save_nlu_jsonl(nlu_data: List[Dict], path: str = "dataset/nlu.jsonl") -> int:
    """Save NLU data with validation"""
    Path("dataset").mkdir(exist_ok=True)

    valid_samples = []
    invalid_samples = []

    for sample in nlu_data:
        is_valid, error = validate_nlu_sample(sample)
        if is_valid:
            valid_samples.append(sample)
        else:
            invalid_samples.append((sample, error))

    if invalid_samples:
        print(f"\n  ⚠️  Found {len(invalid_samples):,} invalid samples (skipped)")

    with open(path, "w", encoding="utf-8") as f:
        for item in valid_samples:
            json_line = {
                "text": item["text"],
                "intent": item["intent"],
                "entities": [
                    {
                        "start": e["start"],
                        "end": e["end"],
                        "entity": e["entity"],
                        "value": e["value"],
                    }
                    for e in item["entities"]
                ],
            }
            f.write(json.dumps(json_line, ensure_ascii=False) + "\n")

    return len(valid_samples)


def analyze_dataset_quality(nlu_data: List[Dict]) -> Dict:
    """Phân tích chất lượng dataset"""
    analysis = {
        "total_samples": len(nlu_data),
        "unique_texts": len(set(s["text"] for s in nlu_data)),
        "avg_text_length": sum(len(s["text"]) for s in nlu_data) / len(nlu_data),
        "samples_with_entities": sum(1 for s in nlu_data if s["entities"]),
        "intent_distribution": defaultdict(int),
        "entity_type_distribution": defaultdict(int),
    }

    for sample in nlu_data:
        analysis["intent_distribution"][sample["intent"]] += 1
        for ent in sample["entities"]:
            analysis["entity_type_distribution"][ent["entity"]] += 1

    return analysis


def save_domain_yaml(intents: Dict, entities: Dict, path: str = "dataset/domain.yml"):
    """Save domain configuration"""
    domain = {
        "version": "3.1",
        "intents": list(intents.keys()),
        "entities": [e.upper() for e in entities.keys()],
        "slots": {
            ent.upper(): {"type": "text", "influence_conversation": True}
            for ent in entities.keys()
        },
        "responses": {
            "utter_ask_file": [{"text": "Bạn muốn mở file nào?"}],
            "utter_ask_app": [{"text": "Bạn muốn mở bằng app nào?"}],
            "utter_ask_query": [{"text": "Bạn muốn nghe bài nào?"}],
            "utter_confirm_action": [{"text": "Đang thực hiện {intent}"}],
        },
    }
    Path("dataset").mkdir(exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(domain, f, allow_unicode=True, sort_keys=False)


# ---------------------------
# 5️⃣ MULTI-TURN SESSIONS
# ---------------------------


def generate_contextual_session(intent: str, entities_dict: Dict) -> List[Dict]:
    """Generate realistic multi-turn conversations"""
    session = []

    if intent == "open_file":
        scenario = random.choice(
            ["complete", "missing_file", "missing_app", "missing_both"]
        )

        if scenario == "complete":
            file = random.choice(entities_dict["file"])
            app = random.choice(entities_dict["app"])
            session.append({"role": "user", "text": f"mở {file} bằng {app}"})
            session.append({"role": "assistant", "text": f"Đang mở {file} bằng {app}"})

        elif scenario == "missing_file":
            app = random.choice(entities_dict["app"])
            session.append({"role": "user", "text": f"mở file bằng {app}"})
            session.append({"role": "assistant", "text": "File nào bạn muốn mở?"})
            file = random.choice(entities_dict["file"])
            session.append({"role": "user", "text": file})
            session.append({"role": "assistant", "text": f"Đang mở {file} bằng {app}"})

        elif scenario == "missing_app":
            file = random.choice(entities_dict["file"])
            session.append({"role": "user", "text": f"mở {file}"})
            session.append({"role": "assistant", "text": "Bạn muốn mở bằng app nào?"})
            app = random.choice(entities_dict["app"])
            session.append({"role": "user", "text": app})
            session.append({"role": "assistant", "text": f"Đang mở {file} bằng {app}"})

        else:  # missing_both
            session.append({"role": "user", "text": "mở file giúp tôi"})
            session.append({"role": "assistant", "text": "Bạn muốn mở file nào?"})
            file = random.choice(entities_dict["file"])
            session.append({"role": "user", "text": file})
            session.append({"role": "assistant", "text": "Bạn muốn mở bằng app nào?"})
            app = random.choice(entities_dict["app"])
            session.append({"role": "user", "text": app})
            session.append({"role": "assistant", "text": f"Đang mở {file} bằng {app}"})

    elif intent == "play_music":
        scenario = random.choice(["complete", "missing_query", "with_app"])

        if scenario == "complete":
            query = random.choice(entities_dict["query"])
            session.append({"role": "user", "text": f"phát nhạc {query}"})
            session.append({"role": "assistant", "text": f"Đang phát {query}"})

        elif scenario == "missing_query":
            session.append({"role": "user", "text": "phát nhạc đi"})
            session.append({"role": "assistant", "text": "Bạn muốn nghe bài nào?"})
            query = random.choice(entities_dict["query"])
            session.append({"role": "user", "text": query})
            session.append({"role": "assistant", "text": f"Đang phát {query}"})

        else:  # with_app
            query = random.choice(entities_dict["query"])
            app = random.choice(["Spotify", "VLC"])
            session.append({"role": "user", "text": f"cho tôi nghe {query} trên {app}"})
            session.append(
                {"role": "assistant", "text": f"Đang phát {query} trên {app}"}
            )

    elif intent == "rename_file":
        file = random.choice(entities_dict["file"])
        new_file = random.choice(entities_dict["new_file"])
        session.append({"role": "user", "text": f"đổi tên {file} thành {new_file}"})
        session.append(
            {"role": "assistant", "text": f"Đã đổi tên {file} thành {new_file}"}
        )

    else:
        # Simple intent - direct execution
        template = random.choice(INTENTS[intent])
        text = template

        # Replace placeholders
        for ent_type, values in entities_dict.items():
            placeholder = f"{{{ent_type}}}"
            if placeholder in text:
                text = text.replace(placeholder, random.choice(values))

        session.append({"role": "user", "text": text})
        session.append(
            {"role": "assistant", "text": f"Đã thực hiện {intent.replace('_', ' ')}"}
        )

    return session


def generate_multi_turn_sessions(
    intents: Dict, entities: Dict, n_sessions: int = 10000
) -> List[Dict]:
    """Generate diverse multi-turn sessions"""
    sessions = []
    intent_keys = list(intents.keys())

    print(f"\n🔄 Generating {n_sessions:,} multi-turn sessions...")

    for i in range(n_sessions):
        intent = random.choice(intent_keys)
        session = generate_contextual_session(intent, entities)
        sessions.append(
            {"session_id": f"sess_{i:06d}", "intent": intent, "turns": session}
        )

        if (i + 1) % 2500 == 0:
            print(f"   Progress: {i + 1:,}/{n_sessions:,} sessions", flush=True)

    return sessions


def save_multi_turn_json(sessions: List[Dict], path: str = "dataset/multi_turn.json"):
    """Save multi-turn sessions"""
    Path("dataset").mkdir(exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(sessions, f, ensure_ascii=False, indent=2)


# ---------------------------
# 6️⃣ MAIN
# ---------------------------

if __name__ == "__main__":
    # ========================================
    # 🎯 CONFIG - OPTIMIZED FOR QUALITY
    # ========================================
    N_PER_TEMPLATE = 300  # 300 variants per template (down from 5000!)
    N_SESSIONS = 10000  # Multi-turn sessions
    # With 54 templates: 54 × 300 = ~16K samples
    # But HIGH QUALITY with minimal duplicates!
    # ========================================

    print("=" * 70)
    print("🚀 OPTIMIZED NLU DATASET GENERATOR")
    print("=" * 70)

    # Calculate expected output
    total_intents = len(INTENTS)
    total_templates = sum(len(templates) for templates in INTENTS.values())
    expected_samples = total_templates * N_PER_TEMPLATE

    print(f"\n📊 Configuration:")
    print(f"   - Intents: {total_intents}")
    print(f"   - Templates: {total_templates}")
    print(f"   - Variants per template: {N_PER_TEMPLATE}")
    print(f"   - Expected samples: ~{expected_samples:,}")
    print(f"   - Entity types: {len(ENTITIES)}")
    print(f"   - Total entity values: {sum(len(v) for v in ENTITIES.values())}")

    # Generate NLU data
    print(f"\n🔄 Generating NLU data...")
    print(f"{'Intent':<20} │ {'Samples':>8} │ {'Unique':>8}")
    print("─" * 70)

    nlu_data, stats = generate_nlu_data(
        INTENTS, ENTITIES, n_per_template=N_PER_TEMPLATE
    )

    print("─" * 70)
    print(f"{'TOTAL':<20} │ {stats['total_samples']:>8,} │ {stats['unique_texts']:>8,}")

    # Analyze quality
    print(f"\n📊 Dataset Quality Analysis:")
    analysis = analyze_dataset_quality(nlu_data)
    print(f"   - Total samples: {analysis['total_samples']:,}")
    print(f"   - Unique texts: {analysis['unique_texts']:,}")
    print(f"   - Duplicate rate: {stats['duplicate_rate']:.2f}%")
    print(f"   - Avg text length: {analysis['avg_text_length']:.1f} chars")
    print(
        f"   - Samples with entities: {analysis['samples_with_entities']:,} ({analysis['samples_with_entities']/analysis['total_samples']*100:.1f}%)"
    )

    # Save NLU data
    print(f"\n💾 Saving NLU data...")
    valid_count = save_nlu_jsonl(nlu_data)
    print(f"✅ Saved {valid_count:,} samples to dataset/nlu.jsonl")

    # Save domain config
    print(f"\n💾 Saving domain configuration...")
    save_domain_yaml(INTENTS, ENTITIES)
    print(f"✅ Saved domain.yml")

    # Generate multi-turn sessions
    print(f"\n" + "=" * 70)
    sessions = generate_multi_turn_sessions(INTENTS, ENTITIES, n_sessions=N_SESSIONS)

    print(f"\n💾 Saving multi-turn sessions...")
    save_multi_turn_json(sessions)
    print(f"✅ Saved {len(sessions):,} sessions to dataset/multi_turn.json")

    # Final summary with quality metrics
    print("\n" + "=" * 70)
    print("📊 FINAL SUMMARY")
    print("=" * 70)
    print(f"   ✓ NLU samples: {valid_count:,}")
    print(f"   ✓ Unique samples: {stats['unique_texts']:,}")
    print(
        f"   ✓ Duplicate rate: {stats['duplicate_rate']:.2f}% ({'✅ EXCELLENT' if stats['duplicate_rate'] < 5 else '⚠️  HIGH'})"
    )
    print(f"   ✓ Multi-turn sessions: {len(sessions):,}")
    print(f"   ✓ Intents: {len(INTENTS)}")
    print(f"   ✓ Entity types: {len(ENTITIES)}")
    print(f"   ✓ Average samples per intent: {valid_count // len(INTENTS):,}")
    print("=" * 70)
    print("✨ Dataset generation complete!")
    print("=" * 70)

    # Tips
    print("\n💡 Next Steps:")
    print("   1. Review dataset/nlu.jsonl to check quality")
    print("   2. Review dataset/multi_turn.json for conversation flows")
    print("   3. If duplicate rate < 5%: Ready to train! 🚀")
    print("   4. If need more data: Increase N_PER_TEMPLATE to 500-800")
    print("   5. Train with: 80% train / 10% validation / 10% test split")
