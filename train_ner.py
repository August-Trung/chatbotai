import spacy
from spacy.training import Example
from spacy.util import minibatch, compounding
from pathlib import Path
import random
import json
from sklearn.model_selection import train_test_split
from tqdm import tqdm
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from train_ner_data import TRAIN_DATA, VALID_DATA
from generated_train_data import TRAIN_DATA

def convert_numpy_types(obj):
    """
    Chuyển đổi các kiểu dữ liệu numpy thành kiểu Python chuẩn để có thể serialize JSON.
    """
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    else:
        return obj

def create_and_train_ner_model(train_data, valid_data=None, output_dir="./improved_ner_vi", 
                              n_iter=100, batch_size=8, dropout_rate=0.3):
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
        
        # Lưu trữ lịch sử huấn luyện
        training_history = {
            'epochs': [],
            'losses': [],
            'precisions': [],
            'recalls': [],
            'f1_scores': []
        }
        
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
                
                # Lưu vào lịch sử (chuyển đổi numpy types thành Python types)
                training_history['epochs'].append(int(i))
                training_history['losses'].append(float(losses.get('ner', 0)))
                training_history['precisions'].append(float(eval_results['precision']))
                training_history['recalls'].append(float(eval_results['recall']))
                training_history['f1_scores'].append(float(eval_results['f1']))
                
                print(f"Epoch {i}, Loss: {losses.get('ner', 0):.4f}, Precision: {eval_results['precision']:.4f}, "
                      f"Recall: {eval_results['recall']:.4f}, F1: {eval_results['f1']:.4f}")
                
                # Kiểm tra early stopping
                current_loss = losses.get("ner", float('inf'))
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
                training_history['epochs'].append(int(i))
                training_history['losses'].append(float(losses.get('ner', 0)))
                if i % 10 == 0:  # Chỉ in mỗi 10 epochs để tránh spam
                    print(f"Epoch {i}, Loss: {losses.get('ner', 0):.4f}")
    
    # Lưu mô hình cuối cùng
    if output_dir:
        nlp.to_disk(output_path / "final_model")
        print(f"Đã lưu mô hình tại {output_path / 'final_model'}")
        
        # Chuyển đổi training_history để đảm bảo tất cả đều là Python types
        training_history_clean = convert_numpy_types(training_history)
        
        # Lưu lịch sử huấn luyện
        with open(output_path / "training_history.json", "w", encoding="utf-8") as f:
            json.dump(training_history_clean, f, ensure_ascii=False, indent=2)
    
    return nlp, training_history

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

