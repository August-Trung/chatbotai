import spacy
import json

def test_ner_model(model_path="improved_ner_vi/best_model"):
    """
    Kiểm tra mô hình NER đã huấn luyện với nhiều ví dụ
    """
    # Tải mô hình
    try:
        nlp = spacy.load(model_path)
        print(f"Đã tải mô hình từ {model_path}")
    except Exception as e:
        print(f"Lỗi khi tải mô hình: {e}")
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
    
    print("\n=== KẾT QUẢ NHẬN DẠNG THỰC THỂ ===\n")
    
    for text in test_examples:
        doc = nlp(text)
        print(f"Command: {text}")
        
        entities = []
        if len(doc.ents) == 0:
            print(" - Không nhận diện được thực thể nào")
        else:
            for ent in doc.ents:
                print(f" - {ent.text}: {ent.label_}")
                entities.append({"text": ent.text, "label": ent.label_, "start": ent.start_char, "end": ent.end_char})
        
        results[text] = entities
        print("")  # Dòng trống để dễ đọc
    
    # Lưu kết quả vào file JSON để phân tích chi tiết
    with open("ner_test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("Đã lưu kết quả kiểm tra vào file 'ner_test_results.json'")
    
    # Thực hiện đánh giá thủ công một số trường hợp đặc biệt
    specific_tests = {
        "notepad_test": ("mở notepad", ["APP"]),
        "youtube_test": ("tìm bài hát Yesterday trên youtube", ["QUERY", "APP"]),
        "path_test": ("mở file trong thư mục Tài liệu", ["FILE", "PATH"]),
    }
    
    print("\n=== KIỂM TRA CÁC TRƯỜNG HỢP ĐẶC BIỆT ===\n")
    
    for test_name, (test_text, expected_labels) in specific_tests.items():
        doc = nlp(test_text)
        found_labels = [ent.label_ for ent in doc.ents]
        
        success = all(label in found_labels for label in expected_labels)
        
        print(f"Test '{test_name}': {'PASSED' if success else 'FAILED'}")
        print(f" - Câu: '{test_text}'")
        print(f" - Kỳ vọng: {expected_labels}")
        print(f" - Tìm thấy: {found_labels}")
        print(f" - Thực thể: {[(ent.text, ent.label_) for ent in doc.ents]}")
        print("")

if __name__ == "__main__":
    test_ner_model()