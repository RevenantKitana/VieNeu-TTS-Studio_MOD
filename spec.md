# 📄 ĐẶC TẢ KỸ THUẬT & THIẾT KẾ UX: BATCH STUDIO & THƯ VIỆN DỰ ÁN (VIENEU-TTS)

---

## 1. TỔNG QUAN
Tài liệu này chuẩn hóa yêu cầu và giải pháp kỹ thuật cho 2 phân hệ mở rộng trên nền tảng **VieNeu-TTS**:
1. **📦 Batch Studio (Tạo Audio theo Dự án / Phân đoạn):** Hỗ trợ tạo audio cho các kịch bản dài, chia tách thành nhiều tệp `.wav` theo thẻ phân đoạn (block), hỗ trợ tiếp tục tiến trình khi gián đoạn (Resume / Skip Existing), kháng lỗi từng câu và tự động xuất siêu dữ liệu (metadata timeline).
2. **📂 Audio Library & Merging Engine (Thư viện Dự án & Bộ nối âm thanh):** Quản lý lịch sử dự án theo thư mục, giao diện Master-Detail (danh sách dự án $\rightarrow$ bảng chi tiết câu thoại), trình phát nghe lại, mở thư mục trên File Explorer, xuất gói `.zip` và công cụ nối ghép tệp tổng (`_FULL_MERGED`) đa định dạng qua FFmpeg - cdn link tải https://cdn.mio.io.vn/ffmpeg.exe lưu ngay trong dự án

---

## 2. CÚ PHÁP ĐẦU VÀO & PHÂN TÍCH VĂN BẢN (INPUT PARSING)

### 2.1. Phân biệt Thẻ Phân đoạn (Block Tag) và Thẻ Cảm xúc (Emotion Tag)
Để **hoàn toàn tương thích** và không xung đột với các thẻ biểu cảm có sẵn của VieNeu-TTS v3 Turbo (`[cười]`, `[hắng giọng]`, `[thở dài]`):

* **Cú pháp Thẻ Phân đoạn:**
  * `[#Tên_Đoạn]` hoặc `[Block: Tên_Đoạn]`
* **Quy tắc Regex Parser:**
  ```python
  import re

  # Nhận diện thẻ phân đoạn nhưng bỏ qua các tag cảm xúc có sẵn của v3 Turbo
  BLOCK_PATTERN = re.compile(
      r'\[(?!cười|thở dài|hắng giọng)(?:#|Block:\s*)?([^\]]+)\]',
      re.IGNORECASE
  )
  ```

### 2.2. Ký hiệu Bỏ qua Thủ công (Manual Skip)
* Để bỏ qua không render lại một block đã hoàn thành:
  * Thêm tiền tố `#`, `!`, `//`, hoặc `skip:` trước thẻ:
  ```text
  ![#Đoạn 2] Đoạn này sẽ bị bỏ qua không tạo audio.
  [skip: #Đoạn 3] Đoạn này cũng được bỏ qua.
  ```

### 2.3. Quy tắc Gom dòng & Xử lý Ngoại lệ
1. **Gom nhiều dòng:** Tất cả các dòng văn bản nằm bên dưới một thẻ phân đoạn (dù có nhiều dấu xuống dòng `Enter`) đều được gộp chung vào cùng một tệp âm thanh của đoạn đó.
2. **Phần mở đầu không có thẻ:** Nếu có nội dung văn bản đứng trước thẻ phân đoạn đầu tiên, hệ thống sẽ tự động gộp vào đầu của đoạn thứ nhất (không tạo file riêng).
3. **Văn bản không có thẻ nào:** Toàn bộ văn bản được gán nhãn mặc định là `[#Đoạn 1]` (sinh 1 file duy nhất).

---

## 3. CẤU TRÚC LƯU TRỮ & QUẢN LÝ DỰ ÁN (PROJECT STRUCTURE)

### 3.1. Quy tắc Đặt tên Thư mục Dự án
* Giao diện cung cấp ô: `📁 Tên dự án / Thư mục` (Ví dụ: `sach_noi_chuong_1`).
* **Tự động sinh (Fallback):** Nếu để trống, hệ thống tự động sinh tên theo định dạng thời gian: `batch_YYYYMMDD_HHMMSS`.

### 3.2. Cấu trúc Thư mục trên Đĩa
Tất cả các dự án được lưu trữ tập trung tại thư mục `outputs/projects/`:
```text
VieNeu-TTS/
└── outputs/
    └── projects/
        └── sach_noi_chuong_1/
            ├── sach_noi_chuong_1_01.wav          # Audio phân đoạn 1
            ├── sach_noi_chuong_1_02.wav          # Audio phân đoạn 2
            ├── sach_noi_chuong_1_mapping.txt     # Danh sách mapping timeline dạng text
            ├── info.json                         # Toàn bộ metadata timeline & trạng thái
            └── sach_noi_chuong_1_FULL_MERGED.mp3 # (Tùy chọn) File gộp hoàn chỉnh
```

