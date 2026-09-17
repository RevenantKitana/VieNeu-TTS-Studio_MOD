import gradio as gr

theme = gr.themes.Soft(
    primary_hue="indigo",
    secondary_hue="cyan",
    neutral_hue="slate",
    font=[gr.themes.GoogleFont('Inter'), 'ui-sans-serif', 'system-ui'],
).set(
    button_primary_background_fill="linear-gradient(90deg, #6366f1 0%, #0ea5e9 100%)",
    button_primary_background_fill_hover="linear-gradient(90deg, #4f46e5 0%, #0284c7 100%)",
)

css = """
.container { max-width: 1400px; margin: auto; }
/* Compact control rows (Voice Cloning → saved voices): caption above, one-line
   controls vertically centred so a small button sits level with the dropdown. */
.field-caption { margin: 4px 0 -6px 0; }
.field-caption p { margin: 0; font-size: 0.85rem; color: var(--block-title-text-color); }
.inline-row { align-items: center; }
.header-box {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
    margin-bottom: 14px;
    padding: 10px 18px;
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    border-radius: 12px;
    color: white !important;
    border: 1px solid rgba(255, 255, 255, 0.08);
}
.header-left {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
}
.header-title {
    font-size: 1.35rem;
    font-weight: 800;
    margin: 0;
    line-height: 1.2;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    color: white !important;
}
.gradient-text {
    background: -webkit-linear-gradient(45deg, #60A5FA, #22D3EE);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.header-icon {
    color: white;
}
.mod-badge {
    background: linear-gradient(135deg, rgba(236, 72, 153, 0.2), rgba(168, 85, 247, 0.25));
    border: 1px solid rgba(236, 72, 153, 0.4);
    color: #f472b6 !important;
    padding: 3px 10px;
    border-radius: 14px;
    font-size: 0.78rem;
    font-weight: 600;
    text-decoration: none;
    transition: all 0.2s ease;
    display: inline-flex;
    align-items: center;
    gap: 4px;
}
.mod-badge:hover {
    background: linear-gradient(135deg, rgba(236, 72, 153, 0.35), rgba(168, 85, 247, 0.4));
    color: #fb7185 !important;
    border-color: #f472b6;
    transform: translateY(-1px);
}
.header-links {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
}
.header-link-pill {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 4px 10px;
    background: rgba(255, 255, 255, 0.07);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    color: #94a3b8 !important;
    font-size: 0.8rem;
    font-weight: 500;
    text-decoration: none;
    transition: all 0.15s ease;
}
.header-link-pill:hover {
    background: rgba(255, 255, 255, 0.15);
    color: #38bdf8 !important;
    border-color: rgba(56, 189, 248, 0.4);
}
.status-box {
    font-weight: 500;
    border: 1px solid rgba(99, 102, 241, 0.1);
    background: rgba(99, 102, 241, 0.03);
    border-radius: 8px;
}
.status-box textarea {
    text-align: center;
    font-family: inherit;
}
.estimate-box {
    font-weight: 500;
    border: 1px solid rgba(99, 102, 241, 0.1);
    background: rgba(99, 102, 241, 0.03);
    border-radius: 8px;
}
.estimate-box textarea {
    text-align: center;
    font-family: inherit;
}
.warning-banner {
    background-color: #fffbeb;
    border: 1px solid #fef3c7;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 20px;
}
.warning-banner-title {
    color: #92400e;
    font-weight: 700;
    font-size: 1.1rem;
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
}
.warning-banner-grid {
    display: flex;
    gap: 15px;
    flex-wrap: wrap;
}
.warning-banner-item {
    flex: 1;
    min-width: 240px;
    background: #fef3c7;
    padding: 12px;
    border-radius: 8px;
    border: 1px solid #fde68a;
}
.warning-banner-item strong {
    color: #b45309;
    display: block;
    margin-bottom: 4px;
    font-size: 0.95rem;
}
.warning-banner-content {
    color: #78350f;
    font-size: 0.9rem;
    line-height: 1.5;
}
.warning-banner-content b {
    color: #451a03;
    background: rgba(251, 191, 36, 0.2);
    padding: 1px 4px;
    border-radius: 4px;
}
.script-box textarea {
    font-family: 'Inter', sans-serif;
    line-height: 1.6;
}
.speaker-table {
    margin-top: 10px;
}
.batch-toolbar {
    display: flex !important;
    flex-direction: row !important;
    gap: 8px !important;
    margin-bottom: 8px !important;
    flex-wrap: wrap !important;
    align-items: center !important;
}
.batch-toolbar > div,
.batch-toolbar > button,
.batch-toolbar .gradio-button,
.batch-toolbar > div[class*="block"],
.batch-toolbar > div[class*="svelte"] {
    flex: 0 0 auto !important;
    width: auto !important;
    min-width: unset !important;
    max-width: fit-content !important;
}
.batch-toolbar button {
    border-radius: 6px !important;
    font-size: 0.85rem !important;
    padding: 6px 12px !important;
    white-space: nowrap !important;
    width: auto !important;
    min-width: unset !important;
    flex: 0 0 auto !important;
}
.batch-box textarea {
    font-family: 'Inter', ui-sans-serif, sans-serif;
    line-height: 1.6;
    font-size: 0.95rem;
}
.library-summary {
    background: rgba(99, 102, 241, 0.05);
    border: 1px solid rgba(99, 102, 241, 0.2);
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 12px;
}
.library-summary h3 {
    margin-top: 0;
    margin-bottom: 8px;
    color: var(--primary-500, #6366f1);
}
"""

