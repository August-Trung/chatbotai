import random

# Sinh dữ liệu tự động các câu cơ bản và câu mở trung thực (non-random)
apps = ["Word", "Excel", "Notepad", "PowerPoint", "VLC", "Chrome", "Spotify", "Zalo", "Telegram", "YouTube"]
# Thêm các biến thể chữ hoa/thường cho từng ứng dụng
app_variants = {
    "Word": ["word", "WORD", "Word"],
    "Excel": ["excel", "EXCEL", "Excel", "exel", "exell"],  # Thêm lỗi chính tả phổ biến
    "Notepad": ["notepad", "NOTEPAD", "Notepad", "NotePad"],
    "PowerPoint": ["powerpoint", "POWERPOINT", "PowerPoint", "Power Point"],
    "VLC": ["vlc", "VLC"],
    "Chrome": ["chrome", "CHROME", "Chrome"],
    "Spotify": ["spotify", "SPOTIFY", "Spotify"],
    "Zalo": ["zalo", "ZALO", "Zalo"],
    "Telegram": ["telegram", "TELEGRAM", "Telegram"],
    "YouTube": ["youtube", "YOUTUBE", "Youtube", "you tube", "you-tube"]
}

app_templates = [
    "mở ứng dụng {}", "khởi động {}", "chạy {}", "dùng {}", "bật ứng dụng {}",
    "mở phần mềm {}", "khởi chạy {}", "mở trình duyệt {}", "mở {}", "hãy mở {}", 
    "tôi muốn mở {}", "làm ơn mở {}", "giúp tôi mở {}"
]

files = ["Báo cáo.docx", "update.xlsx", "report.pdf", "data.csv", "slide.pptx", 
         "Báo cáo Tài chính 2023.xlsx", "danh sách khách hàng.xlsx", "báo cáo năm 2023.docx",
         "slide thuyết trình.pptx", "report.xlsx"]
file_templates = [
    "mở file {}", "tìm file {}", "xem file {}", "chạy file {}", "kiểm tra file {}",
    "mở tài liệu {}", "mở báo cáo {}", "mở bảng tính {}", "đọc file {}", "xem tài liệu {}",
    "giúp tôi mở file {}", "tôi muốn xem file {}", "hãy mở file {}"
]

paths = ["thư mục Tài liệu", "thư mục Downloads", "ổ D", "D:\\Học tập", "Desktop\\Projects",
         "D:/Kế Toán", "Desktop\\Thuyết trình cuối kỳ", "D:/Reports", "thư mục Marketing",
         "thư mục Học tập", "ổ C", "ổ E", "D:\\Tài liệu\\Công việc"]
path_templates = [
    "trong {}", "ở {}", "truy cập {}", "đi tới {}", "trong thư mục {}",
    "trong ổ {}", "từ {}", "tại {}", "nằm trong {}", "ở trong {}"
]

queries = ["Yesterday", "Faded", "Hello", "Hạ Còn Vương Nắng", "Despacito", 
           "Độ ta không độ nàng", "Em của ngày hôm qua", "Python nâng cao", 
           "luật dân sự", "bầu trời hoàng hôn"]
query_templates = [
    "tìm bài hát {} trên Youtube", "xem video {} trên Youtube",
    "nghe nhạc {} trên Spotify", "phát bài hát {}", "tìm kiếm video {}",
    "tìm tài liệu về {}", "tìm thông tin về {}", "tra cứu {}", 
    "tìm kiếm {}", "xem hình ảnh về {}", "tìm hình ảnh {}"
]

# Hàm sinh spaCy data
def generate_spacy_data():
    data = []
    
    # Các câu mở APP (với đa dạng biến thể)
    for app in apps:
        for variant in app_variants[app]:
            # Câu đơn giản
            sent = f"mở {variant}"
            start = sent.index(variant)
            data.append((sent, {"entities": [(start, start+len(variant), "APP")] }))
            
            # Câu với chữ hoa đầu câu
            sent2 = f"Mở {variant}"
            start2 = sent2.index(variant)
            data.append((sent2, {"entities": [(start2, start2+len(variant), "APP")] }))
            
            # Câu với template ngẫu nhiên
            for tmpl in random.sample(app_templates, min(3, len(app_templates))):
                sent = tmpl.format(variant)
                start = sent.index(variant)
                data.append((sent, {"entities": [(start, start+len(variant), "APP")] }))
    
    # FILE
    for file in files:
        # Câu đơn giản
        sent = f"mở file {file}"
        start = sent.index(file)
        data.append((sent, {"entities": [(start, start+len(file), "FILE")] }))
        
        # Với template ngẫu nhiên
        for tmpl in random.sample(file_templates, min(3, len(file_templates))):
            sent = tmpl.format(file)
            start = sent.index(file)
            data.append((sent, {"entities": [(start, start+len(file), "FILE")] }))
    
    # PATH
    for path in paths:
        # Câu đơn giản với PATH
        sent = f"đi tới {path}"
        start = sent.index(path)
        data.append((sent, {"entities": [(start, start+len(path), "PATH")] }))
        
        # Với template ngẫu nhiên
        for tmpl in random.sample(path_templates, min(3, len(path_templates))):
            sent = tmpl.format(path)
            start = sent.index(path)
            data.append((sent, {"entities": [(start, start+len(path), "PATH")] }))
    
    # FILE + PATH - đảm bảo coverage
    for file in random.sample(files, 3):
        for path in random.sample(paths, 3):
            sent = f"mở file {file} trong {path}"
            file_start = sent.index(file)
            path_start = sent.index(path)
            data.append((sent, {"entities": [(file_start, file_start+len(file), "FILE"), 
                                              (path_start, path_start+len(path), "PATH")] }))
    
    # FILE + PATH + APP - đảm bảo coverage
    for file in random.sample(files, 2):
        for path in random.sample(paths, 2):
            for app in random.sample(apps, 2):
                for variant in random.sample(app_variants[app], 1):
                    sent = f"mở file {file} trong {path} bằng {variant}"
                    file_start = sent.index(file)
                    path_start = sent.index(path)
                    app_start = sent.index(variant)
                    data.append((sent, {"entities": [(file_start, file_start+len(file), "FILE"), 
                                                     (path_start, path_start+len(path), "PATH"),
                                                     (app_start, app_start+len(variant), "APP")] }))
    
    # QUERY
    for query in queries:
        # Câu đơn giản với QUERY
        sent = f"tìm kiếm {query}"
        start = sent.index(query)
        data.append((sent, {"entities": [(start, start+len(query), "QUERY")] }))
    
    # QUERY + APP
    for query in queries:
        for app in ["Youtube", "YouTube", "Spotify", "SPOTIFY"]:
            app_type = "YouTube" if app.lower() in ["youtube", "you tube", "youtube"] else "Spotify"
            sent = f"tìm bài hát {query} trên {app}"
            query_start = sent.index(query)
            app_start = sent.index(app)
            data.append((sent, {"entities": [(query_start, query_start+len(query), "QUERY"),
                                              (app_start, app_start+len(app), "APP")] }))
    
    # QUERY + PATH
    for query in random.sample(queries, 3):
        for path in random.sample(paths, 3):
            sent = f"tìm tài liệu về {query} trong {path}"
            query_start = sent.index(query)
            path_start = sent.index(path)
            data.append((sent, {"entities": [(query_start, query_start+len(query), "QUERY"),
                                              (path_start, path_start+len(path), "PATH")] }))
            
    return data