### 3.3. Đặc tả Tệp Metadata (`info.json`)
```json
{
  "project_name": "sach_noi_chuong_1",
  "created_at": "2026-09-17 21:50:00",
  "model_backbone": "VieNeu-TTS-v3-Turbo",
  "voice": "Trúc Ly",
  "total_items": 2,
  "total_duration_sec": 8.5,
  "total_duration_formatted": "00:00:08.500",
  "items": [
    {
      "index": 1,
      "tag": "Đoạn 1",
      "file_name": "sach_noi_chuong_1_01.wav",
      "text": "Về miền Tây không chỉ để ngắm nhìn sông nước hữu tình... [cười]",
      "start_sec": 0.0,
      "end_sec": 4.2,
      "duration_sec": 4.2,
      "start_timestamp": "00:00:00.000",
      "end_timestamp": "00:00:04.200",
      "status": "SUCCESS"
    },
    {
      "index": 2,
      "tag": "Đoạn 2",
      "file_name": "sach_noi_chuong_1_02.wav",
      "text": "Hà Nội những ngày vào thu mang một vẻ đẹp trầm mặc...",
      "start_sec": 4.2,
      "end_sec": 8.5,
      "duration_sec": 4.3,
      "start_timestamp": "00:00:04.200",
      "end_timestamp": "00:00:08.500",
      "status": "SUCCESS"
    }
  ]
}
```

### 3.4. Đặc tả Tệp Mapping Timeline (`<tên_dự_án>_mapping.txt`)
```text
[sach_noi_chuong_1_01.wav] [00:00:00.000 -> 00:00:04.200] [Đoạn 1]
[sach_noi_chuong_1_02.wav] [00:00:04.200 -> 00:00:08.500] [Đoạn 2]
```

---

## 4. CƠ CHẾ CHỐNG SẬP & TIẾP TỤC TIẾN TRÌNH (RESILIENCE & RESUME)

1. **Chế độ xử lý tệp trùng (Existing Files Action):**
   * 🔄 **Ghi đè tất cả (`Overwrite All`):** Render lại từ đầu toàn bộ các đoạn trong kịch bản.
   * ⚡ **Bỏ qua file đã có / Chạy tiếp (`Resume / Skip Existing`):** Quét thư mục dự án, nếu đoạn nào đã có tệp `.wav` hợp lệ thì tự động nạp độ dài và bỏ qua, chỉ render tiếp các đoạn còn thiếu (giúp tiếp tục công việc khi rớt mạng, mất điện hoặc bấm Dừng giữa chừng).
2. **Kháng lỗi từng câu (Fault Tolerance):**
   * Quá trình sinh giọng từng câu được bọc riêng biệt trong khối `try...except`.
   * Nếu 1 câu bị lỗi (ký tự lạ, lỗi engine...), hệ thống ghi nhận trạng thái `"status": "FAILED"` vào `info.json`, **không làm dừng toàn bộ batch** mà tiếp tục render các câu kế tiếp.
3. **Nút Dừng mềm (Graceful Stop):**
   * Khi nhấn `⏹️ Dừng`, hệ thống hoàn tất lưu file audio của câu đang chạy dở, cập nhật `info.json` đến thời điểm hiện tại và dừng an toàn.

---

## 5. THIẾT KẾ GIAO DIỆN NGƯỜI DÙNG (UX/UI SPECIFICATION)

Giao diện bổ sung **2 Tab chuyên biệt** trong `apps/gradio_main.py`:

### 5.1. Tab 1: 📦 Batch Studio
```text
+-----------------------------------------------------------------------------------------+
| [Tên dự án]: [sach_noi_chuong_1         ]  [Giọng đọc]: [⭐ Trúc Ly           ▼]       |
| [Xử lý file cũ]: (•) Resume (Bỏ qua đã có)  ( ) Ghi đè toàn bộ                           |
|-----------------------------------------------------------------------------------------|
| Thanh công cụ nhanh: [+ Chèn Thẻ Đoạn]  [🎭 Chèn [cười]]  [🎭 Chèn [thở dài]]           |
|-----------------------------------------------------------------------------------------|
| [Khung soạn thảo kịch bản Multi-block]                                                 |
| [#Đoạn 1] Đây là nội dung đoạn thứ nhất... [cười] rất vui!                              |
|                                                                                         |
| [#Đoạn 2] Đây là nội dung đoạn thứ hai...                                              |
|-----------------------------------------------------------------------------------------|
| [⚡ Tự động nối file sau khi tạo]  [Định dạng xuất nối]: [MP3 (320 kbps) ▼]             |
| [Khoảng lặng giữa các đoạn]: [===o=== 0.5s]                                             |
| [ 🎵 Bắt đầu Batch ]   [ ⏹️ Dừng ]                                                      |
|-----------------------------------------------------------------------------------------|
| Tiến trình: [=====================>        ] 60% (Đang xử lý: Đoạn 3/5 | Còn lại ~20s)   |
+-----------------------------------------------------------------------------------------+
```

