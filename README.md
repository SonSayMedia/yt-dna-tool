# YT DNA Tool (localhost)

Phần mềm chạy trên máy cá nhân: **phân tích kênh → rút khuôn tiêu đề → quét từ khóa → tái tạo tiêu đề** theo khuôn kênh follow. (Tool 2: DNA ảnh + SRT→prompt sẽ bổ sung ở bước sau.)

## Cần cài trước
1. **Python 3.10+** — tải tại https://www.python.org/downloads/ (khi cài nhớ tick "Add Python to PATH").
2. **ffmpeg** (chỉ cần cho Tool 2 sau này) — tải tại https://www.gyan.dev/ffmpeg/builds/ và thêm vào PATH.

## Cài đặt & chạy (Windows)
1. Mở thư mục `yt-dna-tool`.
2. Copy `config.example.json` → đổi tên thành `config.json`, điền 4 thông tin:
   - `llm_base_url`: endpoint của 9router (thường kết thúc `/v1`)
   - `llm_api_key`: khóa 9router
   - `llm_model`: tên model Gemini Flash
   - `llm_vision_model`: model có "mắt" (để trống = dùng chung `llm_model`)
   - `youtube_api_key`: khóa YouTube Data API v3
3. Nhấp đúp **`run.bat`** (lần đầu sẽ tự tạo môi trường ảo + cài thư viện).
4. Mở trình duyệt: **http://127.0.0.1:5000**

## Đã có (Khối A, B, C, D)
- **① Phân tích kênh**: dán link kênh → lấy 20 video top view → rút "khuôn tiêu đề" (Title DNA), lưu lại để tái dùng.
- **② Quét từ khóa**: nhập từ khóa → chọn mốc thời gian (3 tháng–3 năm) hoặc **Trend 48h** → xếp theo tổng view → bóc tách 3 thành phần → **tái tạo tiêu đề** theo khuôn đã chọn, ngôn ngữ tùy chọn.
- **③ DNA ảnh** (2 cách nạp):
  - **Tải ảnh lên** thumbnail + ảnh nội dung, hoặc
  - **Dán link video** → tool tự tải bản nhẹ (yt-dlp) + cắt khung hình (ffmpeg) + lấy thumbnail qua API.
  - → Gemini vision → DNA thumbnail + DNA ảnh nội dung (kèm prompt tiếng Anh gắn sẵn), lưu lại.
- **④ SRT → Prompt**: file SRT (tên file = tiêu đề) + chọn DNA → 1 prompt thumbnail (hiện trên màn hình) + N prompt ảnh (cắt cảnh theo nghĩa ≤6s, tiếng Anh) → tải `.txt` đánh số.

## Lưu ý quota
YouTube API mặc định ~10.000 điểm/ngày. Mỗi lần quét từ khóa hoặc phân tích kênh tốn ~100–120 điểm. Với 2–3 từ khóa/ngày là rất thoải mái.
