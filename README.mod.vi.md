# 🦜 VieNeu-TTS Studio (Bản Mod Mở Rộng - Modded by Khánh)

> **Phiên bản mở rộng & tối ưu hóa UX/UI cho nền tảng Text-to-Speech tiếng Việt VieNeu-TTS.**  
> ⚡ **Tác giả bản Mod:** [Khánh (k.mio.io.vn)](https://k.mio.io.vn)  
> 🌟 **Dự án gốc & Mô hình AI:** [Phạm Nguyễn Ngọc Bảo (pnnbao97/VieNeu-TTS)](https://github.com/pnnbao97/VieNeu-TTS)

---

## 🌟 TỔNG QUAN VỀ BẢN MOD

Bản mod này nâng cấp **VieNeu-TTS** từ một công cụ sinh giọng nói câu đơn lẻ thành một **Studio Sản xuất Âm thanh Hoàn chỉnh (Production Studio)** với khả năng xử lý kịch bản dài nhiều phân đoạn, quản lý lịch sử dự án, tự động nối ghép âm thanh đa định dạng và tự động hóa toàn bộ quy trình khởi động.

---

## ✨ CÁC TÍNH NĂNG MỚI ĐƯỢC BỔ SUNG

### 1. 📦 Batch Studio (Tạo Audio theo Dự án & Phân đoạn)
- **Cú pháp Multi-block thông minh:** Hỗ trợ phân đoạn kịch bản dạng `[#Tên_Đoạn]` hoặc `[Block: Tên_Đoạn]`.
- **Bảo toàn Thẻ Cảm xúc:** Hoàn toàn tương thích và không xung đột với các tag cảm xúc có sẵn của v3 Turbo (`[cười]`, `[thở dài]`, `[hắng giọng]`).
- **Bỏ qua Thủ công (Manual Skip):** Thêm tiền tố `#`, `!`, `//`, hoặc `skip:` trước thẻ đoạn để bỏ qua không render lại (ví dụ: `![#Đoạn 2]`, `[skip: #Đoạn 3]`).
- **Gom dòng & Xử lý Ngoại lệ:** Gom toàn bộ các dòng văn bản (kể cả nhiều dấu xuống dòng `Enter`) dưới mỗi thẻ vào cùng 1 đoạn audio; tự động xử lý phần mở đầu chưa có thẻ.
- **Tiếp tục tiến trình (Resume / Skip Existing):** Tự động phát hiện các file `.wav` đã render thành công và bỏ qua, chỉ tạo tiếp các đoạn còn thiếu khi tiến trình bị gián đoạn.
- **Kháng lỗi từng câu (Fault Tolerance):** Khối `try...except` độc lập cho từng phân đoạn; nếu 1 đoạn gặp lỗi, hệ thống ghi nhận trạng thái `FAILED` vào metadata và tiếp tục xử lý các đoạn kế tiếp mà không làm sập toàn bộ batch.
- **Tự động xuất Siêu dữ liệu & Mapping:** Tự động tạo tệp `info.json` (thời lượng, mốc timeline `HH:MM:SS.mmm`, trạng thái) và `<tên_dự_án>_mapping.txt`.

---

### 2. 📂 Thư viện Dự án & Bộ nối âm thanh (Audio Library & Merging Engine)
- **Quản lý Master-Detail:** Quét toàn bộ thư mục `outputs/projects/` và hiển thị danh sách dự án kèm bảng câu thoại chi tiết.
- **Trình phát Nghe lại Trực quan:** Nhấp vào từng dòng trên bảng để nghe lại trực tiếp phân đoạn đó trên trình phát audio.
- **Thao tác 1-Click:**
  - 📂 **Mở thư mục trên máy:** Mở trực tiếp thư mục dự án trên Windows File Explorer / macOS Finder.
  - 📦 **Tải gói .ZIP:** Tự động nén toàn bộ âm thanh, metadata và file gộp thành file `.zip` tải về máy.
- **Bộ nối ghép âm thanh FFmpeg đa định dạng:**
  - Tự động quét các tệp `*_\d+.wav`, loại trừ các file gộp cũ để chống lặp.
  - Chèn khoảng lặng tự động (`silence_gap`) giữa các đoạn theo cài đặt người dùng (mặc định 0.5s).
  - Hỗ trợ xuất các chuẩn định dạng:
    1. `WAV (Lossless PCM)` - `.wav`
    2. `MP3 (320 kbps)` - `.mp3` (Chất lượng cao)
    3. `MP3 (192 kbps)` - `.mp3` (Chuẩn phổ thông)
    4. `MP3 (128 kbps)` - `.mp3` (Tiết kiệm dung lượng)
    5. `FLAC (Lossless Compressed)` - `.flac`
    6. `M4A / AAC (256 kbps)` - `.m4a` (Chuẩn Apple Podcast)
    7. `OGG / Vorbis (192 kbps)` - `.ogg`

---

### 3. ⚡ Tự Động Hóa & Khởi Động Siêu Nhanh
- **Tự động nạp Model (Auto-load on startup):** Ngay khi mở trang WebUI, hệ thống tự động kiểm tra local cache và nạp sẵn model `VieNeu-TTS-v3-Turbo` (48kHz) cùng toàn bộ 25 giọng đọc mẫu. Người dùng vào là có thể **tạo giọng ngay lập tức** mà không cần ấn nút "Tải Model".
- **Tiền kiểm tra Tài nguyên (`apps/preflight.py`):**
  - Tự động kiểm tra `ffmpeg.exe` (tự tải từ CDN `https://cdn.mio.io.vn/ffmpeg.exe` về thư mục gốc nếu chưa có).
  - Tự động kiểm tra và tải trước model weights về `models_cache/`.
- **Launcher Scripts 1-Click:**
  - `start_app.bat`: Chạy kiểm tra tài nguyên, tự động mở trình duyệt web và khởi động server.
  - `start_portable.bat`: Chế độ Portable 100% không làm ảnh hưởng môi trường bên ngoài.

---

### 4. 🎨 Cải Tiến Giao Diện Người Dùng (UI/UX Redesign)
- **Header Compact Navbar:** Tinh gọn chiều cao Viewport hơn 60%, hiển thị tiêu đề gradient kèm Badge `⚡ Mod by Khánh [k.mio.io.vn]` và icon pills (`🤗 Models`, `🐙 GitHub`, `👤 Ngọc Bảo`, `💬 Discord`).
- **Phân tách Trải nghiệm Người dùng:**
  - **Dành cho Người dùng Phổ thông:** Giao diện trực quan, loại bỏ các cảnh báo kỹ thuật/dòng lệnh rườm rà, hướng dẫn thu âm clone giọng dễ hiểu (3–5s, không nhạc nền, bật lọc ồn).
  - **Tab `🛠️ Dành cho Developer`:** Tập hợp riêng toàn bộ tài liệu kỹ thuật: Code mẫu Python SDK/API (`Vieneu.infer()`, `clone_and_infer()`), tối ưu GPU CUDA (`uv sync --group gpu`), kiến trúc v3-Turbo vs v3-Nano, và hướng dẫn huấn luyện LoRA (`finetune/README.md`).

---

## 📁 CẤU TRÚC THƯ MỤC DỰ ÁN

Tất cả các dự án tạo ra từ Batch Studio được lưu trữ tại `outputs/projects/`:
```text
VieNeu-TTS/
├── ffmpeg.exe                           # Tự động tải từ CDN nếu thiếu
├── models_cache/                        # Thư mục chứa model weights (Portable)
├── start_app.bat                        # Script khởi động tự động 1-click
├── outputs/
│   └── projects/
│       └── sach_noi_chuong_1/
│           ├── sach_noi_chuong_1_01.wav          # Audio phân đoạn 1
│           ├── sach_noi_chuong_1_02.wav          # Audio phân đoạn 2
│           ├── sach_noi_chuong_1_mapping.txt     # Danh sách mapping timeline
│           ├── info.json                         # Metadata chi tiết & trạng thái
│           └── sach_noi_chuong_1_FULL_MERGED.mp3 # File âm thanh gộp hoàn chỉnh
```

---

## 🚀 HƯỚNG DẪN CÀI ĐẶT & KHỞI CHẠY

### Cách 1: Khởi động nhanh trên Windows (Khuyên dùng)
Nhấp đúp chuột vào file:
```cmd
start_app.bat
```
*(Script sẽ tự động kiểm tra FFmpeg, nạp cache model, mở trình duyệt tại `http://127.0.0.1:7860` và khởi chạy WebUI)*

---

### Cách 2: Chạy thủ công qua Command Line

1. **Cài đặt môi trường với `uv`:**
   ```bash
   # Dành cho máy CPU:
   uv sync

   # Dành cho máy có GPU NVIDIA (CUDA):
   uv sync --group gpu
   ```

2. **Khởi chạy ứng dụng Web:**
   ```bash
   uv run python apps/gradio_main.py
   ```

---

## 📝 VÍ DỤ CÚ PHÁP KỊCH BẢN BATCH STUDIO

Bạn có thể dán kịch bản sau vào Tab **📦 Batch Studio** để thử nghiệm:

```text
[#Đoạn 1] Về miền Tây không chỉ để ngắm nhìn sông nước hữu tình, mà còn để lắng nghe những câu hò điệu lý ngọt ngào.
Nơi đây, con người luôn đôn hậu và mến khách. [cười] Bạn đã từng về miền Tây chưa?

[#Đoạn 2] Hà Nội những ngày vào thu mang một vẻ đẹp trầm mặc và đầy thi vị. [thở dài]
Gió heo may thổi nhẹ qua từng tán cây xà cừ cổ thụ, đưa hương hoa sữa thoang thoảng khắp các ngõ phố.

[#Đoạn 3] Chúc các bạn có những giây phút trải nghiệm tuyệt vời cùng VieNeu-TTS Batch Studio!
```

---

## 🤝 GHI CÔNG & BẢN QUYỀN

- **Mô hình AI & Mã nguồn gốc:** [Phạm Nguyễn Ngọc Bảo](https://github.com/pnnbao97/VieNeu-TTS)  
- **Bản Mod Studio, Batch Engine & UI/UX:** [Khánh (k.mio.io.vn)](https://k.mio.io.vn)  
- **Giấy phép:** Apache-2.0 License
