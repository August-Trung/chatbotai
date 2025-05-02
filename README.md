# Trợ lý AI Desktop (Chatbot Điều khiển Máy tính)

Một chatbot AI cá nhân chạy trên desktop, được thiết kế để hiểu các lệnh bằng tiếng Việt và thực hiện các tác vụ hàng ngày, giúp tự động hóa công việc trên máy tính.

## Mục tiêu Dự án

Xây dựng một trợ lý ảo có khả năng:

-   Hiểu ngôn ngữ tự nhiên (tiếng Việt).
-   Tương tác với hệ điều hành để thực thi các lệnh cơ bản và nâng cao.
-   Cung cấp giao diện người dùng thân thiện và dễ sử dụng.

## Các Chức năng Hiện tại (Tính đến V6.8.1)

Dựa trên phiên bản code trong file `chatbot_gui_v1.py`:

**1. Giao diện Người dùng (UI):**

-   Giao diện đồ họa xây dựng bằng CustomTkinter.
-   Hiển thị lịch sử chat dạng bong bóng, phân biệt Bot và Người dùng.
-   Hỗ trợ chuyển đổi chế độ Sáng (Light) / Tối (Dark) qua nút bấm.
-   Ô nhập liệu hỗ trợ xem lại lịch sử lệnh bằng phím Lên/Xuống.
-   Hỗ trợ dán nhanh vào ô nhập liệu bằng cách nhấn chuột phải.
-   Nút "Xem thêm" tự động ẩn/hiện khi có nhiều kết quả tìm kiếm file.

**2. Điều khiển Ứng dụng:**

-   **Mở Ứng dụng:** Bằng lệnh `mở [tên]` hoặc `khởi động [tên]`.
    -   Hỗ trợ các ứng dụng được định nghĩa sẵn (Notepad, Edge, Chrome, CMD, Explorer, Calculator,...).
    -   Hỗ trợ tên viết tắt (alias) như `note`, `me`, `cal`, `exp`.
-   **Đóng Ứng dụng:** Bằng lệnh `đóng [tên]` hoặc `tắt [tên]`.
    -   Hỗ trợ alias.
    -   Đóng dựa trên tên tiến trình (có thể đóng tất cả cửa sổ của ứng dụng đó).

**3. Tương tác Web (Mở tab mới):**

-   **Mở URL:** Lệnh `truy cập`, `vào web`, `mở web`, `mở trang`, `mở` + URL/tên web/alias (ví dụ: `mở gg`, `truy cập vnexpress.net`).
-   **Tìm kiếm Google:** Lệnh `tìm kiếm`, `search`, `tìm`, `vào` + nội dung tìm kiếm.
-   **Tìm nhạc:**
    -   `tìm nhạc [bài hát]` -> Mặc định tìm trên YouTube.
    -   `tìm nhạc [bài hát] trên google` (hoặc `bằng gg`,...) -> Tìm trên Google Search.
-   **Chỉ định Trình duyệt:** Hỗ trợ thêm `trong [browser]`, `bằng [browser]`, `trên [browser]` (ví dụ: `truy cập voz bằng me`). Hỗ trợ alias cho trình duyệt.
-   **Chạy nền:** Các thao tác web được chạy trong luồng riêng để tránh treo giao diện.

**4. Tìm kiếm File:**

-   **Lệnh:** `tìm file`, `kiếm file`,... + tên/mẫu/loại file.
-   **Tìm theo Tên/Mẫu:** Hỗ trợ tìm kiếm chứa chuỗi hoặc dùng ký tự đại diện (`*`, `?`).
-   **Tìm theo Loại File:** Hỗ trợ tìm theo loại thông dụng (excel, word, ảnh, video, nhạc, pdf,...) và các alias/đuôi file cụ thể (ppt, xlsx, jpg,...).
-   **Tìm theo Vị trí:** Hỗ trợ chỉ định vị trí tìm kiếm bằng giới từ và tên quen thuộc (ví dụ: `tìm file excel trong ổ D`, `kiếm ảnh trên desktop`).
-   **Phạm vi Mặc định:** Desktop, Documents, Downloads, Pictures, Music, Videos nếu không chỉ định vị trí.
-   **Sắp xếp:** Kết quả tự động sắp xếp theo ngày sửa đổi mới nhất.
-   **Phân trang:** Hiển thị tối đa 15 kết quả/lần, có nút và lệnh "Xem thêm"/"thêm" để xem tiếp.
-   **Chạy nền:** Tìm kiếm file chạy trong luồng riêng để tránh treo giao diện.

