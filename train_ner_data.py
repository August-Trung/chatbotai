# Dữ liệu huấn luyện nâng cao cho mô hình NER tiếng Việt với cải thiện nhận dạng PATH

TRAIN_DATA = [
    # BLOCK 1: PATH trọn vẹn - lặp lại nhiều lần để nhấn mạnh tính liên tục của PATH
    # Lưu ý: PATH phải là một thực thể liên tục, không bị chia nhỏ
    ("mở file trong thư mục Tài liệu", {"entities": [(4, 8, "FILE"), (9, 29, "PATH")]}),
    ("mở file trong thư mục Tài liệu", {"entities": [(4, 8, "FILE"), (9, 29, "PATH")]}),
    ("mở file trong thư mục Tài liệu", {"entities": [(4, 8, "FILE"), (9, 29, "PATH")]}),
    ("mở file trong thư mục Tài liệu", {"entities": [(4, 8, "FILE"), (9, 29, "PATH")]}),
    ("mở file trong thư mục Tài liệu", {"entities": [(4, 8, "FILE"), (9, 29, "PATH")]}),
    ("tìm file trong thư mục Downloads", {"entities": [(4, 8, "FILE"), (9, 30, "PATH")]}),
    ("tìm file trong thư mục Downloads", {"entities": [(4, 8, "FILE"), (9, 30, "PATH")]}),
    ("tìm file trong thư mục Downloads", {"entities": [(4, 8, "FILE"), (9, 30, "PATH")]}),
    ("tìm file trong thư mục Downloads", {"entities": [(4, 8, "FILE"), (9, 30, "PATH")]}),
    ("tìm file trong thư mục Downloads", {"entities": [(4, 8, "FILE"), (9, 30, "PATH")]}),
    
    # BLOCK 2: PATH với ổ đĩa - lặp lại nhiều lần để mô hình học được toàn bộ đơn vị "trong ổ X"
    ("tìm file trong ổ D", {"entities": [(4, 8, "FILE"), (9, 20, "PATH")]}),
    ("tìm file trong ổ D", {"entities": [(4, 8, "FILE"), (9, 20, "PATH")]}),
    ("tìm file trong ổ D", {"entities": [(4, 8, "FILE"), (9, 20, "PATH")]}),
    ("tìm file trong ổ D", {"entities": [(4, 8, "FILE"), (9, 20, "PATH")]}),
    ("tìm file trong ổ D", {"entities": [(4, 8, "FILE"), (9, 20, "PATH")]}),
    ("tìm tài liệu trong ổ D", {"entities": [(4, 13, "FILE"), (14, 25, "PATH")]}),
    ("tìm tài liệu trong ổ D", {"entities": [(4, 13, "FILE"), (14, 25, "PATH")]}),
    ("tìm tài liệu trong ổ D", {"entities": [(4, 13, "FILE"), (14, 25, "PATH")]}),
    ("tìm file trong ổ C", {"entities": [(4, 8, "FILE"), (9, 20, "PATH")]}),
    ("tìm file trong ổ C", {"entities": [(4, 8, "FILE"), (9, 20, "PATH")]}),
    ("tìm file trong ổ C", {"entities": [(4, 8, "FILE"), (9, 20, "PATH")]}),
    
    # BLOCK 3: Xử lý PATH một cách toàn vẹn - tập trung vào tính liên tục
    ("tìm file trong thư mục", {"entities": [(4, 8, "FILE"), (9, 24, "PATH")]}),
    ("tìm file trong thư mục", {"entities": [(4, 8, "FILE"), (9, 24, "PATH")]}),
    ("tìm file trong thư mục", {"entities": [(4, 8, "FILE"), (9, 24, "PATH")]}),
    ("tìm file trong thư mục", {"entities": [(4, 8, "FILE"), (9, 24, "PATH")]}),
    ("tìm file trong thư mục", {"entities": [(4, 8, "FILE"), (9, 24, "PATH")]}),
    ("tìm tài liệu trong thư mục", {"entities": [(4, 13, "FILE"), (14, 29, "PATH")]}),
    ("tìm tài liệu trong thư mục", {"entities": [(4, 13, "FILE"), (14, 29, "PATH")]}),
    ("tìm tài liệu trong thư mục", {"entities": [(4, 13, "FILE"), (14, 29, "PATH")]}),
    ("tìm tài liệu trong thư mục", {"entities": [(4, 13, "FILE"), (14, 29, "PATH")]}),
    ("tìm video trong thư mục", {"entities": [(4, 9, "FILE"), (10, 25, "PATH")]}),
    ("tìm video trong thư mục", {"entities": [(4, 9, "FILE"), (10, 25, "PATH")]}),
    ("tìm video trong thư mục", {"entities": [(4, 9, "FILE"), (10, 25, "PATH")]}),
    ("tìm video trong thư mục", {"entities": [(4, 9, "FILE"), (10, 25, "PATH")]}),
    
    # BLOCK 4: Xử lý PATH với tên cụ thể - lặp lại để tăng trọng số
    ("tìm file trong thư mục Documents", {"entities": [(4, 8, "FILE"), (9, 31, "PATH")]}),
    ("tìm file trong thư mục Documents", {"entities": [(4, 8, "FILE"), (9, 31, "PATH")]}),
    ("tìm file trong thư mục Pictures", {"entities": [(4, 8, "FILE"), (9, 30, "PATH")]}),
    ("tìm file trong thư mục Pictures", {"entities": [(4, 8, "FILE"), (9, 30, "PATH")]}),
    ("tìm file trong thư mục Videos", {"entities": [(4, 8, "FILE"), (9, 29, "PATH")]}),
    ("tìm file trong thư mục Videos", {"entities": [(4, 8, "FILE"), (9, 29, "PATH")]}),
    ("tìm file trong thư mục Music", {"entities": [(4, 8, "FILE"), (9, 28, "PATH")]}),
    ("tìm file trong thư mục Music", {"entities": [(4, 8, "FILE"), (9, 28, "PATH")]}),
    
    # BLOCK 5: Xử lý PATH phức tạp hơn
    ("tìm file trong thư mục Documents/Work", {"entities": [(4, 8, "FILE"), (9, 36, "PATH")]}),
    ("tìm file trong thư mục Documents/Work", {"entities": [(4, 8, "FILE"), (9, 36, "PATH")]}),
    ("tìm file trong thư mục Tài liệu/Công việc", {"entities": [(4, 8, "FILE"), (9, 42, "PATH")]}),
    ("tìm file trong thư mục Tài liệu/Công việc", {"entities": [(4, 8, "FILE"), (9, 42, "PATH")]}),
    ("tìm file trong D:/Documents", {"entities": [(4, 8, "FILE"), (9, 28, "PATH")]}),
    ("tìm file trong D:/Documents", {"entities": [(4, 8, "FILE"), (9, 28, "PATH")]}),
    
    # BLOCK 6: Xử lý PATH với file cụ thể
    ("tìm file Báo cáo.docx trong ổ D", {"entities": [(4, 22, "FILE"), (23, 34, "PATH")]}),
    ("tìm file Báo cáo.docx trong ổ D", {"entities": [(4, 22, "FILE"), (23, 34, "PATH")]}),
    ("tìm file Báo cáo.xlsx trong ổ D", {"entities": [(4, 22, "FILE"), (23, 34, "PATH")]}),
    ("tìm file Báo cáo.docx trong thư mục D", {"entities": [(4, 22, "FILE"), (23, 39, "PATH")]}),
    ("tìm file Báo cáo.docx trong thư mục D", {"entities": [(4, 22, "FILE"), (23, 39, "PATH")]}),
    ("tìm file Report.docx trong thư mục Documents", {"entities": [(4, 20, "FILE"), (21, 43, "PATH")]}),
    ("tìm file Report.docx trong thư mục Documents", {"entities": [(4, 20, "FILE"), (21, 43, "PATH")]}),
    
    # BLOCK 7: Thêm PATH với đa dạng loại file
    ("tìm file excel.xlsx trong thư mục Tài liệu", {"entities": [(4, 19, "FILE"), (20, 40, "PATH")]}),
    ("tìm file excel.xlsx trong thư mục Tài liệu", {"entities": [(4, 19, "FILE"), (20, 40, "PATH")]}),
    ("tìm file rename.xlsx trong thư mục Tài liệu", {"entities": [(4, 19, "FILE"), (20, 40, "PATH")]}),
    ("tìm file rename.xlsx trong thư mục Tài liệu", {"entities": [(4, 19, "FILE"), (20, 40, "PATH")]}),
    ("tìm file video.mp4 trong ổ E", {"entities": [(4, 19, "FILE"), (20, 31, "PATH")]}),
    ("tìm file video.mp4 trong ổ E", {"entities": [(4, 19, "FILE"), (20, 31, "PATH")]}),
    ("tìm file video.mp4 trong thư mục Videos", {"entities": [(4, 19, "FILE"), (20, 41, "PATH")]}),
    ("tìm file video.mp4 trong thư mục Videos", {"entities": [(4, 19, "FILE"), (20, 41, "PATH")]}),

    # BLOCK 8: Thêm PATH với cấu trúc APP cuối câu - nhấn mạnh cấu trúc FILE-PATH-APP đầy đủ
    ("mở file excel.xlsx trong thư mục Tài liệu bằng excel", {"entities": [(4, 19, "FILE"), (20, 40, "PATH"), (47, 52, "APP")]}),
    ("mở file excel.xlsx trong thư mục Tài liệu bằng excel", {"entities": [(4, 19, "FILE"), (20, 40, "PATH"), (47, 52, "APP")]}),
    ("mở file excel.xlsx trong thư mục Tài liệu bằng excel", {"entities": [(4, 19, "FILE"), (20, 40, "PATH"), (47, 52, "APP")]}),
    ("mở file excel.xlsx trong thư mục Tài liệu bằng excel", {"entities": [(4, 19, "FILE"), (20, 40, "PATH"), (47, 52, "APP")]}),
    ("mở file rename.xlsx trong thư mục Tài liệu bằng excel", {"entities": [(4, 19, "FILE"), (20, 40, "PATH"), (47, 52, "APP")]}),
    ("mở file rename.xlsx trong thư mục Tài liệu bằng excel", {"entities": [(4, 19, "FILE"), (20, 40, "PATH"), (47, 52, "APP")]}),
    ("mở file rename.xlsx trong thư mục Tài liệu bằng excel", {"entities": [(4, 19, "FILE"), (20, 40, "PATH"), (47, 52, "APP")]}),
    ("mở file rename.xlsx trong thư mục Tài liệu bằng excel", {"entities": [(4, 19, "FILE"), (20, 40, "PATH"), (47, 52, "APP")]}),
    ("mở file báo cáo.docx trong thư mục Công việc bằng word", {"entities": [(4, 23, "FILE"), (24, 49, "PATH"), (56, 60, "APP")]}),
    ("mở file báo cáo.docx trong thư mục Công việc bằng word", {"entities": [(4, 23, "FILE"), (24, 49, "PATH"), (56, 60, "APP")]}),
    ("mở file báo cáo.docx trong thư mục Công việc bằng word", {"entities": [(4, 23, "FILE"), (24, 49, "PATH"), (56, 60, "APP")]}),
    ("mở file báo cáo.docx trong thư mục Công việc bằng word", {"entities": [(4, 23, "FILE"), (24, 49, "PATH"), (56, 60, "APP")]}),
    
    # BLOCK 9: Các biểu thức "trong" không phải PATH - để giúp mô hình phân biệt
    ("tìm từ english trong văn bản", {"entities": [(4, 15, "QUERY")]}),
    ("tìm từ english trong văn bản", {"entities": [(4, 15, "QUERY")]}),
    ("tìm bài hát Yesterday trong playlist", {"entities": [(4, 21, "QUERY")]}),
    ("tìm bài hát Yesterday trong playlist", {"entities": [(4, 21, "QUERY")]}),
    
    # Dữ liệu gốc đã được tăng cường
    # APP - nhấn mạnh đặc biệt vào nhận dạng "ứng dụng" với APP
    ("mở notepad", {"entities": [(4, 11, "APP")]}),
    ("mở notepad", {"entities": [(4, 11, "APP")]}),
    ("mở notepad", {"entities": [(4, 11, "APP")]}),
    ("mở notepad", {"entities": [(4, 11, "APP")]}),
    ("mở notepad", {"entities": [(4, 11, "APP")]}),
    
    # Tập trung vào cấu trúc "mở ứng dụng X" - lặp lại nhiều lần
    ("mở ứng dụng notepad", {"entities": [(13, 20, "APP")]}),
    ("mở ứng dụng notepad", {"entities": [(13, 20, "APP")]}),
    ("mở ứng dụng notepad", {"entities": [(13, 20, "APP")]}),
    ("mở ứng dụng word", {"entities": [(13, 17, "APP")]}),
    ("mở ứng dụng word", {"entities": [(13, 17, "APP")]}),
    ("mở ứng dụng word", {"entities": [(13, 17, "APP")]}),
    ("mở ứng dụng word", {"entities": [(13, 17, "APP")]}),
    ("mở ứng dụng word", {"entities": [(13, 17, "APP")]}),
    ("mở ứng dụng excel", {"entities": [(13, 18, "APP")]}),
    ("mở ứng dụng excel", {"entities": [(13, 18, "APP")]}),
    ("mở ứng dụng excel", {"entities": [(13, 18, "APP")]}),
    ("mở ứng dụng excel", {"entities": [(13, 18, "APP")]}),
    ("mở ứng dụng excel", {"entities": [(13, 18, "APP")]}),
    
    # APP cơ bản
    ("chạy notepad", {"entities": [(5, 12, "APP")]}),
    ("khởi chạy notepad", {"entities": [(11, 18, "APP")]}),
    ("mở chrome", {"entities": [(4, 10, "APP")]}),
    ("vào google", {"entities": [(4, 10, "APP")]}),
    ("đóng chrome", {"entities": [(6, 12, "APP")]}),
    ("mở facebook bằng chrome", {"entities": [(4, 12, "APP"), (18, 24, "APP")]}),
    ("mở zalo", {"entities": [(4, 8, "APP")]}),
    ("mở excel", {"entities": [(4, 9, "APP")]}),
    ("mở word", {"entities": [(4, 8, "APP")]}),
    ("mở word", {"entities": [(4, 8, "APP")]}),
    ("mở word", {"entities": [(4, 8, "APP")]}),
    ("mở excel", {"entities": [(4, 9, "APP")]}),
    ("mở excel", {"entities": [(4, 9, "APP")]}),
    ("mở excel", {"entities": [(4, 9, "APP")]}),
    ("mở notepad++", {"entities": [(4, 13, "APP")]}),
    ("mở Office", {"entities": [(4, 10, "APP")]}),
    ("mở Microsoft Word", {"entities": [(4, 17, "APP")]}),
    ("mở MS Word", {"entities": [(4, 11, "APP")]}),
    ("mở ứng dụng Word", {"entities": [(13, 17, "APP")]}),
    ("mở ứng dụng Excel", {"entities": [(13, 18, "APP")]}),
    ("chạy ứng dụng Spotify", {"entities": [(14, 22, "APP")]}),
    ("mở youtube", {"entities": [(4, 11, "APP")]}),
    ("mở game Liên Minh Huyền Thoại", {"entities": [(4, 30, "APP")]}),
    ("chạy ứng dụng Zoom", {"entities": [(14, 18, "APP")]}),
    ("mở trình duyệt Edge", {"entities": [(4, 20, "APP")]}),
    ("mở phần mềm Paint", {"entities": [(4, 19, "APP")]}),
    ("mở ứng dụng Teams", {"entities": [(13, 18, "APP")]}),
    ("mở messenger", {"entities": [(4, 13, "APP")]}),
    ("mở OneNote", {"entities": [(4, 11, "APP")]}),
    ("mở Outlook", {"entities": [(4, 11, "APP")]}),

    # Các trình duyệt web
    ("mở chrome", {"entities": [(4, 10, "APP")]}),
    ("mở microsoft edge", {"entities": [(4, 18, "APP")]}),
    ("khởi động chrome", {"entities": [(11, 17, "APP")]}),
    ("chạy trình duyệt safari", {"entities": [(5, 24, "APP")]}),
    ("mở opera", {"entities": [(4, 9, "APP")]}),

    # Các ứng dụng truyền thông xã hội
    ("mở zalo", {"entities": [(4, 8, "APP")]}),
    ("mở facebook", {"entities": [(4, 12, "APP")]}),
    ("khởi chạy messenger", {"entities": [(11, 20, "APP")]}),
    ("mở ứng dụng telegram", {"entities": [(13, 21, "APP")]}),

    # Các ứng dụng phát triển và công cụ
    ("mở visual studio code", {"entities": [(4, 21, "APP")]}),
    ("mở pycharm", {"entities": [(4, 11, "APP")]}),
    ("khởi động android studio", {"entities": [(11, 25, "APP")]}),
    ("mở terminal", {"entities": [(4, 12, "APP")]}),
    ("chạy command prompt", {"entities": [(5, 18, "APP")]}),

    # Trường hợp đặc biệt
    ("mở microsoft word để soạn thảo", {"entities": [(4, 17, "APP"), (18, 32, "QUERY")]}),
    ("khởi động paint để chỉnh sửa ảnh", {"entities": [(11, 16, "APP"), (17, 35, "QUERY")]}),
    ("mở excel để xem báo cáo doanh thu tháng 5", {"entities": [(4, 9, "APP"), (10, 41, "QUERY")]}),
    ("mở file trong thư mục Desktop và chỉnh sửa bằng notepad", {"entities": [(4, 8, "FILE"), (9, 32, "PATH"), (46, 53, "APP")]}),
    
    # FILE - Phân biệt rõ các trường hợp file có tên phức tạp và tên đơn giản
    # File đơn giản - lặp lại để mô hình nhận dạng đúng phạm vi
    ("mở file excel", {"entities": [(4, 14, "FILE")]}),
    ("mở file excel", {"entities": [(4, 14, "FILE")]}),
    ("mở file excel", {"entities": [(4, 14, "FILE")]}),
    ("mở file word", {"entities": [(4, 13, "FILE")]}),
    ("mở file word", {"entities": [(4, 13, "FILE")]}),
    ("mở file word", {"entities": [(4, 13, "FILE")]}),
    ("tìm file excel", {"entities": [(4, 14, "FILE")]}),
    ("tìm file excel", {"entities": [(4, 14, "FILE")]}),
    ("tìm file excel", {"entities": [(4, 14, "FILE")]}),
    
    # File có phần mở rộng - lặp lại nhiều lần 
    ("mở file Sales.xlsx", {"entities": [(4, 19, "FILE")]}),
    ("mở file Sales.xlsx", {"entities": [(4, 19, "FILE")]}),
    ("mở file Sales.xlsx", {"entities": [(4, 19, "FILE")]}),
    ("mở file Sales.xlsx bằng excel", {"entities": [(4, 19, "FILE"), (26, 31, "APP")]}),
    ("mở file Sales.xlsx bằng excel", {"entities": [(4, 19, "FILE"), (26, 31, "APP")]}),
    ("mở file Báo_cáo_Q1_2023.xlsx", {"entities": [(4, 29, "FILE")]}),
    ("mở file Báo cáo Q1 2023.xlsx", {"entities": [(4, 29, "FILE")]}),
    
    # File với PATH đầy đủ
    ("tìm file Báo_cáo.docx trong ổ D", {"entities": [(4, 23, "FILE"), (24, 35, "PATH")]}),
    ("tìm file Báo_cáo.docx trong ổ D", {"entities": [(4, 23, "FILE"), (24, 35, "PATH")]}),
    ("tìm ảnh.jpg trong thư mục Pictures", {"entities": [(4, 12, "FILE"), (13, 34, "PATH")]}),
    ("tìm ảnh.png trong thư mục Pictures", {"entities": [(4, 12, "FILE"), (13, 34, "PATH")]}),
    ("tìm file Report.doc trong thư mục Documents/Work", {"entities": [(4, 19, "FILE"), (20, 47, "PATH")]}),
    ("tìm file Report.pdf trong thư mục Documents/Work", {"entities": [(4, 19, "FILE"), (20, 47, "PATH")]}),
    ("mở file tài liệu.pdf", {"entities": [(4, 22, "FILE")]}),
    ("tìm file báo cáo quý 1.docx trong thư mục Công việc", {"entities": [(4, 27, "FILE"), (28, 53, "PATH")]}),
    ("tìm file báo.cáo.quý.1.docx trong thư mục Công việc", {"entities": [(4, 29, "FILE"), (30, 55, "PATH")]}),
    ("mở file báo_cáo_quý_1.docx trong thư mục Công việc", {"entities": [(4, 29, "FILE"), (30, 55, "PATH")]}),
    
    # QUERY
    ("tìm bài hát Yesterday trên youtube", {"entities": [(4, 21, "QUERY"), (22, 35, "APP")]}),
    ("phát bài hát Yesterday Night", {"entities": [(5, 28, "QUERY")]}),
    ("tìm tài liệu Java nâng cao", {"entities": [(4, 25, "QUERY")]}),
    ("tìm phim Inception trên Netflix", {"entities": [(4, 18, "QUERY"), (19, 32, "APP")]}),
    ("xem ảnh kỷ niệm 2020", {"entities": [(4, 21, "QUERY")]}),
    ("tìm bài hát Yesterday", {"entities": [(4, 21, "QUERY")]}),
    ("tìm bài hát Yesterday trong spotify", {"entities": [(4, 21, "QUERY"), (22, 36, "APP")]}),
    ("tìm file excel với tên Báo cáo", {"entities": [(4, 9, "FILE"), (15, 27, "QUERY")]}),
    ("phát nhạc Lo-fi Chill", {"entities": [(5, 20, "QUERY")]}),
    ("tìm slide bài giảng AI", {"entities": [(4, 24, "QUERY")]}),
    ("tìm bài hát Shape of You", {"entities": [(4, 25, "QUERY")]}),
    ("xem video Hướng dẫn nấu ăn", {"entities": [(4, 26, "QUERY")]}),
    ("tìm ảnh mùa thu", {"entities": [(4, 14, "QUERY")]}),
    ("tìm tài liệu Python nâng cao trong ổ D", {"entities": [(4, 29, "QUERY"), (30, 41, "PATH")]}),
    ("tìm video trên youtube", {"entities": [(4, 9, "QUERY"), (15, 22, "APP")]}),
    ("tìm bài hát trên youtube", {"entities": [(4, 11, "QUERY"), (17, 24, "APP")]}),
    ("tìm Yesterday trên youtube", {"entities": [(4, 13, "QUERY"), (19, 26, "APP")]}),
    ("tìm video Yesterday trên youtube", {"entities": [(4, 20, "QUERY"), (26, 33, "APP")]}),
    ("tìm video Yesterday Night trên youtube", {"entities": [(4, 26, "QUERY"), (32, 39, "APP")]}),
    ("xem Yesterday trên youtube", {"entities": [(4, 13, "QUERY"), (19, 26, "APP")]}),
]

