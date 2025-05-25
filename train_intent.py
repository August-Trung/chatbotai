from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from sklearn.model_selection import train_test_split
import torch
import evaluate
import numpy as np
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

# Hàm tính toán metric
def compute_metrics(eval_pred):
    metric = evaluate.load("accuracy")
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    accuracy = metric.compute(predictions=predictions, references=labels)
    return {
        "accuracy": accuracy["accuracy"],
    }

# Thiết lập tham số huấn luyện
# Cài đặt cho dataset lớn (~250 examples)
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

# Lưu mô hình
model.save_pretrained("phobert_intent_model")
tokenizer.save_pretrained("phobert_intent_model")
print("Model saved to phobert_intent_model")

# Lưu ánh xạ nhãn
import json
with open("phobert_intent_model/label_map.json", "w") as f:
    json.dump({"label2id": label_map, "id2label": id2label}, f, ensure_ascii=False)
print("Label mapping saved to phobert_intent_model/label_map.json")