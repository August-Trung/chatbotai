# -*- coding: utf-8 -*-
import json, random, re
from pathlib import Path
import yaml
from typing import List, Dict, Tuple

# ---------------------------
# 1️⃣ INTENTS, ENTITIES & TEMPLATES
# ---------------------------

INTENTS = {
    "open_app": [
        "mở {app}",
        "chạy {app}",
        "khởi động {app}",
        "bật {app} lên",
        "{app} đi",
        "cho tôi {app}",
    ],
    "close_app": ["tắt {app}", "đóng {app}", "kill {app}", "thoát {app}"],
    "open_file": [
        "mở file {file}",
        "mở {file}",
        "chạy file {file}",
        "bật file {file}",
        "{file} đi",
        "cho tôi xem {file}",
    ],
    "delete_file": ["xóa file {file}", "delete {file}", "xóa {file} đi"],
    "copy_file": ["sao chép {file}", "copy {file}", "nhân bản {file}"],
    "rename_file": [
        "đổi tên {file} thành {new_file}",
        "rename {file} sang {new_file}",
        "đổi {file} thành {new_file}",
    ],
    "play_music": [
        "phát nhạc {query}",
        "nghe bài {query}",
        "play {query}",
        "cho tôi nghe {query}",
        "bật nhạc {query}",
    ],
    "search_web": [
        "tìm {query} trên web",
        "search {query}",
        "google {query}",
        "tìm kiếm {query}",
    ],
    "send_email": [
        "gửi email đến {contact}",
        "mail {contact}",
        "gửi mail cho {contact}",
    ],
    "system_control": [
        "{action} máy",
        "{action} máy tính",
        "{action} pc",
        "{action} laptop",
    ],
    "open_website": [
        "mở trang {website}",
        "vào {website}",
        "truy cập {website}",
        "{website} đi",
    ],
}

ENTITIES = {
    "file": [
        "report.xlsx",
        "data.json",
        "presentation.pptx",
        "backup.rar",
        "image.png",
    ],
    "new_file": ["report_new.xlsx", "data_updated.json", "final_presentation.pptx"],
    "app": ["Excel", "VLC", "Spotify", "Chrome", "Word", "Notepad", "Photoshop"],
    "query": ["Faded", "Despacito", "Shape of You", "Hello", "Believer"],
    "contact": ["Alice", "Bob", "Charlie", "David", "Emma"],
    "action": ["tắt", "khởi động lại", "sleep", "hibernate", "restart", "shutdown"],
    "website": ["google.com", "facebook.com", "youtube.com", "github.com"],
}

# Natural variations
PREFIXES = ["", "em ", "tôi muốn ", "cho tôi ", "giúp tôi ", "làm ơn "]
SUFFIXES = ["", " đi", " nào", " giúp tôi", " được không", " nhé", " ơi"]

# Typo simulation (Vietnamese common mistakes)
TYPO_PATTERNS = [
    (r"\bmở\b", ["mo", "mor"]),
    (r"\btắt\b", ["tat", "tatt"]),
    (r"\bchạy\b", ["chay", "chaj"]),
    (r"\bfile\b", ["fiel", "fale"]),
    (r"\bđổi\b", ["doi", "doir"]),
]

# ---------------------------
# 2️⃣ IMPROVED VARIANT GENERATION
# ---------------------------


def apply_typo_safe(
    text: str, entity_positions: List[Dict], prob: float = 0.05
) -> Tuple[str, List[Dict]]:
    """
    Apply typos SAFELY without breaking entity positions
    Returns: (modified_text, updated_entity_positions)
    """
    if random.random() > prob or not TYPO_PATTERNS:
        return text, entity_positions

    # Try to apply typo to non-entity parts only
    pattern, typos = random.choice(TYPO_PATTERNS)
    matches = list(re.finditer(pattern, text))

    if not matches:
        return text, entity_positions

    # Filter matches that don't overlap with entities
    safe_matches = []
    for match in matches:
        match_start, match_end = match.span()
        is_safe = True
        for ent in entity_positions:
            # Check if match overlaps with entity
            if not (match_end <= ent["start"] or match_start >= ent["end"]):
                is_safe = False
                break
        if is_safe:
            safe_matches.append(match)

    if not safe_matches:
        return text, entity_positions

    # Apply typo to a random safe match
    match = random.choice(safe_matches)
    typo = random.choice(typos)
    match_start, match_end = match.span()

    # Replace and adjust entity positions
    new_text = text[:match_start] + typo + text[match_end:]
    length_diff = len(typo) - (match_end - match_start)

    # Update entity positions that come after the typo
    new_positions = []
    for ent in entity_positions:
        new_ent = ent.copy()
        if ent["start"] >= match_end:
            new_ent["start"] += length_diff
            new_ent["end"] += length_diff
        new_positions.append(new_ent)

    return new_text, new_positions


