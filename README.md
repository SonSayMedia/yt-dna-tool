# YT DNA Tool (chạy trên máy cá nhân)

Phần mềm chạy ngay trên máy của bạn (localhost), làm **2 việc chính**:

1. **Viết lại / tái tạo tiêu đề** YouTube theo "khuôn" của một kênh thành công (kèm từ khóa chính, dịch sang tiếng Việt, nhiều ngôn ngữ).
2. **Tạo prompt thumbnail** (tiếng Anh, dán vào Google Flow / ChatGPT / Gemini để ra ảnh) đồng nhất phong cách kênh: khóa font chữ, khóa bố cục, khóa nhân vật; chữ trên thumbnail viết **cùng ngôn ngữ với tiêu đề**.

## Cần chuẩn bị
| Thứ cần | Ghi chú |
|---|---|
| **Python 3.10+** | https://www.python.org/downloads/ — khi cài nhớ tick **"Add Python to PATH"** |
| **9router** đang chạy trên máy | Cổng AI (Gemini...) — mặc định `http://127.0.0.1:20128/v1`. Cần 1 key 9router |
| **YouTube Data API v3 key** | https://console.cloud.google.com → bật "YouTube Data API v3" → tạo API key (dạng `AIza...`) |

*(Không cần ffmpeg hay yt-dlp — bản này chỉ lấy thumbnail, không tải video.)*

## Cài & chạy (Windows)
1. Giải nén thư mục, nhấp đúp **`run.bat`** (lần đầu tự cài thư viện 1–2 phút; các lần sau chạy ngay).
2. Trình duyệt tự mở **http://127.0.0.1:5000**. Cửa sổ đen phải để nguyên khi dùng; đóng nó = tắt phần mềm.
3. Vào tab **⚙️ Cài đặt** → dán key 9router + key YouTube → **Lưu cài đặt**. Hai đèn xanh trên góc phải là xong.

## Quy trình 4 bước (tab "Tiêu đề")
1. **Phân tích DNA kênh** — dán link kênh đối thủ → rút *khuôn tiêu đề* (độ dài, tử huyệt, giọng điệu, khung xương, **từ khóa chiến thắng của kênh**).
2. **Quét ảnh thumb** — dán link kênh (khuyên dùng, tự lấy ~20 thumbnail nhiều view) hoặc tải ảnh lên → *DNA thumbnail* (font, bố cục, màu, nhân vật cố định...).
3. **Quét từ khóa → tái tạo** — nhập từ khóa, chọn mốc thời gian (7 ngày … 3 năm, hoặc Trend 48h), loại video, ngôn ngữ → tool tìm video nhiều view và tạo tiêu đề mới theo khuôn. Từ khóa bạn gõ là **từ khóa chính**: tiêu đề mới luôn chứa nó trong 50 ký tự đầu.
4. **Tích chọn tiêu đề → "🖼️ Làm thumb cả loạt"** — tool **bóc tách từng tiêu đề theo công thức** (vấn đề · khoảng trống tò mò · bối cảnh · tử huyệt → suy ra chủ thể · hành động · cảm xúc · thế giới cảnh) để bạn **xem và sửa**, rồi mới **sinh prompt** cho cả loạt. Cảnh luôn **bám nội dung tiêu đề**; kênh chỉ giữ phong cách vẽ, màu, bố cục, font và nhân vật cố định. Kết quả copy / tải `.txt` / gửi Google Sheet.

🎨 **Tái tạo thumbnail đối thủ theo DNA của bạn**: bảng kết quả có cột *Thumbnail*; bấm **"Tái tạo theo DNA"** dưới ảnh (hoặc tick *Lấy ý tưởng từ thumbnail đối thủ* khi làm cả loạt) → AI nhìn ảnh, lấy **bố cục + ý tưởng** và điền sẵn bóc tách cho tiêu đề mới (ô *Bố cục thumbnail đối thủ* sửa được); ảnh vẽ lại theo bố cục đó nhưng nội dung theo từ khóa/tiêu đề mới, còn phong cách/màu/font/nhân vật theo DNA của bạn. Không chép chữ/nhân vật/logo của đối thủ. Các ô bóc tách luôn là tiếng Việt có dấu.

Ngoài ra: **Viết lại tiêu đề** (dán tiêu đề hoặc link video bất kỳ, có ô *Từ khóa chính* tùy chọn) và **Lịch sử tiêu đề** (tự lưu, tìm lại được).

💡 Khuôn tiêu đề và DNA thumbnail là 2 kho **độc lập** — bạn có thể lấy tiêu đề theo kênh A và thumbnail theo kênh B cho cùng một ngách.

## Tính năng đáng chú ý
- **Ép từ khóa**: mỗi tiêu đề mới có dòng 🔑 (từ khóa chính / từ khóa kênh / từ khóa gốc giữ lại) kèm ✅ đủ hoặc ⚠️ thiếu; nút **🔄 Tạo lại** đổi sang khung xương khác.
- **Nhiều ngôn ngữ**: Việt, English, 中文, 日本語, 한국어, ไทย, Español. Có bản dịch tiếng Việt cho cả tiêu đề gốc lẫn tiêu đề mới.
- **Google Sheet**: ⚙️ Cài đặt → *Google Sheet* → làm theo hướng dẫn (có sẵn code để bấm Copy). Prompt thumbnail tự điền **nối tiếp xuống cuối bảng**, không ghi đè.
- **2 model AI**: ⚙️ Cài đặt → *Model Phân tích & Nhìn ảnh* (nên là Gemini) và *Model Sáng tạo* (tiêu đề & prompt). Mặc định đã chọn sẵn.
- **Cập nhật**: khi có bản mới, chỉ cần **F5** trình duyệt.

## Dữ liệu riêng của bạn (đừng gửi cho người khác)
`config.json` (chứa key), `profiles.json`, `dna_profiles.json`, `used.json`, `seen.json`, `title_history.json` — tự tạo trong thư mục phần mềm.

## Lưu ý quota YouTube
Mặc định ~10.000 điểm/ngày. Mỗi lần quét từ khóa, phân tích kênh hoặc quét ảnh thumb từ link kênh tốn ~100–120 điểm (tải ảnh lên thì không tốn). Với vài lượt mỗi ngày là thoải mái.

Xem thêm: `HUONG DAN SU DUNG.txt` (hướng dẫn từng bước + xử lý sự cố).