def plot_ner_results(nlp, valid_data, test_results, training_history=None, save_dir="./plots"):
    """
    Vẽ các biểu đồ đánh giá mô hình NER.
    """
    # Tạo thư mục nếu chưa tồn tại
    os.makedirs(save_dir, exist_ok=True)
    
    # Evaluate NER metrics
    entity_results = evaluate_by_entity_type(nlp, valid_data)
    
    # Lấy danh sách các entity types có trong kết quả
    available_entities = list(entity_results.keys())
    
    if available_entities:
        precision = [entity_results[label]["precision"] for label in available_entities]
        recall = [entity_results[label]["recall"] for label in available_entities]
        f1 = [entity_results[label]["f1"] for label in available_entities]
        
        # Plot NER Evaluation Metrics
        plt.figure(figsize=(12, 6))
        bar_width = 0.25
        index = np.arange(len(available_entities))
        
        bars1 = plt.bar(index - bar_width, precision, bar_width, label="Precision", color="#ff7f0e", alpha=0.8)
        bars2 = plt.bar(index, recall, bar_width, label="Recall", color="#2ca02c", alpha=0.8)
        bars3 = plt.bar(index + bar_width, f1, bar_width, label="F1-Score", color="#1f77b4", alpha=0.8)
        
        plt.xlabel("Entity Types")
        plt.ylabel("Score")
        plt.title("NER Evaluation Metrics by Entity Type")
        plt.xticks(index, available_entities, rotation=45, ha='right')
        plt.legend()
        plt.ylim(0, 1.1)
        
        # Thêm giá trị trên các cột
        for i, (p, r, f) in enumerate(zip(precision, recall, f1)):
            plt.text(i - bar_width, p + 0.02, f"{p:.2f}", ha="center", va="bottom", fontsize=9)
            plt.text(i, r + 0.02, f"{r:.2f}", ha="center", va="bottom", fontsize=9)
            plt.text(i + bar_width, f + 0.02, f"{f:.2f}", ha="center", va="bottom", fontsize=9)
        
        plt.tight_layout()
        plt.savefig(f"{save_dir}/ner_metrics_by_entity.png", dpi=300, bbox_inches='tight')
        plt.show()
        plt.close()
    
    # Plot NER Test Case Result Distribution
    if test_results:
        passed = sum(1 for result in test_results if result["passed"])
        failed = len(test_results) - passed
        total = len(test_results)
        
        plt.figure(figsize=(8, 6))
        labels = ["Passed", "Failed"]
        sizes = [passed, failed]
        colors = ["#2ecc71", "#e74c3c"]
        explode = (0.05, 0)  # Tách phần "Passed" ra một chút
        
        wedges, texts, autotexts = plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', 
                                          startangle=90, explode=explode, shadow=True)
        
        # Thêm số lượng vào label
        for i, (wedge, text) in enumerate(zip(wedges, texts)):
            text.set_text(f"{labels[i]}\n({sizes[i]})")
        
        plt.title(f"NER Test Case Results\n(Total: {total} test cases)", fontsize=14, fontweight='bold')
        plt.savefig(f"{save_dir}/ner_test_distribution.png", dpi=300, bbox_inches='tight')
        plt.show()
        plt.close()
        
        # Plot Distribution of Entity Labels in Test Results
        entity_counts = {}
        for result in test_results:
            for _, label in result["entities"]:
                entity_counts[label] = entity_counts.get(label, 0) + 1
        
        if entity_counts:
            plt.figure(figsize=(10, 6))
            entities = list(entity_counts.keys())
            counts = list(entity_counts.values())
            
            colors = plt.cm.Set3(np.linspace(0, 1, len(entities)))
            bars = plt.bar(entities, counts, color=colors, alpha=0.8)
            
            plt.title("Distribution of Entity Labels in Test Cases", fontsize=14, fontweight='bold')
            plt.xlabel("Entity Types")
            plt.ylabel("Count")
            
            # Thêm giá trị trên các cột
            for bar, count in zip(bars, counts):
                plt.text(bar.get_x() + bar.get_width()/2, count + 0.1, 
                        str(count), ha="center", va="bottom", fontweight='bold')
            
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            plt.savefig(f"{save_dir}/entity_distribution.png", dpi=300, bbox_inches='tight')
            plt.show()
            plt.close()
    
    # Plot Training History if available
    if training_history and training_history['epochs']:
        plt.figure(figsize=(15, 5))
        
        # Loss plot
        plt.subplot(1, 3, 1)
        plt.plot(training_history['epochs'], training_history['losses'], 'b-', linewidth=2, marker='o')
        plt.title('Training Loss')
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        plt.grid(True, alpha=0.3)
        
        # Precision, Recall, F1 plot
        if training_history['precisions']:
            plt.subplot(1, 3, 2)
            epochs_subset = training_history['epochs'][:len(training_history['precisions'])]
            plt.plot(epochs_subset, training_history['precisions'], 'r-', linewidth=2, marker='s', label='Precision')
            plt.plot(epochs_subset, training_history['recalls'], 'g-', linewidth=2, marker='^', label='Recall')
            plt.plot(epochs_subset, training_history['f1_scores'], 'b-', linewidth=2, marker='o', label='F1-Score')
            plt.title('Validation Metrics')
            plt.xlabel('Epoch')
            plt.ylabel('Score')
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.ylim(0, 1)
        
        # Entity-wise F1 scores
        if available_entities:
            plt.subplot(1, 3, 3)
            f1_scores = [entity_results[label]["f1"] for label in available_entities]
            bars = plt.bar(range(len(available_entities)), f1_scores, 
                          color=plt.cm.viridis(np.linspace(0, 1, len(available_entities))))
            plt.title('Final F1-Score by Entity')
            plt.xlabel('Entity Type')
            plt.ylabel('F1-Score')
            plt.xticks(range(len(available_entities)), available_entities, rotation=45, ha='right')
            plt.ylim(0, 1)
            
            # Thêm giá trị
            for bar, score in zip(bars, f1_scores):
                plt.text(bar.get_x() + bar.get_width()/2, score + 0.02, 
                        f"{score:.3f}", ha="center", va="bottom", fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(f"{save_dir}/training_history.png", dpi=300, bbox_inches='tight')
        plt.show()
        plt.close()
    
    print(f"Đã lưu tất cả biểu đồ vào thư mục: {save_dir}")

def main():
    """
    Hàm chính để huấn luyện và đánh giá mô hình.
    """
    # Tham số huấn luyện
    n_iter = 100
    batch_size = 8
    dropout_rate = 0.3
    
    # Chia dữ liệu thành train và validation
    if not VALID_DATA:
        train_data, valid_data = train_test_split(TRAIN_DATA, test_size=0.2, random_state=42)
    else:
        train_data = TRAIN_DATA
        valid_data = VALID_DATA
    
    print(f"Số lượng mẫu huấn luyện: {len(train_data)}")
    print(f"Số lượng mẫu kiểm định: {len(valid_data)}")
    
    # Huấn luyện mô hình
    nlp, training_history = create_and_train_ner_model(
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
    
    # Tạo và hiển thị biểu đồ
    print("\n=== Tạo biểu đồ đánh giá ===")
    plot_ner_results(nlp, valid_data, test_results, training_history)
    
    # Lưu kết quả kiểm tra với convert_numpy_types
    test_results_clean = convert_numpy_types(test_results)
    with open("ner_test_results.json", "w", encoding="utf-8") as f:
        json.dump(test_results_clean, f, ensure_ascii=False, indent=2)
    
    print(f"Đã lưu kết quả kiểm tra vào file 'ner_test_results.json'")

if __name__ == "__main__":
    main()
