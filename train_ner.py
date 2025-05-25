import spacy
from spacy.training import Example
from spacy.util import minibatch, compounding
from pathlib import Path
import random
import json
from sklearn.model_selection import train_test_split
from tqdm import tqdm
import numpy as np
from generated_train_data import TRAIN_DATA, VALID_DATA

def create_and_train_ner_model(train_data, valid_data=None, output_dir="./improved_ner_vi", 
                              n_iter=100, batch_size=8, dropout_rate=0.25):
    """
    Tạo và huấn luyện mô hình NER với các tham số tối ưu.
    """
    # Tạo mô hình trống với pipeline NER
    nlp = spacy.blank("vi")
    
    # Tạo NER pipeline
    if "ner" not in nlp.pipe_names:
        ner = nlp.add_pipe("ner")
    else:
        ner = nlp.get_pipe("ner")
    
    # Thêm các nhãn từ dữ liệu huấn luyện
    for _, annotations in train_data:
        for ent in annotations.get("entities", []):
            ner.add_label(ent[2])
    
    # Khởi tạo các pipe khác và loại trừ chúng khỏi quá trình huấn luyện
    pipe_exceptions = ["ner", "trf_wordpiecer", "trf_tok2vec"]
    other_pipes = [pipe for pipe in nlp.pipe_names if pipe not in pipe_exceptions]
    
    # Chỉ huấn luyện NER
    with nlp.disable_pipes(*other_pipes):
        # Chuẩn bị optimizer
        optimizer = nlp.begin_training()
        optimizer.learn_rate = 0.0001  # Giảm learning rate để học chi tiết hơn
        
        # Theo dõi loss để phát hiện early stopping
        best_loss = float('inf')
        no_improvement = 0
        patience = 10  # Số epochs không cải thiện trước khi dừng
        
        # Tạo thư mục đầu ra nếu chưa tồn tại
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Hiển thị tiến trình huấn luyện
        print("Bắt đầu huấn luyện...")
        for i in tqdm(range(n_iter)):
            # Xáo trộn dữ liệu mỗi vòng lặp
            random.shuffle(train_data)
            losses = {}
            
            # Batch compounding: bắt đầu với batch nhỏ và tăng dần
            batches = minibatch(train_data, size=compounding(4, batch_size, 1.001))
            for batch in batches:
                # Chuyển đổi định dạng dữ liệu cho spaCy
                examples = []
                for text, annotations in batch:
                    doc = nlp.make_doc(text)
                    example = Example.from_dict(doc, annotations)
                    examples.append(example)
                
                # Cập nhật mô hình
                nlp.update(
                    examples,
                    drop=dropout_rate,  # Dropout để giảm overfitting
                    losses=losses,
                    sgd=optimizer,
                )
            
            # Đánh giá trên tập validation mỗi 10 vòng lặp
            if valid_data and i % 10 == 0:
                eval_results = evaluate_model(nlp, valid_data)
                print(f"Epoch {i}, Loss: {losses['ner']:.4f}, Precision: {eval_results['precision']:.4f}, "
                      f"Recall: {eval_results['recall']:.4f}, F1: {eval_results['f1']:.4f}")
                
                # Kiểm tra early stopping
                current_loss = losses["ner"]
                if current_loss < best_loss - 0.001:  # 0.001 là ngưỡng cải thiện tối thiểu
                    best_loss = current_loss
                    no_improvement = 0
                    # Lưu mô hình tốt nhất
                    if output_dir:
                        nlp.to_disk(output_path / "best_model")
                else:
                    no_improvement += 1
                    if no_improvement >= patience:
                        print(f"Early stopping tại epoch {i}")
                        break
            else:
                # In loss nếu không có validation
                print(f"Epoch {i}, Loss: {losses['ner']:.4f}")
    
    # Lưu mô hình cuối cùng
    if output_dir:
        nlp.to_disk(output_path / "final_model")
        print(f"Đã lưu mô hình tại {output_path / 'final_model'}")
    
    return nlp

def evaluate_model(nlp, test_data):
    """
    Đánh giá mô hình NER với precision, recall và F1-score.
    """
    tp = 0  # True positive
    fp = 0  # False positive
    fn = 0  # False negative
    
    for text, annotations in test_data:
        # Dự đoán entities
        doc = nlp(text)
        gold_entities = annotations.get("entities", [])
        
        # Chuyển đổi gold entities thành tập hợp (start, end, label)
        gold_ents = {(start, end, label) for start, end, label in gold_entities}
        
        # Chuyển đổi predicted entities thành tập hợp
        pred_ents = {(ent.start_char, ent.end_char, ent.label_) for ent in doc.ents}
        
        # Tính true positives, false positives và false negatives
        tp += len(gold_ents.intersection(pred_ents))
        fp += len(pred_ents - gold_ents)
        fn += len(gold_ents - pred_ents)
    
    # Tính precision, recall và F1 score
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return {"precision": precision, "recall": recall, "f1": f1}

