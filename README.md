# Pipeline Gen Data → Train → Test

Hướng dẫn nhanh để sinh dataset bằng `z_Gen_Data/new_gen_data_3M_ProMax.py`, train mô hình Intent/NER (GPU hoặc CPU) và chạy bộ test kiểm thử.

## 0. Chuẩn bị môi trường
- Python 3.10+ khuyến nghị, chạy ở thư mục gốc repo.
- Tạo virtualenv (khuyến khích) và cài thư viện: `pip install -r requirements.txt`.
- Nếu muốn CPU-only cho PyTorch, cài bản torch phù hợp CPU; nếu đã có GPU CUDA thì giữ nguyên.

## 1. Sinh dataset từ new_gen_data_3M_ProMax.py
1) Chạy lệnh từ gốc dự án:  
   ```bash
   python z_Gen_Data/new_gen_data_3M_ProMax.py
   ```
2) Script sẽ tạo/ghi vào thư mục `dataset/`:
   - `dataset/nlu.jsonl` (mẫu Intent + entity span dùng cho cả Intent & NER),
   - `dataset/domain.yml`,
   - `dataset/multi_turn.json` (mẫu hội thoại nhiều lượt).
3) Nếu cần chỉnh kích thước dữ liệu, mở file và sửa `N_PER_TEMPLATE` hoặc `N_SESSIONS` ở cuối file rồi chạy lại. Luôn đảm bảo sau khi gen xong, các file trên thực sự tồn tại trong `dataset/` trước khi train.

## 2. Train mô hình
Tất cả script nằm trong `z_Train_Data/`. Dữ liệu đọc từ `dataset/nlu.jsonl` hoặc các file split nếu bạn tự tạo (`dataset/nlu_train.jsonl`, `dataset/nlu_validation.jsonl`).

### 2.1. Train trên GPU (PhoBERT)
- Intent:  
  ```bash
  python z_Train_Data/train_intent_phobert_gpu.py
  ```
- NER:  
  ```bash
  python z_Train_Data/train_ner_phobert_gpu.py
  ```
Kết quả: thư mục `phobert_intent_model/` và `phobert_ner_model/` (model, tokenizer, các file báo cáo/plot). Có thể tinh chỉnh nhanh qua biến môi trường: `BATCH_SIZE`, `EPOCHS`, `LR`, `INTENT_BASE_MODEL`, `NER_BASE_MODEL`.

### 2.2. Train trên CPU (fallback)
- Intent (PhoBERT dùng CPU nếu không có GPU):  
  ```bash
  python z_Train_Data/train_intent.py
  ```
- NER (spaCy):  
  ```bash
  python z_Train_Data/train_ner.py
  ```
Kết quả NER spaCy lưu tại `improved_ner_vi/final_model/`. (Tùy chọn: cài thêm model `vi_core_news_sm`/`vi_core_news_lg` để có tokenizer tiếng Việt tốt hơn, nhưng script sẽ tự fallback sang `spacy.blank("vi")` nếu thiếu.)

## 3. Kiểm thử mô hình
Sau khi train xong, chạy các test trong `z_Train_Data/`:
- Intent (đọc model từ `phobert_intent_model/`):  
  ```bash
  python z_Train_Data/test_intent.py
  ```
- NER (mặc định đọc `phobert_ner_model/`; nếu bạn train spaCy CPU, chỉnh đường dẫn `model_path` trong file để trỏ tới `improved_ner_vi/final_model/`):  
  ```bash
  python z_Train_Data/test_ner.py
  ```
Bạn có thể mở hai file test và thêm câu lệnh vào các list `test_commands`/`test_examples`/`specific_tests` để phủ nhiều kịch bản hơn và xem mô hình đang nhận diện sai ở đâu.

## 4. Ghi chú nhanh
- Kiểm tra kích thước dataset trước khi train (ví dụ `wc -l dataset/nlu.jsonl` trên Linux/macOS hoặc `Measure-Object -Line dataset/nlu.jsonl` trên PowerShell).
- Muốn giữ split cố định, tự tạo `dataset/nlu_train.jsonl` và `dataset/nlu_validation.jsonl`; các loader `train_intent_data_fixed.py` và `train_ner_data_fixed.py` sẽ ưu tiên dùng chúng.
- Khi thay đổi kích thước/bản chất dataset, nên xóa các thư mục model cũ (`phobert_intent_model/`, `phobert_ner_model/`, `improved_ner_vi/`) để tránh lẫn kết quả train trước.
