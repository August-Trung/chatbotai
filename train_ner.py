import spacy
from spacy.training import Example
from spacy.util import minibatch, compounding
from train_ner_data import TRAIN_DATA, VALID_DATA  # Sử dụng TRAIN_DATA tinh chỉnh (30 ví dụ)
import random

def train_ner_model():
    # Tạo mô hình trống
    nlp = spacy.blank("vi")
    if "ner" not in nlp.pipe_names:
        ner = nlp.add_pipe("ner")
    else:
        ner = nlp.get_pipe("ner")

    # Thêm nhãn thực thể
    for label in ["APP", "FILE", "PATH", "QUERY"]:
        ner.add_label(label)

    # Tạo danh sách Examples để khởi tạo
    examples = []
    for text, annotations in TRAIN_DATA:
        doc = nlp.make_doc(text)
        example = Example.from_dict(doc, annotations)
        examples.append(example)

    # Khởi tạo mô hình
    nlp.initialize(lambda: examples)

    # Tạo optimizer với learning rate phù hợp
    optimizer = nlp.create_optimizer()
    optimizer.learn_rate = 0.0001  # Giảm learning rate thêm nữa để học chi tiết hơn

    # Đánh giá mô hình
    def evaluate_model(nlp, valid_data):
        examples = []
        for text, annot in valid_data:
            doc = nlp.make_doc(text)
            example = Example.from_dict(doc, annot)
            examples.append(example)
        return nlp.evaluate(examples)

    # Hàm tạo mini-batches cho quá trình huấn luyện
    def create_mini_batches(train_data, batch_size):
        random.shuffle(train_data)
        batches = []
        for i in range(0, len(train_data), batch_size):
            batches.append(train_data[i:i + batch_size])
        return batches

    # Huấn luyện với mini-batches và dropout
    n_iter = 150  # Tăng số lần lặp thêm nữa
    batch_size = 4
    dropout_rate = 0.25  # Giảm dropout để học tốt hơn các trường hợp đặc biệt

    for itn in range(n_iter):
        batches = create_mini_batches(TRAIN_DATA, batch_size)
        losses = {}
        
        for batch in batches:
            examples = []
            for text, annotations in batch:
                doc = nlp.make_doc(text)
                example = Example.from_dict(doc, annotations)
                examples.append(example)
            
            nlp.update(examples, drop=dropout_rate, sgd=optimizer, losses=losses)
        
        print(f"Iteration {itn}, Losses: {losses}")
        
        # Đánh giá định kỳ
        if itn % 10 == 0:
            scores = evaluate_model(nlp, VALID_DATA)
            print(f"Validation scores: Overall F1 = {scores['ents_f']}")
            for label in ['APP', 'FILE', 'PATH', 'QUERY']:
                if label in scores['ents_per_type']:
                    print(f"  {label}: F1 = {scores['ents_per_type'][label]['f']}, "
                        f"P = {scores['ents_per_type'][label]['p']}, "
                        f"R = {scores['ents_per_type'][label]['r']}")

    # Lưu mô hình
    nlp.to_disk("improved_ner_vi")
    print("Model saved to improved_ner_vi")

    # Kiểm tra một số ví dụ
    test_examples = [
        "mở notepad",
        "tìm file Báo cáo.docx trong ổ D",
        "tìm bài hát Yesterday trên youtube",
        "mở file rename.xlsx trong thư mục Tài liệu bằng excel",
        # Thêm các ví dụ kiểm tra chi tiết
        "mở file trong thư mục Tài liệu",
        "tìm tài liệu trong ổ D",
        "xem video Yesterday trên youtube",
    ]

    print("\n=== Kiểm tra mô hình với các ví dụ ===")
    for text in test_examples:
        doc = nlp(text)
        print(f"\nCommand: {text}")
        if len(doc.ents) == 0:
            print(" - Không nhận diện được thực thể nào")
        else:
            for ent in doc.ents:
                print(f" - {ent.text}: {ent.label_}")

if __name__ == "__main__":
    train_ner_model()