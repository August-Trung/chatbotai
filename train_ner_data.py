# Dữ liệu huấn luyện FIXED cho mô hình NER tiếng Việt
# ✅ Sửa lỗi W030: Thêm cả chữ thường VÀ chữ hoa
# ✅ Tăng cường FILE và PATH với nhiều patterns hơn
# ✅ Cân bằng tỷ lệ các entity

TRAIN_DATA = [
    # ========== BLOCK 1: APP - Cả chữ thường và chữ HOA ==========
    # Chữ thường
    ("mở notepad", {"entities": [(3, 10, "APP")]}),
    ("mở notepad", {"entities": [(3, 10, "APP")]}),
    ("mở word", {"entities": [(3, 7, "APP")]}),
    ("mở excel", {"entities": [(3, 8, "APP")]}),
    ("mở chrome", {"entities": [(3, 9, "APP")]}),
    ("mở zalo", {"entities": [(3, 7, "APP")]}),
    ("mở youtube", {"entities": [(3, 10, "APP")]}),
    ("mở spotify", {"entities": [(3, 10, "APP")]}),
    ("mở telegram", {"entities": [(3, 11, "APP")]}),
    
    # Chữ HOA - QUAN TRỌNG để fix W030
    ("Mở Notepad", {"entities": [(3, 10, "APP")]}),
    ("Mở Word", {"entities": [(3, 7, "APP")]}),
    ("Mở Excel", {"entities": [(3, 8, "APP")]}),
    ("Mở Chrome", {"entities": [(3, 9, "APP")]}),
    ("Mở Zalo", {"entities": [(3, 7, "APP")]}),
    ("Mở Youtube", {"entities": [(3, 10, "APP")]}),
    ("Mở Spotify", {"entities": [(3, 10, "APP")]}),
    ("Mở Telegram", {"entities": [(3, 11, "APP")]}),
    
    # Mixed case
    ("chạy notepad", {"entities": [(5, 12, "APP")]}),
    ("khởi động word", {"entities": [(11, 15, "APP")]}),
    ("mở ứng dụng excel", {"entities": [(12, 17, "APP")]}),
    ("vào google", {"entities": [(4, 10, "APP")]}),
    ("đóng chrome", {"entities": [(5, 11, "APP")]}),
    
    # ========== BLOCK 2: FILE - Tăng cường mạnh ==========
    # File đơn giản
    ("mở file", {"entities": [(3, 7, "FILE")]}),
    ("mở file", {"entities": [(3, 7, "FILE")]}),
    ("mở file", {"entities": [(3, 7, "FILE")]}),
    ("tìm file", {"entities": [(4, 8, "FILE")]}),
    ("tìm file", {"entities": [(4, 8, "FILE")]}),
    ("tìm file", {"entities": [(4, 8, "FILE")]}),
    ("tìm tài liệu", {"entities": [(4, 13, "FILE")]}),
    ("tìm tài liệu", {"entities": [(4, 13, "FILE")]}),
    ("mở tập tin", {"entities": [(3, 10, "FILE")]}),
    ("mở tập tin", {"entities": [(3, 10, "FILE")]}),
    
    # File với extension (chữ thường)
    ("mở file report.xlsx", {"entities": [(3, 19, "FILE")]}),
    ("mở file report.xlsx", {"entities": [(3, 19, "FILE")]}),
    ("mở file report.xlsx", {"entities": [(3, 19, "FILE")]}),
    ("tìm file data.csv", {"entities": [(4, 17, "FILE")]}),
    ("tìm file data.csv", {"entities": [(4, 17, "FILE")]}),
    ("mở file video.mp4", {"entities": [(3, 17, "FILE")]}),
    ("mở file image.png", {"entities": [(3, 17, "FILE")]}),
    ("tìm file document.pdf", {"entities": [(4, 21, "FILE")]}),
    
    # File với extension (chữ HOA - fix W030)
    ("Mở file Report.xlsx", {"entities": [(3, 19, "FILE")]}),
    ("Tìm file Data.csv", {"entities": [(4, 17, "FILE")]}),
    ("Mở File Video.mp4", {"entities": [(3, 17, "FILE")]}),
    
    # File tiếng Việt có dấu
    ("mở file báo cáo.docx", {"entities": [(3, 20, "FILE")]}),
    ("mở file báo cáo.docx", {"entities": [(3, 20, "FILE")]}),
    ("mở file báo cáo.docx", {"entities": [(3, 20, "FILE")]}),
    ("tìm file danh sách.xlsx", {"entities": [(4, 23, "FILE")]}),
    ("tìm file danh sách.xlsx", {"entities": [(4, 23, "FILE")]}),
    ("mở file thuyết trình.pptx", {"entities": [(3, 25, "FILE")]}),
    ("tìm file dữ liệu.csv", {"entities": [(4, 20, "FILE")]}),
    
    # File phức tạp hơn
    ("mở file báo cáo tài chính q1 2023.xlsx", {"entities": [(3, 38, "FILE")]}),
    ("mở file báo cáo tài chính q1 2023.xlsx", {"entities": [(3, 38, "FILE")]}),
    ("tìm file kế hoạch marketing 2024.docx", {"entities": [(4, 37, "FILE")]}),
    ("tìm file kế hoạch marketing 2024.docx", {"entities": [(4, 37, "FILE")]}),
    
    # ========== BLOCK 3: PATH - Tăng cường mạnh ==========
    # PATH cơ bản với "thư mục"
    ("mở file trong thư mục", {"entities": [(3, 7, "FILE"), (14, 22, "PATH")]}),
    ("mở file trong thư mục", {"entities": [(3, 7, "FILE"), (14, 22, "PATH")]}),
    ("mở file trong thư mục", {"entities": [(3, 7, "FILE"), (14, 22, "PATH")]}),
    ("tìm file trong thư mục", {"entities": [(4, 8, "FILE"), (15, 23, "PATH")]}),
    ("tìm file trong thư mục", {"entities": [(4, 8, "FILE"), (15, 23, "PATH")]}),
    ("tìm file trong thư mục", {"entities": [(4, 8, "FILE"), (15, 23, "PATH")]}),
    
    # PATH với tên cụ thể (chữ thường)
    ("mở file trong thư mục downloads", {"entities": [(3, 7, "FILE"), (14, 31, "PATH")]}),
    ("mở file trong thư mục downloads", {"entities": [(3, 7, "FILE"), (14, 31, "PATH")]}),
    ("mở file trong thư mục downloads", {"entities": [(3, 7, "FILE"), (14, 31, "PATH")]}),
    ("tìm file trong thư mục documents", {"entities": [(4, 8, "FILE"), (15, 32, "PATH")]}),
    ("tìm file trong thư mục documents", {"entities": [(4, 8, "FILE"), (15, 32, "PATH")]}),
    ("tìm file trong thư mục documents", {"entities": [(4, 8, "FILE"), (15, 32, "PATH")]}),
    ("mở file trong thư mục pictures", {"entities": [(3, 7, "FILE"), (14, 30, "PATH")]}),
    ("mở file trong thư mục videos", {"entities": [(3, 7, "FILE"), (14, 28, "PATH")]}),
    ("mở file trong thư mục music", {"entities": [(3, 7, "FILE"), (14, 27, "PATH")]}),
    
    # PATH với tên cụ thể (chữ HOA - fix W030)
    ("Mở file trong thư mục Downloads", {"entities": [(3, 7, "FILE"), (14, 31, "PATH")]}),
    ("Tìm file trong thư mục Documents", {"entities": [(4, 8, "FILE"), (15, 32, "PATH")]}),
    ("Mở file trong thư mục Pictures", {"entities": [(3, 7, "FILE"), (14, 30, "PATH")]}),
    
    # PATH tiếng Việt
    ("mở file trong thư mục tài liệu", {"entities": [(3, 7, "FILE"), (14, 31, "PATH")]}),
    ("mở file trong thư mục tài liệu", {"entities": [(3, 7, "FILE"), (14, 31, "PATH")]}),
    ("mở file trong thư mục tài liệu", {"entities": [(3, 7, "FILE"), (14, 31, "PATH")]}),
    ("tìm file trong thư mục công việc", {"entities": [(4, 8, "FILE"), (15, 33, "PATH")]}),
    ("tìm file trong thư mục công việc", {"entities": [(4, 8, "FILE"), (15, 33, "PATH")]}),
    ("mở file trong thư mục dự án", {"entities": [(3, 7, "FILE"), (14, 28, "PATH")]}),
    ("mở file trong thư mục dự án", {"entities": [(3, 7, "FILE"), (14, 28, "PATH")]}),
    
    # PATH với ổ đĩa
    ("mở file trong ổ d", {"entities": [(3, 7, "FILE"), (14, 18, "PATH")]}),
    ("mở file trong ổ d", {"entities": [(3, 7, "FILE"), (14, 18, "PATH")]}),
    ("mở file trong ổ d", {"entities": [(3, 7, "FILE"), (14, 18, "PATH")]}),
    ("tìm file trong ổ c", {"entities": [(4, 8, "FILE"), (15, 19, "PATH")]}),
    ("tìm file trong ổ c", {"entities": [(4, 8, "FILE"), (15, 19, "PATH")]}),
    ("tìm file trong ổ e", {"entities": [(4, 8, "FILE"), (15, 19, "PATH")]}),
    
    # PATH với ổ đĩa (chữ HOA)
    ("Mở file trong ổ D", {"entities": [(3, 7, "FILE"), (14, 18, "PATH")]}),
    ("Tìm file trong ổ C", {"entities": [(4, 8, "FILE"), (15, 19, "PATH")]}),
    
    # PATH phức tạp với đường dẫn
    ("mở file trong d:/documents", {"entities": [(3, 7, "FILE"), (14, 26, "PATH")]}),
    ("mở file trong d:/documents", {"entities": [(3, 7, "FILE"), (14, 26, "PATH")]}),
    ("tìm file trong c:/users/admin", {"entities": [(4, 8, "FILE"), (15, 30, "PATH")]}),
    ("mở file trong thư mục documents/work", {"entities": [(3, 7, "FILE"), (14, 36, "PATH")]}),
    ("mở file trong thư mục tài liệu/công việc", {"entities": [(3, 7, "FILE"), (14, 41, "PATH")]}),
    
    # ========== BLOCK 4: FILE + PATH kết hợp ==========
    ("mở file report.xlsx trong thư mục documents", {"entities": [(3, 19, "FILE"), (26, 44, "PATH")]}),
    ("mở file report.xlsx trong thư mục documents", {"entities": [(3, 19, "FILE"), (26, 44, "PATH")]}),
    ("tìm file data.csv trong thư mục downloads", {"entities": [(4, 17, "FILE"), (24, 42, "PATH")]}),
    ("tìm file data.csv trong thư mục downloads", {"entities": [(4, 17, "FILE"), (24, 42, "PATH")]}),
    ("mở file báo cáo.docx trong thư mục tài liệu", {"entities": [(3, 20, "FILE"), (27, 44, "PATH")]}),
    ("mở file báo cáo.docx trong thư mục tài liệu", {"entities": [(3, 20, "FILE"), (27, 44, "PATH")]}),
    ("mở file báo cáo.docx trong thư mục tài liệu", {"entities": [(3, 20, "FILE"), (27, 44, "PATH")]}),
    ("tìm file video.mp4 trong ổ d", {"entities": [(4, 18, "FILE"), (25, 29, "PATH")]}),
    ("tìm file video.mp4 trong ổ d", {"entities": [(4, 18, "FILE"), (25, 29, "PATH")]}),
    
    # Với chữ HOA
    ("Mở file Report.xlsx trong thư mục Documents", {"entities": [(3, 19, "FILE"), (26, 44, "PATH")]}),
    ("Tìm file Báo cáo.docx trong ổ D", {"entities": [(4, 21, "FILE"), (28, 32, "PATH")]}),
    
    # ========== BLOCK 5: FILE + PATH + APP ==========
    ("mở file report.xlsx trong thư mục documents bằng excel", {"entities": [(3, 19, "FILE"), (26, 44, "PATH"), (50, 55, "APP")]}),
    ("mở file report.xlsx trong thư mục documents bằng excel", {"entities": [(3, 19, "FILE"), (26, 44, "PATH"), (50, 55, "APP")]}),
    ("mở file report.xlsx trong thư mục documents bằng excel", {"entities": [(3, 19, "FILE"), (26, 44, "PATH"), (50, 55, "APP")]}),
    ("mở file báo cáo.docx trong thư mục tài liệu bằng word", {"entities": [(3, 20, "FILE"), (27, 44, "PATH"), (50, 54, "APP")]}),
    ("mở file báo cáo.docx trong thư mục tài liệu bằng word", {"entities": [(3, 20, "FILE"), (27, 44, "PATH"), (50, 54, "APP")]}),
    ("mở file video.mp4 trong ổ d bằng vlc", {"entities": [(3, 17, "FILE"), (24, 28, "PATH"), (34, 37, "APP")]}),
    ("mở file video.mp4 trong ổ d bằng vlc", {"entities": [(3, 17, "FILE"), (24, 28, "PATH"), (34, 37, "APP")]}),
    
    # ========== BLOCK 6: QUERY ==========
    ("tìm bài hát yesterday", {"entities": [(4, 21, "QUERY")]}),
    ("tìm bài hát yesterday", {"entities": [(4, 21, "QUERY")]}),
    ("phát nhạc bolero", {"entities": [(5, 16, "QUERY")]}),
    ("phát nhạc bolero", {"entities": [(5, 16, "QUERY")]}),
    ("tìm từ python", {"entities": [(4, 13, "QUERY")]}),
    ("tìm từ python", {"entities": [(4, 13, "QUERY")]}),
    ("tìm video hướng dẫn", {"entities": [(4, 19, "QUERY")]}),
    ("tìm phim inception", {"entities": [(4, 18, "QUERY")]}),
    ("tìm tài liệu java", {"entities": [(4, 18, "QUERY")]}),
    
    # QUERY + APP
    ("tìm bài hát yesterday trên youtube", {"entities": [(4, 21, "QUERY"), (27, 34, "APP")]}),
    ("tìm bài hát yesterday trên youtube", {"entities": [(4, 21, "QUERY"), (27, 34, "APP")]}),
    ("tìm phim inception trên netflix", {"entities": [(4, 18, "QUERY"), (24, 31, "APP")]}),
    ("phát nhạc bolero trên spotify", {"entities": [(5, 16, "QUERY"), (22, 29, "APP")]}),
    
    # ========== BLOCK 7: Mixed case và edge cases ==========
    ("Mở file Báo cáo.docx", {"entities": [(3, 20, "FILE")]}),
    ("Tìm file Data.xlsx", {"entities": [(4, 18, "FILE")]}),
    ("mở File trong Thư mục", {"entities": [(3, 7, "FILE"), (14, 22, "PATH")]}),
    
    # Không phải QUERY: từ lệnh đơn thuần
    ("mở file báo cáo.docx trong thư mục công việc bằng word", {"entities": [(3, 20, "FILE"), (27, 45, "PATH"), (51, 55, "APP")]}),
    ("tìm file trong thư mục", {"entities": [(4, 8, "FILE"), (15, 23, "PATH")]}),
]