**5. Xử lý Ngôn ngữ:**

-   Hỗ trợ nhiều từ khóa tiếng Việt cho mỗi hành động.
-   Hỗ trợ alias (tên viết tắt) cho ứng dụng, website và loại file.
-   Xử lý lỗi cơ bản cho các lệnh không hiểu hoặc không thực hiện được.

## Công nghệ sử dụng

-   **Ngôn ngữ:** Python 3
-   **Giao diện:** CustomTkinter
-   **Thư viện chuẩn:** `os`, `subprocess`, `platform`, `webbrowser`, `urllib.parse`, `threading`, `fnmatch`, `time`, `tkinter`, `base64`, `io`.
    -   _Lưu ý: Đã loại bỏ Selenium._
    -   _Lưu ý: Chưa tích hợp thư viện xử lý ảnh (Pillow) dù đã có code chuẩn bị._

## Cài đặt và Chạy

1.  **Yêu cầu:** Cài đặt Python 3.
2.  **Cài đặt thư viện:**
    ```bash
    pip install customtkinter
    # pip install Pillow # Cần nếu muốn thêm avatar hình ảnh sau này
    ```
3.  **Chạy ứng dụng:**
    ```bash
    python chatbot_gui_v1.py
    ```

## Cách sử dụng (Ví dụ Lệnh)

-   `mở notepad` hoặc `mở note`
-   `đóng edge` hoặc `tắt me`
-   `truy cập google.com` hoặc `mở gg`
-   `tìm kiếm giá vàng hôm nay` hoặc `tìm thời tiết`
-   `tìm nhạc đường một chiều` (sẽ tìm trên YouTube)
-   `tìm nhạc see tình trên google` (sẽ tìm trên Google)
-   `mở facebook bằng chrome`
-   `tìm file báo cáo *.docx`
-   `kiếm file ảnh trên desktop`
-   `tìm file excel trong ổ D`
-   `thêm` (sau khi tìm file có nhiều kết quả)

## Kế hoạch Phát triển Tương lai

-   **Chức năng Sao chép/Di chuyển File:** Thêm khả năng quản lý file cơ bản.
-   **Xử lý Ngôn ngữ Tự nhiên (NLP) Nâng cao:**
    -   Hiểu các câu lệnh phức tạp hơn, chứa nhiều hành động.
    -   Xử lý các biến thể ngữ pháp, lỗi chính tả linh hoạt hơn.
    -   Có thể tích hợp các thư viện NLP như spaCy, Rasa hoặc các mô hình ngôn ngữ.
-   **Tương tác Web Nâng cao (Bước 2 đã tạm dừng):**
    -   Kiểm tra và tương tác với các tab trình duyệt đang mở sẵn (sử dụng Selenium/Playwright).
    -   Tự động hóa các tác vụ trên web (ví dụ: đăng nhập, điền form cơ bản).
-   **Cải thiện Giao diện:**
    -   Thêm Avatar hình ảnh thực sự.
    -   Tinh chỉnh thêm về màu sắc, font chữ, bố cục.
    -   Có thể thêm các hiệu ứng chuyển động nhẹ.
-   **Khả năng Học hỏi & Tùy chỉnh:**
    -   Cho phép người dùng tự thêm alias, ứng dụng, vị trí tìm kiếm,...
    -   Lưu trữ lịch sử/cài đặt người dùng.
-   **Đóng gói Thành ứng dụng:** Sử dụng PyInstaller hoặc các công cụ tương tự để đóng gói thành file `.exe` (Windows) hoặc ứng dụng độc lập cho các HĐH khác.