# Ví dụ phức tạp bổ sung - đặc biệt tập trung vào các trường hợp đặc biệt trong kết quả test
manual_spacy = [
    ('phát bài hát Faded trên Spotify', {'entities': [(13, 18, 'QUERY'), (24, 31, 'APP')]}),
('mở ứng dụng Chrome', {'entities': [(12, 18, 'APP')]}),
('truy cập C:\\Users\\Admin\\Documents', {'entities': [(9, 33, 'PATH')]}),
('mở ứng dụng VLC', {'entities': [(12, 15, 'APP')]}),
('mở file update.xlsx bằng Excel', {'entities': [(8, 19, 'FILE'), (25, 30, 'APP')]}),
('mở ứng dụng VLC', {'entities': [(12, 15, 'APP')]}),
('tìm file report_final.pdf trong thư mục Downloads', {'entities': [(9, 25, 'FILE'), (32, 49, 'PATH')]}),
('mở file Hello.mp3', {'entities': [(8, 17, 'FILE')]}),
('mở ứng dụng Word', {'entities': [(12, 16, 'APP')]}),
('phát bài hát Hello trên PowerPoint', {'entities': [(13, 18, 'QUERY'), (24, 34, 'APP')]}),
('mở ứng dụng VLC', {'entities': [(12, 15, 'APP')]}),
('phát bài hát Faded trên Spotify', {'entities': [(13, 18, 'QUERY'), (24, 31, 'APP')]}),
('mở ứng dụng Photoshop', {'entities': [(12, 21, 'APP')]}),
('mở ứng dụng VLC', {'entities': [(12, 15, 'APP')]}),
('truy cập ổ D', {'entities': [(9, 12, 'PATH')]}),
('truy cập thư mục Học tập', {'entities': [(9, 24, 'PATH')]}),
('truy cập E:\\Media', {'entities': [(9, 17, 'PATH')]}),
('mở file update.xlsx bằng Excel', {'entities': [(8, 19, 'FILE'), (25, 30, 'APP')]}),
('phát bài hát Hạ Còn Vương Nắng trên VLC', {'entities': [(13, 30, 'QUERY'), (36, 39, 'APP')]}),
('truy cập ổ D', {'entities': [(9, 12, 'PATH')]}),
('truy cập ổ D', {'entities': [(9, 12, 'PATH')]}),
('mở file presentation.pptx', {'entities': [(8, 25, 'FILE')]}),
('tìm file report_final.pdf trong thư mục Downloads', {'entities': [(9, 25, 'FILE'), (32, 49, 'PATH')]}),
('mở ứng dụng Chrome', {'entities': [(12, 18, 'APP')]}),
('mở ứng dụng PowerPoint', {'entities': [(12, 22, 'APP')]}),
('phát bài hát Hạ Còn Vương Nắng trên VLC', {'entities': [(13, 30, 'QUERY'), (36, 39, 'APP')]}),
('mở file báo cáo.docx', {'entities': [(8, 20, 'FILE')]}),
('mở file Báo cáo.docx trong ổ D', {'entities': [(8, 20, 'FILE'), (27, 30, 'PATH')]}),
('mở ứng dụng Zalo', {'entities': [(12, 16, 'APP')]}),
('mở file Faded.mp4', {'entities': [(8, 17, 'FILE')]}),
('truy cập E:\\Media', {'entities': [(9, 17, 'PATH')]}),
('truy cập thư mục Downloads', {'entities': [(9, 26, 'PATH')]}),
('xem video Faded trên Youtube', {'entities': [(10, 15, 'QUERY'), (21, 28, 'APP')]}),
('mở file data.png', {'entities': [(8, 16, 'FILE')]}),
('mở ứng dụng PowerPoint', {'entities': [(12, 22, 'APP')]}),
('mở file data.png', {'entities': [(8, 16, 'FILE')]}),
('mở file presentation.pptx', {'entities': [(8, 25, 'FILE')]}),
('mở ứng dụng Excel', {'entities': [(12, 17, 'APP')]}),
('phát bài hát Hello trên PowerPoint', {'entities': [(13, 18, 'QUERY'), (24, 34, 'APP')]}),
('truy cập D:\\Báo cáo', {'entities': [(9, 19, 'PATH')]}),
('mở ứng dụng PowerPoint', {'entities': [(12, 22, 'APP')]}),
('mở ứng dụng Zalo', {'entities': [(12, 16, 'APP')]}),
('phát bài hát Tháng Tư là lời nói dối trên Excel', {'entities': [(13, 36, 'QUERY'), (42, 47, 'APP')]}),
('mở file báo cáo.docx', {'entities': [(8, 20, 'FILE')]}),
('phát bài hát Hello trên PowerPoint', {'entities': [(13, 18, 'QUERY'), (24, 34, 'APP')]}),
('truy cập ổ D', {'entities': [(9, 12, 'PATH')]}),
('phát bài hát Hello trên PowerPoint', {'entities': [(13, 18, 'QUERY'), (24, 34, 'APP')]}),
('phát bài hát Faded trên Spotify', {'entities': [(13, 18, 'QUERY'), (24, 31, 'APP')]}),
('mở file Báo cáo.docx trong ổ D', {'entities': [(8, 20, 'FILE'), (27, 30, 'PATH')]}),
('phát bài hát Faded trên Spotify', {'entities': [(13, 18, 'QUERY'), (24, 31, 'APP')]}),
('truy cập ổ D', {'entities': [(9, 12, 'PATH')]}),
('phát bài hát Tháng Tư là lời nói dối trên Excel', {'entities': [(13, 36, 'QUERY'), (42, 47, 'APP')]}),
('mở ứng dụng Word', {'entities': [(12, 16, 'APP')]}),
('mở file Hello.mp3', {'entities': [(8, 17, 'FILE')]}),
('mở file Hello.mp3', {'entities': [(8, 17, 'FILE')]}),
('mở ứng dụng Spotify', {'entities': [(12, 19, 'APP')]}),
('truy cập thư mục Tài liệu', {'entities': [(9, 25, 'PATH')]}),
('phát bài hát Hạ Còn Vương Nắng trên VLC', {'entities': [(13, 30, 'QUERY'), (36, 39, 'APP')]}),
('truy cập C:\\Users\\Admin\\Documents', {'entities': [(9, 33, 'PATH')]}),
('mở file update.xlsx', {'entities': [(8, 19, 'FILE')]}),
('mở ứng dụng Notepad', {'entities': [(12, 19, 'APP')]}),
('phát bài hát Faded trên Spotify', {'entities': [(13, 18, 'QUERY'), (24, 31, 'APP')]}),
('phát bài hát Despacito trên Notepad', {'entities': [(13, 22, 'QUERY'), (28, 35, 'APP')]}),
('truy cập E:\\Media', {'entities': [(9, 17, 'PATH')]}),
('truy cập thư mục Tài liệu', {'entities': [(9, 25, 'PATH')]}),
('mở ứng dụng Photoshop', {'entities': [(12, 21, 'APP')]}),
('mở ứng dụng Zalo', {'entities': [(12, 16, 'APP')]}),
('mở ứng dụng Chrome', {'entities': [(12, 18, 'APP')]}),
('mở file data.png', {'entities': [(8, 16, 'FILE')]}),
('truy cập D:\\Báo cáo', {'entities': [(9, 19, 'PATH')]}),
('mở file Báo cáo.docx trong ổ D', {'entities': [(8, 20, 'FILE'), (27, 30, 'PATH')]}),
('mở ứng dụng Zalo', {'entities': [(12, 16, 'APP')]}),
('phát bài hát Tháng Tư là lời nói dối trên Excel', {'entities': [(13, 36, 'QUERY'), (42, 47, 'APP')]}),
('mở ứng dụng Excel', {'entities': [(12, 17, 'APP')]}),
('phát bài hát Yesterday trên Word', {'entities': [(13, 22, 'QUERY'), (28, 32, 'APP')]}),
('mở ứng dụng Excel', {'entities': [(12, 17, 'APP')]}),
('mở ứng dụng Chrome', {'entities': [(12, 18, 'APP')]}),
('mở ứng dụng Chrome', {'entities': [(12, 18, 'APP')]}),
('mở ứng dụng Word', {'entities': [(12, 16, 'APP')]}),
('mở file báo cáo.docx', {'entities': [(8, 20, 'FILE')]}),
('mở file Báo cáo.docx trong ổ D', {'entities': [(8, 20, 'FILE'), (27, 30, 'PATH')]}),
('mở file data.png', {'entities': [(8, 16, 'FILE')]}),
('tìm video Hello trên Youtube và mở bằng VLC', {'entities': [(10, 15, 'QUERY'), (21, 28, 'APP'), (40, 43, 'APP')]}),
('mở file update.xlsx bằng Excel', {'entities': [(8, 19, 'FILE'), (25, 30, 'APP')]}),
('phát bài hát Yesterday trên Word', {'entities': [(13, 22, 'QUERY'), (28, 32, 'APP')]}),
('mở ứng dụng Photoshop', {'entities': [(12, 21, 'APP')]}),
('truy cập C:\\Users\\Admin\\Documents', {'entities': [(9, 33, 'PATH')]}),
('tìm video Hello trên Youtube và mở bằng VLC', {'entities': [(10, 15, 'QUERY'), (21, 28, 'APP'), (40, 43, 'APP')]}),
('mở ứng dụng Photoshop', {'entities': [(12, 21, 'APP')]}),
('mở ứng dụng Excel', {'entities': [(12, 17, 'APP')]}),
('tìm video Hello trên Youtube và mở bằng VLC', {'entities': [(10, 15, 'QUERY'), (21, 28, 'APP'), (40, 43, 'APP')]}),
('mở file Faded.mp4', {'entities': [(8, 17, 'FILE')]}),
('mở ứng dụng Chrome', {'entities': [(12, 18, 'APP')]}),
('mở ứng dụng Notepad', {'entities': [(12, 19, 'APP')]}),
('phát bài hát Hạ Còn Vương Nắng trên VLC', {'entities': [(13, 30, 'QUERY'), (36, 39, 'APP')]}),
('mở file update.xlsx bằng Excel', {'entities': [(8, 19, 'FILE'), (25, 30, 'APP')]}),
('xem video Faded trên Youtube', {'entities': [(10, 15, 'QUERY'), (21, 28, 'APP')]}),
('tìm video Hello trên Youtube và mở bằng VLC', {'entities': [(10, 15, 'QUERY'), (21, 28, 'APP'), (40, 43, 'APP')]}),
('mở file báo cáo.docx', {'entities': [(8, 20, 'FILE')]}),
('truy cập ổ D', {'entities': [(9, 12, 'PATH')]}),
('phát bài hát Hello trên PowerPoint', {'entities': [(13, 18, 'QUERY'), (24, 34, 'APP')]}),
('xem video Faded trên Youtube', {'entities': [(10, 15, 'QUERY'), (21, 28, 'APP')]}),
('mở ứng dụng Notepad', {'entities': [(12, 19, 'APP')]}),
('tìm video Hello trên Youtube và mở bằng VLC', {'entities': [(10, 15, 'QUERY'), (21, 28, 'APP'), (40, 43, 'APP')]}),
('truy cập D:\\Báo cáo', {'entities': [(9, 19, 'PATH')]}),
('truy cập E:\\Media', {'entities': [(9, 17, 'PATH')]}),
('mở ứng dụng Word', {'entities': [(12, 16, 'APP')]}),
('mở file report_final.pdf', {'entities': [(8, 24, 'FILE')]}),
('mở file report_final.pdf', {'entities': [(8, 24, 'FILE')]}),
('truy cập thư mục Downloads', {'entities': [(9, 26, 'PATH')]}),
('mở file report_final.pdf', {'entities': [(8, 24, 'FILE')]}),
('mở file Hello.mp3', {'entities': [(8, 17, 'FILE')]}),
('mở ứng dụng Word', {'entities': [(12, 16, 'APP')]}),
('truy cập C:\\Users\\Admin\\Documents', {'entities': [(9, 33, 'PATH')]}),
('mở ứng dụng Excel', {'entities': [(12, 17, 'APP')]}),
('truy cập ổ D', {'entities': [(9, 12, 'PATH')]}),
('xem video Faded trên Youtube', {'entities': [(10, 15, 'QUERY'), (21, 28, 'APP')]}),
('phát bài hát Despacito trên Notepad', {'entities': [(13, 22, 'QUERY'), (28, 35, 'APP')]}),
('mở file Faded.mp4', {'entities': [(8, 17, 'FILE')]}),
('truy cập thư mục Học tập', {'entities': [(9, 24, 'PATH')]}),
('mở file báo cáo.docx', {'entities': [(8, 20, 'FILE')]}),
('phát bài hát Hello trên PowerPoint', {'entities': [(13, 18, 'QUERY'), (24, 34, 'APP')]}),
('mở ứng dụng Spotify', {'entities': [(12, 19, 'APP')]}),
('mở file update.xlsx', {'entities': [(8, 19, 'FILE')]}),
('truy cập D:\\Báo cáo', {'entities': [(9, 19, 'PATH')]}),
('mở ứng dụng Chrome', {'entities': [(12, 18, 'APP')]}),
('mở file update.xlsx bằng Excel', {'entities': [(8, 19, 'FILE'), (25, 30, 'APP')]}),
('mở ứng dụng Photoshop', {'entities': [(12, 21, 'APP')]}),
('mở ứng dụng PowerPoint', {'entities': [(12, 22, 'APP')]}),
('mở file update.xlsx', {'entities': [(8, 19, 'FILE')]}),
('mở file report_final.pdf', {'entities': [(8, 24, 'FILE')]}),
('truy cập thư mục Học tập', {'entities': [(9, 24, 'PATH')]}),
('mở file báo cáo.docx', {'entities': [(8, 20, 'FILE')]}),
('truy cập thư mục Downloads', {'entities': [(9, 26, 'PATH')]}),
('mở file Báo cáo.docx trong ổ D', {'entities': [(8, 20, 'FILE'), (27, 30, 'PATH')]}),
('mở file update.xlsx bằng Excel', {'entities': [(8, 19, 'FILE'), (25, 30, 'APP')]}),
('truy cập thư mục Học tập', {'entities': [(9, 24, 'PATH')]}),
('xem video Faded trên Youtube', {'entities': [(10, 15, 'QUERY'), (21, 28, 'APP')]}),
('phát bài hát Tháng Tư là lời nói dối trên Excel', {'entities': [(13, 36, 'QUERY'), (42, 47, 'APP')]}),
('phát bài hát Yesterday trên Word', {'entities': [(13, 22, 'QUERY'), (28, 32, 'APP')]}),
('phát bài hát Tháng Tư là lời nói dối trên Excel', {'entities': [(13, 36, 'QUERY'), (42, 47, 'APP')]}),
('truy cập D:\\Báo cáo', {'entities': [(9, 19, 'PATH')]}),
('mở file Báo cáo.docx trong ổ D', {'entities': [(8, 20, 'FILE'), (27, 30, 'PATH')]}),
('phát bài hát Hạ Còn Vương Nắng trên VLC', {'entities': [(13, 30, 'QUERY'), (36, 39, 'APP')]}),
('tìm video Hello trên Youtube và mở bằng VLC', {'entities': [(10, 15, 'QUERY'), (21, 28, 'APP'), (40, 43, 'APP')]}),
('truy cập thư mục Downloads', {'entities': [(9, 26, 'PATH')]}),
('mở ứng dụng Notepad', {'entities': [(12, 19, 'APP')]}),
('mở file báo cáo.docx', {'entities': [(8, 20, 'FILE')]}),
('mở ứng dụng Zalo', {'entities': [(12, 16, 'APP')]}),
('phát bài hát Yesterday trên Word', {'entities': [(13, 22, 'QUERY'), (28, 32, 'APP')]}),
('mở file Hello.mp3', {'entities': [(8, 17, 'FILE')]}),
('tìm file report_final.pdf trong thư mục Downloads', {'entities': [(9, 25, 'FILE'), (32, 49, 'PATH')]}),
('truy cập thư mục Học tập', {'entities': [(9, 24, 'PATH')]}),
('phát bài hát Despacito trên Notepad', {'entities': [(13, 22, 'QUERY'), (28, 35, 'APP')]}),
('phát bài hát Yesterday trên Word', {'entities': [(13, 22, 'QUERY'), (28, 32, 'APP')]}),
('mở ứng dụng Notepad', {'entities': [(12, 19, 'APP')]}),
('mở ứng dụng Word', {'entities': [(12, 16, 'APP')]}),
('mở ứng dụng Spotify', {'entities': [(12, 19, 'APP')]}),
('phát bài hát Hello trên PowerPoint', {'entities': [(13, 18, 'QUERY'), (24, 34, 'APP')]}),
('phát bài hát Hạ Còn Vương Nắng trên VLC', {'entities': [(13, 30, 'QUERY'), (36, 39, 'APP')]}),
('truy cập C:\\Users\\Admin\\Documents', {'entities': [(9, 33, 'PATH')]}),
('truy cập thư mục Tài liệu', {'entities': [(9, 25, 'PATH')]}),
('mở ứng dụng Notepad', {'entities': [(12, 19, 'APP')]}),
('truy cập thư mục Downloads', {'entities': [(9, 26, 'PATH')]}),
('mở file Hello.mp3', {'entities': [(8, 17, 'FILE')]}),
('mở file update.xlsx', {'entities': [(8, 19, 'FILE')]}),
('mở file Báo cáo.docx trong ổ D', {'entities': [(8, 20, 'FILE'), (27, 30, 'PATH')]}),
('mở file update.xlsx', {'entities': [(8, 19, 'FILE')]}),
('mở ứng dụng Chrome', {'entities': [(12, 18, 'APP')]}),
('truy cập ổ D', {'entities': [(9, 12, 'PATH')]}),
('mở ứng dụng Zalo', {'entities': [(12, 16, 'APP')]}),
('truy cập thư mục Tài liệu', {'entities': [(9, 25, 'PATH')]}),
('mở file report_final.pdf', {'entities': [(8, 24, 'FILE')]}),
('tìm file report_final.pdf trong thư mục Downloads', {'entities': [(9, 25, 'FILE'), (32, 49, 'PATH')]}),
('truy cập thư mục Học tập', {'entities': [(9, 24, 'PATH')]}),
('mở ứng dụng Notepad', {'entities': [(12, 19, 'APP')]}),
('mở ứng dụng Spotify', {'entities': [(12, 19, 'APP')]}),
('xem video Faded trên Youtube', {'entities': [(10, 15, 'QUERY'), (21, 28, 'APP')]}),
('truy cập C:\\Users\\Admin\\Documents', {'entities': [(9, 33, 'PATH')]}),
('mở ứng dụng Excel', {'entities': [(12, 17, 'APP')]}),
('mở file update.xlsx bằng Excel', {'entities': [(8, 19, 'FILE'), (25, 30, 'APP')]}),
('mở file presentation.pptx', {'entities': [(8, 25, 'FILE')]}),
('truy cập E:\\Media', {'entities': [(9, 17, 'PATH')]}),
('truy cập ổ D', {'entities': [(9, 12, 'PATH')]}),
('mở ứng dụng VLC', {'entities': [(12, 15, 'APP')]}),
('mở ứng dụng PowerPoint', {'entities': [(12, 22, 'APP')]}),
('mở file Faded.mp4', {'entities': [(8, 17, 'FILE')]}),
('phát bài hát Despacito trên Notepad', {'entities': [(13, 22, 'QUERY'), (28, 35, 'APP')]}),
('phát bài hát Hello trên PowerPoint', {'entities': [(13, 18, 'QUERY'), (24, 34, 'APP')]}),
('mở ứng dụng Photoshop', {'entities': [(12, 21, 'APP')]}),
('mở ứng dụng PowerPoint', {'entities': [(12, 22, 'APP')]}),
('truy cập ổ D', {'entities': [(9, 12, 'PATH')]}),
('mở file update.xlsx bằng Excel', {'entities': [(8, 19, 'FILE'), (25, 30, 'APP')]}),
('mở file Báo cáo.docx trong ổ D', {'entities': [(8, 20, 'FILE'), (27, 30, 'PATH')]}),
('phát bài hát Tháng Tư là lời nói dối trên Excel', {'entities': [(13, 36, 'QUERY'), (42, 47, 'APP')]}),
('truy cập C:\\Users\\Admin\\Documents', {'entities': [(9, 33, 'PATH')]}),
('mở file Báo cáo.docx trong ổ D', {'entities': [(8, 20, 'FILE'), (27, 30, 'PATH')]}),
('mở ứng dụng Spotify', {'entities': [(12, 19, 'APP')]}),
('mở file update.xlsx', {'entities': [(8, 19, 'FILE')]}),
('truy cập D:\\Báo cáo', {'entities': [(9, 19, 'PATH')]}),
('mở ứng dụng Spotify', {'entities': [(12, 19, 'APP')]}),
('mở file update.xlsx bằng Excel', {'entities': [(8, 19, 'FILE'), (25, 30, 'APP')]}),
('mở file Faded.mp4', {'entities': [(8, 17, 'FILE')]}),
('truy cập thư mục Tài liệu', {'entities': [(9, 25, 'PATH')]}),
('tìm video Hello trên Youtube và mở bằng VLC', {'entities': [(10, 15, 'QUERY'), (21, 28, 'APP'), (40, 43, 'APP')]}),
('mở ứng dụng Spotify', {'entities': [(12, 19, 'APP')]}),
('phát bài hát Hello trên PowerPoint', {'entities': [(13, 18, 'QUERY'), (24, 34, 'APP')]}),
('mở file Faded.mp4', {'entities': [(8, 17, 'FILE')]}),
('mở file báo cáo.docx', {'entities': [(8, 20, 'FILE')]}),
('mở file Hello.mp3', {'entities': [(8, 17, 'FILE')]}),
('mở ứng dụng Word', {'entities': [(12, 16, 'APP')]}),
('truy cập D:\\Báo cáo', {'entities': [(9, 19, 'PATH')]}),
('mở file report_final.pdf', {'entities': [(8, 24, 'FILE')]}),
('truy cập E:\\Media', {'entities': [(9, 17, 'PATH')]}),
('tìm file report_final.pdf trong thư mục Downloads', {'entities': [(9, 25, 'FILE'), (32, 49, 'PATH')]}),
('mở file update.xlsx', {'entities': [(8, 19, 'FILE')]}),
('tìm video Hello trên Youtube và mở bằng VLC', {'entities': [(10, 15, 'QUERY'), (21, 28, 'APP'), (40, 43, 'APP')]}),
('mở ứng dụng Word', {'entities': [(12, 16, 'APP')]}),
('truy cập thư mục Học tập', {'entities': [(9, 24, 'PATH')]}),
('mở ứng dụng VLC', {'entities': [(12, 15, 'APP')]}),
('mở file update.xlsx', {'entities': [(8, 19, 'FILE')]}),
('mở ứng dụng PowerPoint', {'entities': [(12, 22, 'APP')]}),
('phát bài hát Faded trên Spotify', {'entities': [(13, 18, 'QUERY'), (24, 31, 'APP')]}),
('mở ứng dụng VLC', {'entities': [(12, 15, 'APP')]}),
('mở ứng dụng VLC', {'entities': [(12, 15, 'APP')]}),
('mở file presentation.pptx', {'entities': [(8, 25, 'FILE')]}),
('mở file báo cáo.docx', {'entities': [(8, 20, 'FILE')]}),
('truy cập thư mục Downloads', {'entities': [(9, 26, 'PATH')]}),
('mở file presentation.pptx', {'entities': [(8, 25, 'FILE')]}),
('mở file Hello.mp3', {'entities': [(8, 17, 'FILE')]}),
('phát bài hát Tháng Tư là lời nói dối trên Excel', {'entities': [(13, 36, 'QUERY'), (42, 47, 'APP')]}),
('mở file Hello.mp3', {'entities': [(8, 17, 'FILE')]}),
('tìm file report_final.pdf trong thư mục Downloads', {'entities': [(9, 25, 'FILE'), (32, 49, 'PATH')]}),
('truy cập D:\\Báo cáo', {'entities': [(9, 19, 'PATH')]}),
('mở ứng dụng Spotify', {'entities': [(12, 19, 'APP')]}),
('mở file data.png', {'entities': [(8, 16, 'FILE')]}),
('truy cập thư mục Học tập', {'entities': [(9, 24, 'PATH')]}),
('truy cập E:\\Media', {'entities': [(9, 17, 'PATH')]}),
('mở ứng dụng Notepad', {'entities': [(12, 19, 'APP')]}),
('truy cập thư mục Tài liệu', {'entities': [(9, 25, 'PATH')]}),
('mở file report_final.pdf', {'entities': [(8, 24, 'FILE')]}),
('phát bài hát Yesterday trên Word', {'entities': [(13, 22, 'QUERY'), (28, 32, 'APP')]}),
('mở ứng dụng Zalo', {'entities': [(12, 16, 'APP')]}),
('mở file update.xlsx', {'entities': [(8, 19, 'FILE')]}),
('mở file data.png', {'entities': [(8, 16, 'FILE')]}),
('mở ứng dụng Excel', {'entities': [(12, 17, 'APP')]}),
('phát bài hát Hạ Còn Vương Nắng trên VLC', {'entities': [(13, 30, 'QUERY'), (36, 39, 'APP')]}),
('mở file Báo cáo.docx trong ổ D', {'entities': [(8, 20, 'FILE'), (27, 30, 'PATH')]}),
('mở ứng dụng Photoshop', {'entities': [(12, 21, 'APP')]}),
('truy cập E:\\Media', {'entities': [(9, 17, 'PATH')]}),
('phát bài hát Tháng Tư là lời nói dối trên Excel', {'entities': [(13, 36, 'QUERY'), (42, 47, 'APP')]}),
('tìm file report_final.pdf trong thư mục Downloads', {'entities': [(9, 25, 'FILE'), (32, 49, 'PATH')]}),
('xem video Faded trên Youtube', {'entities': [(10, 15, 'QUERY'), (21, 28, 'APP')]}),
('phát bài hát Hạ Còn Vương Nắng trên VLC', {'entities': [(13, 30, 'QUERY'), (36, 39, 'APP')]}),
('truy cập thư mục Học tập', {'entities': [(9, 24, 'PATH')]}),
('phát bài hát Despacito trên Notepad', {'entities': [(13, 22, 'QUERY'), (28, 35, 'APP')]}),
('truy cập D:\\Báo cáo', {'entities': [(9, 19, 'PATH')]}),
('phát bài hát Despacito trên Notepad', {'entities': [(13, 22, 'QUERY'), (28, 35, 'APP')]}),
('truy cập thư mục Tài liệu', {'entities': [(9, 25, 'PATH')]}),
('phát bài hát Despacito trên Notepad', {'entities': [(13, 22, 'QUERY'), (28, 35, 'APP')]}),
('phát bài hát Despacito trên Notepad', {'entities': [(13, 22, 'QUERY'), (28, 35, 'APP')]}),
('mở file presentation.pptx', {'entities': [(8, 25, 'FILE')]}),
('mở ứng dụng Notepad', {'entities': [(12, 19, 'APP')]}),
('phát bài hát Faded trên Spotify', {'entities': [(13, 18, 'QUERY'), (24, 31, 'APP')]}),
('tìm file report_final.pdf trong thư mục Downloads', {'entities': [(9, 25, 'FILE'), (32, 49, 'PATH')]}),
('truy cập D:\\Báo cáo', {'entities': [(9, 19, 'PATH')]}),
('phát bài hát Hạ Còn Vương Nắng trên VLC', {'entities': [(13, 30, 'QUERY'), (36, 39, 'APP')]}),
('mở file report_final.pdf', {'entities': [(8, 24, 'FILE')]}),
('mở file Faded.mp4', {'entities': [(8, 17, 'FILE')]}),
('mở file Faded.mp4', {'entities': [(8, 17, 'FILE')]}),
('mở file report_final.pdf', {'entities': [(8, 24, 'FILE')]}),
('phát bài hát Hello trên PowerPoint', {'entities': [(13, 18, 'QUERY'), (24, 34, 'APP')]}),
('truy cập thư mục Tài liệu', {'entities': [(9, 25, 'PATH')]}),
('phát bài hát Despacito trên Notepad', {'entities': [(13, 22, 'QUERY'), (28, 35, 'APP')]}),
('phát bài hát Yesterday trên Word', {'entities': [(13, 22, 'QUERY'), (28, 32, 'APP')]}),
('mở ứng dụng Word', {'entities': [(12, 16, 'APP')]}),
('truy cập thư mục Downloads', {'entities': [(9, 26, 'PATH')]}),
('mở ứng dụng Spotify', {'entities': [(12, 19, 'APP')]}),
('mở ứng dụng Excel', {'entities': [(12, 17, 'APP')]}),
('mở file Faded.mp4', {'entities': [(8, 17, 'FILE')]}),
('xem video Faded trên Youtube', {'entities': [(10, 15, 'QUERY'), (21, 28, 'APP')]}),
('mở ứng dụng Spotify', {'entities': [(12, 19, 'APP')]}),
('mở file Hello.mp3', {'entities': [(8, 17, 'FILE')]}),
('mở file update.xlsx bằng Excel', {'entities': [(8, 19, 'FILE'), (25, 30, 'APP')]}),
('phát bài hát Faded trên Spotify', {'entities': [(13, 18, 'QUERY'), (24, 31, 'APP')]}),
('mở ứng dụng Photoshop', {'entities': [(12, 21, 'APP')]}),
('mở file presentation.pptx', {'entities': [(8, 25, 'FILE')]}),
('mở file update.xlsx', {'entities': [(8, 19, 'FILE')]}),
('truy cập E:\\Media', {'entities': [(9, 17, 'PATH')]}),
('mở ứng dụng Zalo', {'entities': [(12, 16, 'APP')]}),
('phát bài hát Despacito trên Notepad', {'entities': [(13, 22, 'QUERY'), (28, 35, 'APP')]}),
('mở file data.png', {'entities': [(8, 16, 'FILE')]}),
('mở ứng dụng Excel', {'entities': [(12, 17, 'APP')]}),
('phát bài hát Yesterday trên Word', {'entities': [(13, 22, 'QUERY'), (28, 32, 'APP')]}),
('mở ứng dụng PowerPoint', {'entities': [(12, 22, 'APP')]}),
('phát bài hát Faded trên Spotify', {'entities': [(13, 18, 'QUERY'), (24, 31, 'APP')]}),
('truy cập thư mục Downloads', {'entities': [(9, 26, 'PATH')]}),
('mở file data.png', {'entities': [(8, 16, 'FILE')]}),
('phát bài hát Yesterday trên Word', {'entities': [(13, 22, 'QUERY'), (28, 32, 'APP')]}),
('truy cập C:\\Users\\Admin\\Documents', {'entities': [(9, 33, 'PATH')]}),
('mở ứng dụng Chrome', {'entities': [(12, 18, 'APP')]}),
('tìm file report_final.pdf trong thư mục Downloads', {'entities': [(9, 25, 'FILE'), (32, 49, 'PATH')]}),
('truy cập C:\\Users\\Admin\\Documents', {'entities': [(9, 33, 'PATH')]}),
('mở file data.png', {'entities': [(8, 16, 'FILE')]}),
('mở file presentation.pptx', {'entities': [(8, 25, 'FILE')]}),
('tìm video Hello trên Youtube và mở bằng VLC', {'entities': [(10, 15, 'QUERY'), (21, 28, 'APP'), (40, 43, 'APP')]}),
('mở ứng dụng Excel', {'entities': [(12, 17, 'APP')]}),
('xem video Faded trên Youtube', {'entities': [(10, 15, 'QUERY'), (21, 28, 'APP')]}),
('tìm video Hello trên Youtube và mở bằng VLC', {'entities': [(10, 15, 'QUERY'), (21, 28, 'APP'), (40, 43, 'APP')]}),
('mở ứng dụng Zalo', {'entities': [(12, 16, 'APP')]}),
('phát bài hát Hạ Còn Vương Nắng trên VLC', {'entities': [(13, 30, 'QUERY'), (36, 39, 'APP')]}),
('mở ứng dụng Word', {'entities': [(12, 16, 'APP')]}),
('truy cập thư mục Tài liệu', {'entities': [(9, 25, 'PATH')]}),
('truy cập thư mục Downloads', {'entities': [(9, 26, 'PATH')]}),
('mở file data.png', {'entities': [(8, 16, 'FILE')]}),
('mở ứng dụng Zalo', {'entities': [(12, 16, 'APP')]}),
('phát bài hát Tháng Tư là lời nói dối trên Excel', {'entities': [(13, 36, 'QUERY'), (42, 47, 'APP')]}),
('mở ứng dụng Notepad', {'entities': [(12, 19, 'APP')]}),
('phát bài hát Tháng Tư là lời nói dối trên Excel', {'entities': [(13, 36, 'QUERY'), (42, 47, 'APP')]}),
('mở ứng dụng PowerPoint', {'entities': [(12, 22, 'APP')]}),
('mở ứng dụng Photoshop', {'entities': [(12, 21, 'APP')]}),
('mở ứng dụng VLC', {'entities': [(12, 15, 'APP')]}),
('mở ứng dụng Photoshop', {'entities': [(12, 21, 'APP')]}),
('mở ứng dụng Chrome', {'entities': [(12, 18, 'APP')]}),
('mở file presentation.pptx', {'entities': [(8, 25, 'FILE')]}),
('mở file Faded.mp4', {'entities': [(8, 17, 'FILE')]}),
('mở file report_final.pdf', {'entities': [(8, 24, 'FILE')]}),
('tìm file report_final.pdf trong thư mục Downloads', {'entities': [(9, 25, 'FILE'), (32, 49, 'PATH')]}),
('truy cập thư mục Tài liệu', {'entities': [(9, 25, 'PATH')]}),
('phát bài hát Yesterday trên Word', {'entities': [(13, 22, 'QUERY'), (28, 32, 'APP')]}),
('xem video Faded trên Youtube', {'entities': [(10, 15, 'QUERY'), (21, 28, 'APP')]}),
('mở file presentation.pptx', {'entities': [(8, 25, 'FILE')]}),
('mở ứng dụng VLC', {'entities': [(12, 15, 'APP')]}),
('truy cập thư mục Downloads', {'entities': [(9, 26, 'PATH')]}),
('mở file báo cáo.docx', {'entities': [(8, 20, 'FILE')]}),
('truy cập thư mục Học tập', {'entities': [(9, 24, 'PATH')]}),
('truy cập E:\\Media', {'entities': [(9, 17, 'PATH')]}),
('phát bài hát Faded trên Spotify', {'entities': [(13, 18, 'QUERY'), (24, 31, 'APP')]}),
('mở ứng dụng PowerPoint', {'entities': [(12, 22, 'APP')]}),
('truy cập C:\\Users\\Admin\\Documents', {'entities': [(9, 33, 'PATH')]}),
]

