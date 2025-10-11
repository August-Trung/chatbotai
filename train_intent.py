from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix
import torch
import evaluate
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import json
# from train_intent_data import TRAIN_DATA
from generated_intent_data import TRAIN_DATA

# Chuẩn bị dữ liệu
texts = [item[0] for item in TRAIN_DATA]
labels = [item[1] for item in TRAIN_DATA]

# Tạo ánh xạ nhãn
label_map = {label: idx for idx, label in enumerate(sorted(set(labels)))}
label_ids = [label_map[label] for label in labels]

# Tạo ánh xạ ngược (id2label) cho mô hình
id2label = {idx: label for label, idx in label_map.items()}

# Tải tokenizer và mô hình
tokenizer = AutoTokenizer.from_pretrained("vinai/phobert-base")
model = AutoModelForSequenceClassification.from_pretrained(
    "vinai/phobert-base",
    num_labels=len(label_map),
    id2label=id2label,
    label2id=label_map
)

# Tokenize dữ liệu
encodings = tokenizer(texts, truncation=True, padding=True, max_length=128)

# Tạo dataset
class IntentDataset(torch.utils.data.Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item["labels"] = torch.tensor(self.labels[idx])
        return item

    def __len__(self):
        return len(self.labels)

dataset = IntentDataset(encodings, label_ids)
train_dataset, eval_dataset = train_test_split(dataset, test_size=0.2, random_state=42)

# Hàm tính toán metric (cập nhật để tính thêm F1-score)
def compute_metrics(eval_pred):
    accuracy_metric = evaluate.load("accuracy")
    f1_metric = evaluate.load("f1")
    
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    
    accuracy = accuracy_metric.compute(predictions=predictions, references=labels)
    f1 = f1_metric.compute(predictions=predictions, references=labels, average='weighted')
    
    return {
        "accuracy": accuracy["accuracy"],
        "f1": f1["f1"]
    }

# Thiết lập tham số huấn luyện
training_args = TrainingArguments(
    output_dir="./phobert_intent",
    num_train_epochs=10,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    warmup_steps=100,
    weight_decay=0.005,
    learning_rate=3e-5,
    logging_dir="./logs",
    logging_steps=10,
    eval_strategy="epoch",
    save_strategy="epoch",
    load_best_model_at_end=True,
    metric_for_best_model="accuracy",
    greater_is_better=True,
    save_total_limit=1
)

# Huấn luyện
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    compute_metrics=compute_metrics
)

# Huấn luyện mô hình
trainer.train()

# Đánh giá mô hình cuối cùng
eval_results = trainer.evaluate()
print("Evaluation results:", eval_results)

# Function for Intent Classification plotting
def plot_intent_results(trainer, intent_labels, save_dir="./plots"):
    # Tạo thư mục nếu chưa tồn tại
    os.makedirs(save_dir, exist_ok=True)
    
    # Evaluate and get predictions
    predictions = trainer.predict(trainer.eval_dataset)
    y_true = predictions.label_ids
    y_pred = np.argmax(predictions.predictions, axis=1)

    # Plot Confusion Matrix
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", 
                xticklabels=intent_labels, yticklabels=intent_labels, 
                cbar_kws={'label': 'Count'})
    plt.title("Confusion Matrix for Intent Classification")
    plt.xlabel("Predicted")
    plt.ylabel("True")
    plt.tight_layout()
    plt.savefig(f"{save_dir}/intent_confusion_matrix.png", dpi=300, bbox_inches='tight')
    plt.show()  # Hiển thị biểu đồ
    plt.close()

    # Tính F1-score thực tế cho từng class
    from sklearn.metrics import classification_report
    report = classification_report(y_true, y_pred, target_names=intent_labels, output_dict=True)
    
    # Lấy F1-score cho từng intent
    f1_scores = [report[label]['f1-score'] for label in intent_labels]
    
    # Plot F1-Score
    plt.figure(figsize=(10, 6))
    colors = plt.cm.Set3(np.linspace(0, 1, len(intent_labels)))
    bars = plt.bar(intent_labels, f1_scores, color=colors)
    plt.title("F1-Score by Intent")
    plt.ylabel("F1-Score")
    plt.ylim(0, 1)
    
    # Thêm giá trị trên các cột
    for bar, score in zip(bars, f1_scores):
        plt.text(bar.get_x() + bar.get_width()/2, score + 0.02, 
                f"{score:.3f}", ha="center", va="bottom")
    
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(f"{save_dir}/f1_score_by_intent.png", dpi=300, bbox_inches='tight')
    plt.show()  # Hiển thị biểu đồ
    plt.close()
    
    # Plot Training History (nếu có log)
    log_history = trainer.state.log_history
    train_losses = [log['train_loss'] for log in log_history if 'train_loss' in log]
    eval_losses = [log['eval_loss'] for log in log_history if 'eval_loss' in log]
    eval_accuracies = [log['eval_accuracy'] for log in log_history if 'eval_accuracy' in log]
    
    if train_losses and eval_losses:
        plt.figure(figsize=(12, 4))
        
        # Loss plot
        plt.subplot(1, 2, 1)
        plt.plot(range(1, len(train_losses) + 1), train_losses, 'b-', label='Training Loss')
        plt.plot(range(1, len(eval_losses) + 1), eval_losses, 'r-', label='Validation Loss')
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        plt.title('Training and Validation Loss')
        plt.legend()
        plt.grid(True)
        
        # Accuracy plot
        plt.subplot(1, 2, 2)
        plt.plot(range(1, len(eval_accuracies) + 1), eval_accuracies, 'g-', label='Validation Accuracy')
        plt.xlabel('Epoch')
        plt.ylabel('Accuracy')
        plt.title('Validation Accuracy')
        plt.legend()
        plt.grid(True)
        
        plt.tight_layout()
        plt.savefig(f"{save_dir}/training_history.png", dpi=300, bbox_inches='tight')
        plt.show()  # Hiển thị biểu đồ
        plt.close()
    
    print(f"Plots saved to {save_dir}")
    return report

# Lưu mô hình
model.save_pretrained("phobert_intent_model")
tokenizer.save_pretrained("phobert_intent_model")
print("Model saved to phobert_intent_model")

# Lưu ánh xạ nhãn
with open("phobert_intent_model/label_map.json", "w", encoding='utf-8') as f:
    json.dump({"label2id": label_map, "id2label": id2label}, f, ensure_ascii=False, indent=2)
print("Label mapping saved to phobert_intent_model/label_map.json")

# Tạo biểu đồ (GỌI HÀM ĐỂ HIỂN THỊ BIỂU ĐỒ)
intent_labels = list(label_map.keys())
classification_report = plot_intent_results(trainer, intent_labels)

# In báo cáo chi tiết
print("\n=== CLASSIFICATION REPORT ===")
from sklearn.metrics import classification_report as sklearn_report
predictions = trainer.predict(trainer.eval_dataset)
y_true = predictions.label_ids
y_pred = np.argmax(predictions.predictions, axis=1)
print(sklearn_report(y_true, y_pred, target_names=intent_labels))