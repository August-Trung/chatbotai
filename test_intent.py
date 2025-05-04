from transformers import pipeline

classifier = pipeline(
    "text-classification",
    model="phobert_intent_model",
    tokenizer="phobert_intent_model"
)

test_commands = [
    "mở notepad",
    "tìm file Báo cáo.docx trong ổ D",
    "vào google",
    "đóng chrome",
    "hiển thị thêm",
    "khởi động notepad",
    "tìm tài liệu Báo cáo.docx trên ổ D",
    "truy cập google",
    "tắt chrome",
    "xem thêm kết quả",
    "mở ứng dụng word",
    "đóng trình duyệt firefox",
    "hiển thị các mục tiếp theo"
]

for cmd in test_commands:
    result = classifier(cmd)
    print(f"Command: {cmd} -> Intent: {result[0]['label']} (Confidence: {result[0]['score']:.4f})")