# Tạo TRAIN_DATA
TRAIN_DATA = generate_spacy_data() + manual_spacy

# Dữ liệu kiểm định VALID_DATA nâng cao với tập trung vào các trường hợp khó
VALID_DATA = [
    # APP variants (hoa/thường/trừu tượng)
    ("mở notepad", {"entities": [(4, 11, "APP")] }),
    ("Mở Notepad", {"entities": [(4, 11, "APP")] }),
    ("mở NOTEPAD", {"entities": [(4, 11, "APP")] }),
    ("mở ứng dụng word", {"entities": [(13, 17, "APP")] }),
    ("mở Excel", {"entities": [(4, 9, "APP")] }),
    ("chạy excel", {"entities": [(5, 10, "APP")] }),
    # FILE + PATH
    ("mở file danh sách khách hàng.xlsx trong thư mục Marketing và chạy bằng Excel",
     {"entities": [(9, 38, "FILE"), (45, 62, "PATH"), (74, 79, "APP")] }),
    ("tìm file báo cáo năm 2023.docx trong ổ D:/Reports",
     {"entities": [(9, 36, "FILE"), (42, 53, "PATH")] }),
    ("mở file trong thư mục Downloads", {"entities": [(4, 8, "FILE"), (15, 33, "PATH")] }),
    ("tìm tài liệu trong ổ D", {"entities": [(4, 13, "QUERY"), (20, 23, "PATH")] }),
    # QUERY + APP
    ("tìm bài hát Yesterday trên youtube", {"entities": [(10, 19, "QUERY"), (25, 32, "APP")] }),
    ("Xem video Yesterday trên YouTube", {"entities": [(10, 19, "QUERY"), (25, 32, "APP")] }),
    ("phát nhạc Despacito trên SPOTIFY", {"entities": [(10, 19, "QUERY"), (25, 32, "APP")] }),
    ("tìm hình ảnh bầu trời hoàng hôn", {"entities": [(11, 30, "QUERY")] }),
    ("tìm tài liệu Python nâng cao trong thư mục Học tập", {"entities": [(15, 30, "QUERY"), (37, 52, "PATH")] }),
    # spelling typo case
    ("mở exel", {"entities": [(4, 8, "APP")] }),
    ("tìm bải hát Yesterday trên youtube", {"entities": [(10, 19, "QUERY"), (25, 32, "APP")] }),
    # Kiểm tra trường hợp đặc biệt từ kết quả test
    ("tìm file excel trong thư mục Downloads", {"entities": [(9, 14, "APP"), (21, 39, "PATH")] }),
    ("mở file report.xlsx bằng excel", {"entities": [(9, 20, "FILE"), (26, 31, "APP")] }),
    # Thêm các test case mới
    ("mở PowerPoint và trình chiếu file slide.pptx", {"entities": [(4, 14, "APP"), (33, 43, "FILE")] }),
    ("tìm tài liệu trong ổ D và mở bằng Word", {"entities": [(20, 23, "PATH"), (34, 38, "APP")] }),
]