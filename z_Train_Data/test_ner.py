"""Test PhoBERT NER model với nhiều ví dụ"""

import json
import torch
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForTokenClassification


def load_phobert_ner(model_path="phobert_ner_model"):
    """Load PhoBERT NER model và tokenizer"""
    model_path = Path(model_path)

    print(f"Đang tải mô hình từ {model_path}...")

    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(str(model_path), use_fast=False)

    # Load model
    model = AutoModelForTokenClassification.from_pretrained(str(model_path))
    model.eval()

    # Load labels
    labels_path = model_path / "labels.json"
    with open(labels_path, "r", encoding="utf-8") as f:
        labels_data = json.load(f)
        label_list = labels_data["labels"]

    id2label = {i: label for i, label in enumerate(label_list)}

    print(f"✅ Đã tải mô hình thành công!")
    print(f"   - Labels: {len(label_list)} loại")

    return tokenizer, model, id2label


def predict_entities(text, tokenizer, model, id2label):
    """Dự đoán entities trong text"""
    # Tokenize
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=128)

    # Predict
    with torch.no_grad():
        outputs = model(**inputs)
        predictions = torch.argmax(outputs.logits, dim=2)

    # Convert tokens và labels
    tokens = tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])
    pred_labels = [id2label[p.item()] for p in predictions[0]]

    # Extract entities
    entities = []
    current_entity = None
    current_text = ""

    for token, label in zip(tokens, pred_labels):
        # Skip special tokens
        if token in ["<s>", "</s>", "<pad>", "<unk>"]:
            continue

        # Clean token
        clean_token = token.replace("@@", "").replace("Ġ", " ").strip()

        if label.startswith("B-"):
            # Lưu entity trước đó
            if current_entity:
                entities.append({"text": current_text.strip(), "label": current_entity})

            # Bắt đầu entity mới
            current_entity = label[2:]  # Bỏ "B-"
            current_text = clean_token

        elif label.startswith("I-") and current_entity:
            # Tiếp tục entity hiện tại
            if clean_token:
                current_text += clean_token

        else:  # "O"
            # Kết thúc entity
            if current_entity:
                entities.append({"text": current_text.strip(), "label": current_entity})
                current_entity = None
                current_text = ""

    # Lưu entity cuối cùng
    if current_entity:
        entities.append({"text": current_text.strip(), "label": current_entity})

    return entities


def test_ner_model(model_path="phobert_ner_model"):
    """Kiểm tra mô hình NER đã huấn luyện với nhiều ví dụ"""

    try:
        tokenizer, model, id2label = load_phobert_ner(model_path)
    except Exception as e:
        print(f"❌ Lỗi khi tải mô hình: {e}")
        return

    # Ví dụ kiểm tra
    test_examples = [
        "mở notepad",
        "tìm file Báo cáo.docx trong ổ D",
        "tìm bài hát Yesterday trên youtube",
        "mở file update.xlsx trong thư mục Tài liệu bằng excel",
        "mở file trong thư mục Tài liệu",
        "tìm tài liệu trong ổ D",
        "xem video Yesterday trên youtube",
        "mở ứng dụng word",
        "mở excel",
        "mở word",
        "mở powerpoint",
        "tìm file excel trong thư mục Downloads",
        "mở file report.xlsx bằng excel",
    ]

    # Kiểm tra và hiển thị kết quả
    results = {}

    print("\n" + "=" * 70)
    print("KẾT QUẢ NHẬN DẠNG THỰC THỂ")
    print("=" * 70 + "\n")

    for text in test_examples:
        entities = predict_entities(text, tokenizer, model, id2label)

        print(f"📝 Command: {text}")

        if len(entities) == 0:
            print("   ⚠️  Không nhận diện được thực thể nào")
        else:
            for ent in entities:
                print(f"   ✅ [{ent['label']:12s}] {ent['text']}")

        results[text] = entities
        print("")

    # Lưu kết quả vào file JSON
    output_file = "ner_test_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"💾 Đã lưu kết quả vào '{output_file}'")

    # Kiểm tra các trường hợp đặc biệt
    specific_tests = {
        "notepad_test": {"text": "mở notepad", "expected": ["APP"]},
        "youtube_test": {
            "text": "tìm bài hát Yesterday trên youtube",
            "expected": ["QUERY", "APP"],
        },
        "file_path_test": {
            "text": "mở file report.xlsx bằng excel",
            "expected": ["FILE", "APP"],
        },
    }

    print("\n" + "=" * 70)
    print("KIỂM TRA CÁC TRƯỜNG HỢP ĐẶC BIỆT")
    print("=" * 70 + "\n")

    for test_name, test_info in specific_tests.items():
        test_text = test_info["text"]
        expected_labels = test_info["expected"]

        entities = predict_entities(test_text, tokenizer, model, id2label)
        found_labels = [ent["label"] for ent in entities]

        success = all(label in found_labels for label in expected_labels)

        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} - {test_name}")
        print(f"   Câu: '{test_text}'")
        print(f"   Kỳ vọng: {expected_labels}")
        print(f"   Tìm thấy: {found_labels}")
        print(f"   Entities: {[(e['text'], e['label']) for e in entities]}")
        print("")

    # Thống kê
    print("=" * 70)
    print("THỐNG KÊ")
    print("=" * 70)

    total_tests = len(test_examples)
    tests_with_entities = sum(1 for ents in results.values() if len(ents) > 0)
    tests_without_entities = total_tests - tests_with_entities

    print(f"   Tổng số test: {total_tests}")
    print(
        f"   Có entities: {tests_with_entities} ({tests_with_entities/total_tests*100:.1f}%)"
    )
    print(
        f"   Không có entities: {tests_without_entities} ({tests_without_entities/total_tests*100:.1f}%)"
    )

    # Đếm loại entities
    entity_counts = {}
    for ents in results.values():
        for ent in ents:
            label = ent["label"]
            entity_counts[label] = entity_counts.get(label, 0) + 1

    if entity_counts:
        print(f"\n   Phân bố entity types:")
        for label, count in sorted(entity_counts.items(), key=lambda x: -x[1]):
            print(f"      - {label:12s}: {count:3d} lần")

    print("\n✨ Hoàn thành!")


if __name__ == "__main__":
    test_ner_model()