### 5.2. Tab 2: 📂 Thư viện Dự án (Audio Library & Viewer)
```text
+-----------------------------------------------------------------------------------------+
| [Chọn Dự án]: [sach_noi_chuong_1 (5 câu - 48kHz - 17/09/2026)                       ▼]  |
| [ 🔄 Làm mới danh sách ]  [ 📂 Mở thư mục trên máy ]  [ 📦 Tải trọn gói .ZIP ]          |
|-----------------------------------------------------------------------------------------|
| BẢNG DANH SÁCH CHI TIẾT CÂU THOẠI:                                                     |
| +----+-------------+------------+----------+-----------------------------+------------+ |
| | STT| Thẻ / File  | Thời lượng | Mốc Time | Lời thoại xem trước         | Thao tác   | |
| +----+-------------+------------+----------+-----------------------------+------------+ |
| | 01 | Đoạn 1      | 4.2s       | 00:00.00 | Về miền Tây không chỉ...    | [▶️ Nghe]  | |
| | 02 | Đoạn 2      | 4.3s       | 00:04.20 | Hà Nội những ngày vào thu...| [▶️ Nghe]  | |
| +----+-------------+------------+----------+-----------------------------+------------+ |
|                                                                                         |
| [TRÌNH PHÁT AUDIO CHÍNH - PLAYER] ----------------------------------------------------- |
|  ▶ [========================================] 04:25 / 08:50                             |
|                                                                                         |
| KHU VỰC NỐI TỆP (MERGE AUDIO):                                                          |
| Định dạng: [MP3 (320kbps) ▼]  Khoảng lặng: [0.5s]  [ 🔗 Nối / Xuất tệp Full ]           |
| Tệp gộp: [sach_noi_chuong_1_FULL_MERGED.mp3] -> [ 📥 Tải xuống tệp gộp ]                |
+-----------------------------------------------------------------------------------------+
```

---

## 6. ĐẶC TẢ BỘ NỐI TỆP ÂM THANH (AUDIO MERGING & EXPORT ENGINE)

### 6.1. Nguyên tắc Ghép & Lọc Tệp (Filtering Rules)
1. **Lọc file hợp lệ:** Trình nối quét thư mục dự án và chỉ nhận các tệp phân đoạn dạng `*_\d+.wav`.
2. **Chống lặp vô hạn:** Tự động loại trừ các tệp có đuôi `_FULL_MERGED.*` hoặc `_merged.*`.
3. **Chèn khoảng lặng (Silence Gap):** Tự động sinh một đoạn silence PCM theo thông số người dùng cài đặt (mặc định: `0.3s - 0.5s`) giữa 2 phân đoạn liên tiếp.
4. **Không nối (Skip Merge):** Nếu thư mục chỉ có 1 tệp duy nhất, hệ thống sẽ bỏ qua bước nối để tiết kiệm tài nguyên.

### 6.2. Danh sách Định dạng Xuất qua FFmpeg
Hệ thống tận dụng FFmpeg (local) để xuất các chuẩn định dạng:
1. `WAV (Lossless PCM 16-bit / 24-bit)` - `.wav`
2. `MP3 (320 kbps)` - `.mp3` (Chất lượng cao)
3. `MP3 (192 kbps)` - `.mp3` (Tiêu chuẩn phổ thông)
4. `MP3 (128 kbps)` - `.mp3` (Tiết kiệm dung lượng)
5. `FLAC (Lossless Compressed)` - `.flac`
6. `M4A / AAC (256 kbps)` - `.m4a` (Chuẩn Apple Podcast)
7. `OGG / Vorbis (192 kbps)` - `.ogg`

---

## 7. CẤU TRÚC MODULE TRIỂN KHAI TRONG CODEBASE

| Tệp / Module | Vai trò & Trách nhiệm |
| :--- | :--- |
| **`apps/batch_speech.py`** *(Mới)* | - Parser bóc tách kịch bản theo regex `[#Tag]` (loại trừ tag cảm xúc).<br>- Engine quản lý render batch, checkpoint resume, tạo `info.json` & `mapping.txt`.<br>- Module nối ghép đa định dạng FFmpeg (`merge_project_audio`). |
| **`apps/audio_library.py`** *(Mới)* | - Scanner quét thư mục `outputs/projects/`.<br>- Xử lý tải gói `.zip` dự án (`zipfile`).<br>- Mở thư mục trực tiếp trên HĐH (`os.startfile` trên Windows / `open` trên macOS). |
| **`apps/gradio_main.py`** | - Tích hợp 2 Tab giao diện: `📦 Batch Studio` và `📂 Thư viện Dự án`.<br>- Kết nối các Event Handler và State giữa các tab. |
| **`apps/ui_constants.py`** | - Bổ sung CSS làm đẹp cho bảng Dataframe, khung soạn thảo kịch bản batch và thanh tiến trình. |
