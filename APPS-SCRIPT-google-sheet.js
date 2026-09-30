// ==========================================================================
//  CỔNG GOOGLE SHEET cho YT DNA Tool  —  dán vào Apps Script của Google Sheet
// --------------------------------------------------------------------------
//  Cách dùng (làm 1 lần):
//   1. Mở Google Sheet của bạn → menu "Tiện ích mở rộng" (Extensions) → "Apps Script".
//   2. Xoá hết code mẫu, dán TOÀN BỘ file này vào → bấm biểu tượng 💾 (Lưu).
//   3. Bấm "Triển khai" (Deploy) → "Bản triển khai mới" (New deployment).
//   4. Bánh răng ⚙ → chọn loại "Ứng dụng web" (Web app).
//        - Thực thi với tư cách: Chính tôi (Me)
//        - Ai có quyền truy cập: BẤT KỲ AI (Anyone)   ← QUAN TRỌNG
//   5. "Triển khai" → "Cho phép quyền truy cập" (Authorize) → chọn tài khoản → Cho phép.
//   6. Copy "URL ứng dụng web" (kết thúc bằng /exec) → dán vào YT DNA Tool:
//        Cài đặt → Google Sheet → ô link → Lưu link → Gửi thử 1 dòng.
//
//  Ghi vào các cột theo thứ tự:  STT | Tiêu đề tiếng Anh | Tiếng Việt | Link video | Prompt thumb
//  (STT tự tăng dựa trên STT của dòng cuối; các dòng mới thêm xuống dưới cùng.)
// ==========================================================================

function doPost(e) {
  var lock = LockService.getScriptLock();
  lock.waitLock(30000);
  try {
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    var rows = (JSON.parse(e.postData.contents).rows) || [];

    // STT tiếp theo = STT của dòng cuối + 1 (nếu ô A dòng cuối là số); nếu không, bắt đầu từ 1.
    var last = sheet.getLastRow();
    var stt = 0;
    if (last >= 1) {
      var v = sheet.getRange(last, 1).getValue();
      if (typeof v === 'number') stt = v;
    }

    rows.forEach(function (r) {
      stt++;
      sheet.appendRow([
        stt,
        r.title_en || '',
        r.title_vi || '',
        r.link_video || '',
        r.prompt_thumb || ''
      ]);
    });

    return ContentService
      .createTextOutput(JSON.stringify({ ok: true, added: rows.length }))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService
      .createTextOutput(JSON.stringify({ ok: false, error: String(err) }))
      .setMimeType(ContentService.MimeType.JSON);
  } finally {
    lock.releaseLock();
  }
}

// Cho phép mở URL bằng trình duyệt để kiểm tra nhanh (hiện chữ "OK").
function doGet() {
  return ContentService.createTextOutput('YT DNA Tool sheet gateway OK');
}