def generate_variants(
    template: str, entity_dict: dict, intent_name: str, n_variants: int = 50
) -> List[Dict]:
    """
    Generate natural variants with CORRECT entity tracking

    Algorithm:
    1. Find all placeholders in template
    2. Replace placeholders ONE BY ONE while tracking positions
    3. Add prefix/suffix and adjust positions
    4. Apply typos safely
    """
    # Find all entity placeholders in template
    placeholder_pattern = r"\{(\w+)\}"
    placeholders = re.findall(placeholder_pattern, template)

    if not placeholders:
        # No entities - just generate text variations
        variants = []
        for _ in range(n_variants):
            prefix = random.choice(PREFIXES)
            suffix = random.choice(SUFFIXES)
            text = (prefix + template + suffix).strip()
            variants.append({"text": text, "intent": intent_name, "entities": []})
        return variants

    variants = []

    for _ in range(n_variants):
        # Select entity values (avoid duplicates in same template)
        entity_values = {}
        used_values = set()

        for key in placeholders:
            if key not in entity_dict:
                continue

            # Get values that haven't been used yet
            available = [v for v in entity_dict[key] if v not in used_values]
            if not available:
                available = entity_dict[key]

            value = random.choice(available)
            entity_values[key] = value
            used_values.add(value)

        # Replace placeholders and track entity positions
        text = template
        entities = []
        offset = 0  # Track how much text length has changed

        # Find and replace each placeholder in order
        for match in re.finditer(placeholder_pattern, template):
            placeholder = match.group(0)  # e.g., "{file}"
            key = match.group(1)  # e.g., "file"

            if key not in entity_values:
                continue

            value = entity_values[key]

            # Calculate position in current text (accounting for previous replacements)
            original_start = match.start()
            current_start = original_start + offset

            # Find and replace the placeholder in current text
            before = text[:current_start]
            after = text[current_start + len(placeholder) :]
            text = before + value + after

            # Record entity position
            entities.append(
                {
                    "start": current_start,
                    "end": current_start + len(value),
                    "entity": key.upper(),
                    "value": value,
                }
            )

            # Update offset for next replacements
            offset += len(value) - len(placeholder)

        # Add natural prefix/suffix
        prefix = random.choice(PREFIXES)
        suffix = random.choice(SUFFIXES)

        # Adjust entity positions for prefix
        for ent in entities:
            ent["start"] += len(prefix)
            ent["end"] += len(prefix)

        # Combine text
        text = prefix + text + suffix

        # Strip and adjust positions
        text_before_strip = text
        text = text.strip()

        # Calculate how many chars were stripped from the left
        left_strip = len(text_before_strip) - len(text_before_strip.lstrip())

        # Adjust entity positions
        for ent in entities:
            ent["start"] -= left_strip
            ent["end"] -= left_strip

        # Apply typos safely
        text, entities = apply_typo_safe(text, entities)

        variants.append({"text": text, "intent": intent_name, "entities": entities})

    return variants


# ---------------------------
# 3️⃣ GENERATE NLU DATA
# ---------------------------


def generate_nlu_data(
    intents: Dict, entities: Dict, n_per_template: int = 5000
) -> List[Dict]:
    """Generate NLU training data with progress tracking"""
    nlu_data = []

    for intent_name, templates in intents.items():
        print(f"  → Generating {intent_name}...", end=" ", flush=True)
        intent_samples = 0

        for template in templates:
            variants = generate_variants(
                template, entities, intent_name, n_per_template
            )
            nlu_data.extend(variants)
            intent_samples += len(variants)

        print(f"{intent_samples:,} samples")

    random.shuffle(nlu_data)
    return nlu_data


# ---------------------------
# 4️⃣ IMPROVED MULTI-TURN SESSIONS
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
    intents: Dict, entities: Dict, n_sessions: int = 50000
) -> List[Dict]:
    """Generate diverse multi-turn sessions with progress tracking"""
    sessions = []
    intent_keys = list(intents.keys())

    print(f"  → Generating {n_sessions:,} sessions...")
    for i in range(n_sessions):
        intent = random.choice(intent_keys)
        session = generate_contextual_session(intent, entities)
        sessions.append(
            {"session_id": f"sess_{i:06d}", "intent": intent, "turns": session}
        )

        if (i + 1) % 10000 == 0:
            print(f"     Progress: {i + 1:,}/{n_sessions:,} sessions", flush=True)

    return sessions