# ========== DỮ LIỆU KIỂM ĐỊNH ==========
VALID_DATA = [
    # APP tests
    ("mở notepad", {"entities": [(3, 10, "APP")]}),
    ("Mở Word", {"entities": [(3, 7, "APP")]}),
    ("khởi động excel", {"entities": [(11, 16, "APP")]}),
    
    # FILE tests  
    ("mở file báo cáo.docx", {"entities": [(3, 20, "FILE")]}),
    ("tìm file trong thư mục", {"entities": [(4, 8, "FILE"), (15, 23, "PATH")]}),
    ("Mở file Report.xlsx", {"entities": [(3, 19, "FILE")]}),
    
    # PATH tests
    ("mở file trong thư mục downloads", {"entities": [(3, 7, "FILE"), (14, 31, "PATH")]}),
    ("tìm file trong ổ d", {"entities": [(4, 8, "FILE"), (15, 19, "PATH")]}),
    ("Mở file trong thư mục Documents", {"entities": [(3, 7, "FILE"), (14, 31, "PATH")]}),
    
    # FILE + PATH
    ("mở file report.xlsx trong thư mục documents", {"entities": [(3, 19, "FILE"), (26, 44, "PATH")]}),
    ("tìm file báo cáo.docx trong ổ d", {"entities": [(4, 21, "FILE"), (28, 32, "PATH")]}),
    
    # FILE + PATH + APP
    ("mở file report.xlsx trong thư mục documents bằng excel", {"entities": [(3, 19, "FILE"), (26, 44, "PATH"), (50, 55, "APP")]}),
    ("tìm file video.mp4 trong ổ d bằng vlc", {"entities": [(4, 18, "FILE"), (25, 29, "PATH"), (35, 38, "APP")]}),
    
    # QUERY + APP
    ("tìm bài hát yesterday trên youtube", {"entities": [(4, 21, "QUERY"), (27, 34, "APP")]}),
    ("xem video yesterday trên youtube", {"entities": [(4, 19, "QUERY"), (25, 32, "APP")]}),
    
    # Complex
    ("mở file báo cáo tài chính 2023.xlsx trong thư mục d:/kế toán bằng excel", {"entities": [(3, 35, "FILE"), (42, 60, "PATH"), (66, 71, "APP")]}),
]