# Dữ liệu kiểm định
VALID_DATA = [
    # APP - nhấn mạnh đặc biệt vào nhận dạng "ứng dụng" với APP
    ("mở notepad", {"entities": [(4, 11, "APP")]}),
    ("mở word", {"entities": [(4, 8, "APP")]}),
    ("mở excel", {"entities": [(4, 9, "APP")]}),
    ("mở outlook", {"entities": [(4, 11, "APP")]}),
    ("khởi động word", {"entities": [(11, 15, "APP")]}),
    ("chạy excel", {"entities": [(5, 10, "APP")]}),
    ("khởi chạy notepad", {"entities": [(11, 18, "APP")]}),
    ("mở ứng dụng word", {"entities": [(13, 17, "APP")]}),

    # FILE và PATH cơ bản
    ("mở file báo cáo trong thư mục Dự án", {"entities": [(4, 12, "FILE"), (13, 34, "PATH")]}),
    ("tìm file dữ liệu trong thư mục Analytics", {"entities": [(4, 13, "FILE"), (14, 38, "PATH")]}),
    ("mở file danh sách khách hàng.xlsx trong thư mục Marketing", {"entities": [(4, 34, "FILE"), (35, 58, "PATH")]}),
    ("tìm file bảng tính.xlsx trong thư mục Tài chính", {"entities": [(4, 22, "FILE"), (23, 48, "PATH")]}),
    
    # FILE với phần mở rộng đa dạng
    ("mở file biên bản họp.pdf", {"entities": [(4, 25, "FILE")]}),
    ("tìm file báo cáo năm 2023.docx", {"entities": [(4, 31, "FILE")]}),
    ("mở file dữ liệu thống kê.csv", {"entities": [(4, 30, "FILE")]}),
    ("tìm file hình ảnh.jpg trong thư mục Media", {"entities": [(4, 20, "FILE"), (21, 40, "PATH")]}),
    
    # PATH phức tạp và đường dẫn ổ đĩa
    ("tìm file trong thư mục Dự án/Phase 1/Documents", {"entities": [(4, 8, "FILE"), (9, 50, "PATH")]}),
    ("mở file trong E:/Backup/2023", {"entities": [(4, 8, "FILE"), (9, 31, "PATH")]}),
    ("tìm file báo cáo trong thư mục F:/Công ty/Báo cáo", {"entities": [(4, 12, "FILE"), (13, 47, "PATH")]}),
    ("mở file trong ổ E", {"entities": [(4, 8, "FILE"), (9, 20, "PATH")]}),
    
    # APP với các ứng dụng khác nhau
    ("mở powerpoint", {"entities": [(4, 14, "APP")]}),
    ("khởi chạy photoshop", {"entities": [(11, 19, "APP")]}),
    ("mở ứng dụng skype", {"entities": [(13, 18, "APP")]}),
    ("chạy trình duyệt firefox", {"entities": [(5, 24, "APP")]}),
    ("mở adobe reader", {"entities": [(4, 16, "APP")]}),
    
    # FILE - PATH - APP kết hợp
    ("mở file thuyết trình.pptx trong thư mục Dự án bằng powerpoint", {"entities": [(4, 27, "FILE"), (28, 49, "PATH"), (56, 66, "APP")]}),
    ("tìm file ảnh logo.png trong thư mục Marketing bằng photoshop", {"entities": [(4, 19, "FILE"), (20, 45, "PATH"), (52, 61, "APP")]}),
    ("mở file video demo.mp4 trong ổ F bằng vlc", {"entities": [(4, 22, "FILE"), (23, 34, "PATH"), (41, 44, "APP")]}),
    ("tìm file PDF trong thư mục Tài liệu bằng acrobat", {"entities": [(4, 12, "FILE"), (13, 33, "PATH"), (40, 47, "APP")]}),
    
    # QUERY đa dạng
    ("tìm bài viết về trí tuệ nhân tạo", {"entities": [(4, 32, "QUERY")]}),
    ("phát nhạc Bolero nhẹ nhàng", {"entities": [(5, 25, "QUERY")]}),
    ("tìm hình ảnh bầu trời hoàng hôn", {"entities": [(4, 31, "QUERY")]}),
    ("xem video hướng dẫn sử dụng Excel trên youtube", {"entities": [(4, 36, "QUERY"), (42, 49, "APP")]}),
    
    # Trường hợp QUERY với APP hoặc PATH
    ("tìm thông tin về Python trong thư mục Học tập", {"entities": [(4, 24, "QUERY"), (25, 46, "PATH")]}),
    ("tìm bài hát Despacito trên spotify", {"entities": [(4, 22, "QUERY"), (28, 35, "APP")]}),
    ("phát podcast về kinh doanh trên google podcast", {"entities": [(5, 28, "QUERY"), (34, 48, "APP")]}),
    ("tìm tài liệu marketing digital trong thư mục Công việc", {"entities": [(4, 30, "QUERY"), (31, 56, "PATH")]}),
    
    # Trường hợp đặc biệt 
    ("mở file presentation_final_v2.pptx bằng powerpoint", {"entities": [(4, 34, "FILE"), (41, 51, "APP")]}),
    ("tìm báo cáo tài chính Q2.xlsx trong thư mục Kế toán/2023", {"entities": [(4, 28, "FILE"), (29, 56, "PATH")]}),
    ("mở phần mềm visual studio code", {"entities": [(4, 28, "APP")]}),
    ("tìm code mẫu python trong thư mục Github/samples", {"entities": [(4, 18, "QUERY"), (19, 48, "PATH")]}),
    
    # Câu lệnh phức tạp
    ("tìm file excel về doanh thu trong thư mục Tài chính/2023", {"entities": [(4, 8, "FILE"), (9, 22, "QUERY"), (23, 58, "PATH")]}),
    ("mở file báo cáo Q4 2023.pdf trong ổ D:/Reports bằng adobe reader", {"entities": [(4, 27, "FILE"), (28, 46, "PATH"), (53, 65, "APP")]}),
    ("tìm hình ảnh sản phẩm mới trong thư mục Marketing/Products", {"entities": [(4, 24, "QUERY"), (25, 60, "PATH")]}),
    ("phát video hướng dẫn sử dụng trong thư mục Training bằng media player", {"entities": [(5, 33, "QUERY"), (34, 56, "PATH"), (63, 75, "APP")]}),
]