# ---------------------------
# 5️⃣ EXPORT FILES WITH VALIDATION
# ---------------------------


def validate_nlu_sample(sample: Dict) -> Tuple[bool, str]:
    """
    Validate a single NLU sample
    Returns: (is_valid, error_message)
    """
    text = sample.get("text", "")
    entities = sample.get("entities", [])

    # Check text is not empty
    if not text or not text.strip():
        return False, "Empty text"

    # Validate entity positions
    for ent in entities:
        start = ent.get("start", -1)
        end = ent.get("end", -1)
        value = ent.get("value", "")

        if start < 0 or end > len(text) or start >= end:
            return (
                False,
                f"Invalid position: start={start}, end={end}, text_len={len(text)}",
            )

        # Check if entity value matches text at position
        actual_value = text[start:end]
        if actual_value != value:
            return (
                False,
                f"Position mismatch: expected '{value}' but found '{actual_value}' at [{start}:{end}]",
            )

    return True, ""


def save_nlu_jsonl(
    nlu_data: List[Dict], path: str = "dataset/nlu.jsonl", debug_invalid: bool = False
):
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

    invalid_count = len(invalid_samples)

    if invalid_count > 0:
        print(f"  ⚠️  Found {invalid_count:,} invalid samples")

        if debug_invalid and invalid_count > 0:
            print(f"\n  🔍 Debug: First 5 invalid samples:")
            for sample, error in invalid_samples[:5]:
                print(f"     ❌ {error}")
                print(f"        Text: {sample['text']}")
                print(f"        Entities: {sample['entities']}\n")

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


def save_multi_turn_json(sessions: List[Dict], path: str = "dataset/multi_turn.json"):
    """Save multi-turn sessions"""
    Path("dataset").mkdir(exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(sessions, f, ensure_ascii=False, indent=2)


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
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(domain, f, allow_unicode=True, sort_keys=False)


# ---------------------------
# 6️⃣ MAIN
# ---------------------------

if __name__ == "__main__":
    # ========================================
    # 🎯 CONFIG: ĐIỀU CHỈNH Ở ĐÂY
    # ========================================
    TARGET_NLU_SAMPLES = 3_000_000  # Muốn 2.5M → đổi thành 2_500_000
    TARGET_SESSIONS = 100_000  # Số session multi-turn
    DEBUG_INVALID = False  # Set True để xem invalid samples
    # ========================================

    print("=" * 60)
    print("🚀 NLU DATASET GENERATOR")
    print("=" * 60)

    # Calculate configuration
    total_intents = len(INTENTS)
    total_templates = sum(len(templates) for templates in INTENTS.values())
    n_per_template = TARGET_NLU_SAMPLES // total_templates

    print(f"\n📊 Configuration:")
    print(f"   - Target samples: {TARGET_NLU_SAMPLES:,}")
    print(f"   - Total intents: {total_intents}")
    print(f"   - Total templates: {total_templates}")
    print(f"   - Samples per template: {n_per_template:,}")
    print(f"   - Expected output: ~{total_templates * n_per_template:,} samples")

    # Generate NLU data
    print(f"\n🔄 Generating NLU data...")
    nlu_data = generate_nlu_data(INTENTS, ENTITIES, n_per_template=n_per_template)

    print(f"\n💾 Saving NLU data...")
    valid_count = save_nlu_jsonl(nlu_data, debug_invalid=DEBUG_INVALID)
    print(f"✅ Saved {valid_count:,} valid NLU samples to dataset/nlu.jsonl")

    # Generate multi-turn sessions
    print(f"\n🔄 Generating multi-turn sessions...")
    sessions = generate_multi_turn_sessions(
        INTENTS, ENTITIES, n_sessions=TARGET_SESSIONS
    )

    print(f"\n💾 Saving multi-turn sessions...")
    save_multi_turn_json(sessions)
    print(f"✅ Saved {len(sessions):,} sessions to dataset/multi_turn.json")

    # Save domain config
    print(f"\n💾 Saving domain configuration...")
    save_domain_yaml(INTENTS, ENTITIES)
    print(f"✅ Saved domain.yml")

    # Final summary
    print("\n" + "=" * 60)
    print("📊 DATASET SUMMARY")
    print("=" * 60)
    print(f"   ✓ NLU samples: {valid_count:,}")
    print(f"   ✓ Multi-turn sessions: {len(sessions):,}")
    print(f"   ✓ Intents: {len(INTENTS)}")
    print(f"   ✓ Entity types: {len(ENTITIES)}")
    print(f"   ✓ Total templates: {total_templates}")
    print("=" * 60)
    print("✨ Dataset generation complete!")
    print("=" * 60)