def evaluate_by_entity_type(nlp, test_data):
    """
    Đánh giá mô hình NER riêng cho từng loại thực thể.
    """
    metrics_by_type = {}
    
    for text, annotations in test_data:
        doc = nlp(text)
        gold_entities = annotations.get("entities", [])
        
        # Phân loại gold entities theo nhãn
        gold_by_type = {}
        for start, end, label in gold_entities:
            if label not in gold_by_type:
                gold_by_type[label] = []
            gold_by_type[label].append((start, end))
        
        # Phân loại predicted entities theo nhãn
        pred_by_type = {}
        for ent in doc.ents:
            if ent.label_ not in pred_by_type:
                pred_by_type[ent.label_] = []
            pred_by_type[ent.label_].append((ent.start_char, ent.end_char))
        
        # Tính TP, FP, FN cho từng nhãn
        all_labels = set(list(gold_by_type.keys()) + list(pred_by_type.keys()))
        for label in all_labels:
            if label not in metrics_by_type:
                metrics_by_type[label] = {"tp": 0, "fp": 0, "fn": 0}
            
            gold_ents_for_label = set(gold_by_type.get(label, []))
            pred_ents_for_label = set(pred_by_type.get(label, []))
            
            # Tính TP, FP, FN
            metrics_by_type[label]["tp"] += len(gold_ents_for_label.intersection(pred_ents_for_label))
            metrics_by_type[label]["fp"] += len(pred_ents_for_label - gold_ents_for_label)
            metrics_by_type[label]["fn"] += len(gold_ents_for_label - pred_ents_for_label)
    
    # Tính precision, recall, F1 cho từng nhãn
    results = {}
    for label, metrics in metrics_by_type.items():
        tp = metrics["tp"]
        fp = metrics["fp"]
        fn = metrics["fn"]
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        results[label] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": tp + fn  # Tổng số entities thực tế của nhãn này
        }
    
    return results

def test_specific_cases(nlp, test_cases):
    """
    Kiểm tra mô hình trên các trường hợp cụ thể.
    """
    results = []
    for name, text, expected_types in test_cases:
        doc = nlp(text)
        found_types = [ent.label_ for ent in doc.ents]
        entities = [(ent.text, ent.label_) for ent in doc.ents]
        
        passed = set(found_types) == set(expected_types)
        
        results.append({
            "name": name,
            "text": text,
            "expected": expected_types,
            "found": found_types,
            "entities": entities,
            "passed": passed
        })
        
        # In kết quả
        status = "PASSED" if passed else "FAILED"
        print(f"Test '{name}': {status}")
        print(f" - Câu: '{text}'")
        print(f" - Kỳ vọng: {expected_types}")
        print(f" - Tìm thấy: {found_types}")
        print(f" - Thực thể: {entities}")
        print()
    
    return results

def main():
    """
    Hàm chính để huấn luyện và đánh giá mô hình.
    """
    # Tham số huấn luyện
    n_iter = 100
    batch_size = 8
    dropout_rate = 0.05
    
    # Chia dữ liệu thành train và validation
    if not VALID_DATA:
        train_data, valid_data = train_test_split(TRAIN_DATA, test_size=0.2, random_state=42)
    else:
        train_data = TRAIN_DATA
        valid_data = VALID_DATA
    
    print(f"Số lượng mẫu huấn luyện: {len(train_data)}")
    print(f"Số lượng mẫu kiểm định: {len(valid_data)}")
    
    # Huấn luyện mô hình
    nlp = create_and_train_ner_model(
        train_data,
        valid_data=valid_data,
        output_dir="./improved_ner_vi",
        n_iter=n_iter,
        batch_size=batch_size,
        dropout_rate=dropout_rate
    )
    
    # Đánh giá tổng quát
    print("\n=== Kết quả đánh giá tổng quát ===")
    overall_results = evaluate_model(nlp, valid_data)
    print(f"Precision: {overall_results['precision']:.4f}")
    print(f"Recall: {overall_results['recall']:.4f}")
    print(f"F1-score: {overall_results['f1']:.4f}")
    
    # Đánh giá chi tiết theo loại thực thể
    print("\n=== Kết quả đánh giá theo loại thực thể ===")
    entity_results = evaluate_by_entity_type(nlp, valid_data)
    for entity_type, metrics in entity_results.items():
        print(f"Entity: {entity_type}")
        print(f"  Precision: {metrics['precision']:.4f}")
        print(f"  Recall: {metrics['recall']:.4f}")
        print(f"  F1-score: {metrics['f1']:.4f}")
        print(f"  Support: {metrics['support']}")
    
    # Kiểm tra các trường hợp đặc biệt
    print("\n=== Kiểm tra các trường hợp đặc biệt ===")
    test_cases = [
        ("notepad_test", "mở notepad", ["APP"]),
        ("youtube_test", "tìm bài hát Yesterday trên youtube", ["QUERY", "APP"]),
        ("path_test", "mở file trong thư mục Tài liệu", ["FILE", "PATH"]),
        ("excel_path_test", "tìm file excel trong thư mục Downloads", ["APP", "PATH"]),
        ("file_app_test", "mở file report.xlsx bằng excel", ["FILE", "APP"]),
        ("complex_test", "Hãy mở file Báo cáo Tài chính 2023.xlsx trong thư mục D:/Kế Toán bằng Excel", ["FILE", "PATH", "APP"]),
        ("file_search_test", "tìm file Báo cáo.docx trong ổ D", ["FILE", "PATH"]),
        ("video_test", "xem video Yesterday trên youtube", ["QUERY", "APP"])
    ]
    test_results = test_specific_cases(nlp, test_cases)
    
    # Lưu kết quả kiểm tra
    with open("ner_test_results.json", "w", encoding="utf-8") as f:
        json.dump(test_results, f, ensure_ascii=False, indent=2)
    
    print(f"Đã lưu kết quả kiểm tra vào file 'ner_test_results.json'")

if __name__ == "__main__":
    main()