head_html = """
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🦜</text></svg>">
"""

DEFAULT_TEXT_GPU = "Hà Nội, trái tim của Việt Nam, là một thành phố ngàn năm văn hiến với bề dày lịch sử và văn hóa độc đáo. Bước chân trên những con phố cổ kính quanh Hồ Hoàn Kiếm, du khách như được du hành ngược thời gian, chiêm ngưỡng kiến trúc Pháp cổ điển hòa quyện với nét kiến trúc truyền thống Việt Nam. Mỗi con phố trong khu phố cổ mang một tên gọi đặc trưng, phản ánh nghề thủ công truyền thống từng thịnh hành nơi đây như phố Hàng Bạc, Hàng Đào, Hàng Mã. Ẩm thực Hà Nội cũng là một điểm nhấn đặc biệt, từ tô phở nóng hổi buổi sáng, bún chả thơm lừng trưa hè, đến chè Thái ngọt ngào chiều thu. Những món ăn dân dã này đã trở thành biểu tượng của văn hóa ẩm thực Việt, được cả thế giới yêu mến. Người Hà Nội nổi tiếng với tính cách hiền hòa, lịch thiệp nhưng cũng rất cầu toàn trong từng chi tiết nhỏ, từ cách pha trà sen cho đến cách chọn hoa sen tây để thưởng trà."
DEFAULT_TEXT_TURBO = (
    "Trước đây, hệ thống điện chủ yếu sử dụng direct current, nhưng Tesla đã chứng minh rằng alternating current is more efficient for long-distance transmission. Nhờ đó, điện có thể được truyền đi xa hơn với ít tổn thất năng lượng hơn. Đây là một bước tiến cực kỳ quan trọng trong ngành điện.\n\n"
    "Một trong những phát minh nổi tiếng của ông là Tesla coil, một thiết bị có thể tạo ra điện áp rất cao và những tia sét nhân tạo. This device is still used today in demonstrations và trong một số ứng dụng nghiên cứu. Khi nhìn thấy những tia điện này, nhiều người cảm thấy vừa ấn tượng vừa hơi đáng sợ."
)

# v3 Turbo demo text — khoe giọng tự nhiên + tag cảm xúc [cười] (tính năng mới, thử nghiệm).
DEFAULT_TEXT_V3 = (
    "Xin chào mọi người! [hắng giọng] Như bạn đang nghe thấy đấy, tốc độ xử lý của mình cực kỳ nhanh và mượt mà, giúp phản hồi gần như ngay lập tức theo thời gian thực. Chính vì vậy, mình rất phù hợp để ứng dụng trực tiếp vào các hệ thống Chatbot thông minh, trợ lý ảo, hoặc làm tổng đài viên tự động cho các doanh nghiệp. Tiện lợi quá đúng không ạ? [cười] Hi vọng phiên bản nâng cấp v3 này sẽ mang lại trải nghiệm tuyệt vời cho dự án của bạn."
)

# Batch Studio multi-block demo texts
DEFAULT_BATCH_SCRIPT_SOLO = """[#Đoạn 1: Mở đầu câu chuyện]
Mùa thu Hà Nội luôn mang một vẻ đẹp rất riêng và lãng mạn. Những con phố rợp bóng cây xà cừ cổ thụ bỗng trở nên trầm mặc hơn khi từng đợt gió heo may se lạnh ùa về. [thở dài] Đi dạo trên đường Phan Đình Phùng vào một buổi sáng sớm, ta có thể cảm nhận được mùi hoa sữa thoang thoảng trong không khí.

[#Đoạn 2: Trải nghiệm công nghệ]
VieNeu-TTS Studio là giải pháp chuyển đổi văn bản thành giọng nói tiếng Việt chất lượng cao. Với công nghệ xử lý âm thanh 48kHz và hệ thống phân đoạn thông minh, bạn có thể dễ dàng tạo ra những cuốn sách nói hấp dẫn hoặc thuyết minh video chuyên nghiệp. [cười] Hãy cùng bắt đầu trải nghiệm ngay hôm nay!
"""

DEFAULT_BATCH_SCRIPT_MULTI = """[#Đoạn 1: Gặp gỡ ở quán cà phê]
(Người dẫn) Trời bắt đầu đổ cơn mưa rào, hai người bạn vội vã bước vào một quán cà phê nhỏ bên góc phố.
(Phương) [thở dài] Mưa to quá anh ơi, may mà chúng mình chạy vào kịp quán!
(Dũng) [cười] Ừ, hôm nay thời tiết bất ngờ thật đấy. À, em đã thử bản Mod VieNeu Studio của anh Khánh chưa?

[#Đoạn 2: Thảo luận về bản Mod của Khánh]
(Phương) Em vừa test xong anh ơi! Bản Mod của anh Khánh xịn xò thực sự, render đa vai từng đoạn 48kHz mượt mà lắm!
(Dũng) [cười] Công nhận anh Khánh mod đỉnh thật, giao diện vừa đẹp vừa tiện lợi. Chuẩn bị xuất bản thôi!
"""

DEFAULT_BATCH_SCRIPT = DEFAULT_BATCH_SCRIPT_SOLO

