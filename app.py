import inspect
import re

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ==========================================
# 1. CẤU HÌNH TRANG WEB
# ==========================================
st.set_page_config(
    page_title="Hệ Thống Quản Lý Điểm Sinh Viên",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="auto",  # "auto": trên điện thoại sidebar không phủ kín màn hình
)

# ==========================================
# 2. BẢNG MÀU PASTEL (dùng chung cho CSS, biểu đồ, bảng điểm)
# Muốn đổi màu chủ đạo: sửa các biến ở :root trong CSS và các hằng số bên dưới.
# Các màu chữ đã được chỉnh để đạt tương phản tối thiểu 4.5:1 (chuẩn WCAG AA).
# ==========================================
INK = "#2f4a60"        # Màu chữ chính
INK_SOFT = "#4f6d84"   # Màu chữ phụ (đã đậm hơn bản cũ để dễ đọc)
LINE = "#d4e6f3"       # Màu viền nhạt
BLUE, BLUE_D = "#8cc4ee", "#4a8fc4"
BLUE_TXT = "#3a79ad"   # Xanh dùng cho CHỮ nhỏ trên nền sáng
MINT, MINT_D = "#a8e0cb", "#2a7254"
PEACH, PEACH_D = "#f6c7b6", "#9a5640"
ROSE, ROSE_D = "#f4b6c0", "#9b4a5a"

GRADE_ORDER = ["Giỏi", "Khá", "Trung bình", "Yếu"]

# Màu cột / biểu đồ theo xếp loại
GRADE_FILL = {"Giỏi": BLUE, "Khá": MINT, "Trung bình": PEACH, "Yếu": ROSE}
# Màu viền cột (đậm hơn màu nền để cột pastel vẫn nổi trên nền trắng)
GRADE_EDGE = {"Giỏi": BLUE_D, "Khá": "#5fbf9a", "Trung bình": "#e8927c", "Yếu": "#d9798a"}

# Màu nền + màu chữ của badge / ô xếp loại
GRADE_BADGE = {
    "Giỏi": ("#d7eefc", "#2f6a95"),
    "Khá": ("#daf3e9", MINT_D),
    "Trung bình": ("#fde6dc", PEACH_D),
    "Yếu": ("#fbe1e5", ROSE_D),
}
GRADE_CLASS = {
    "Giỏi": "badge-gioi",
    "Khá": "badge-kha",
    "Trung bình": "badge-tb",
    "Yếu": "badge-yeu",
}

# Thông tin tác giả. MSSV chỉ hiện 4 số cuối vì trang web này công khai.
AUTHOR_NAME = "Trần Đăng Huy"
AUTHOR_ID_MASKED = "••••••••6543"
AUTHOR_CLASS = "AI87"
AUTHOR_SCHOOL = "ĐH Giao Thông Vận Tải"

# ==========================================
# 3. CSS: GIAO DIỆN PASTEL, KÍNH MỜ, CHUYỂN ĐỘNG NHẸ
# ==========================================
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@300;400;500;600;700&display=swap');

    /* Đăng ký biến số để tạo hiệu ứng đếm số tăng dần bằng CSS */
    @property --ci { syntax: '<integer>'; inherits: false; initial-value: 0; }
    @property --cd { syntax: '<integer>'; inherits: false; initial-value: 0; }

    :root {
        --bg: #eef6fc;
        --card: rgba(255, 255, 255, 0.82);
        --ink: #2f4a60;
        --ink-soft: #4f6d84;
        --line: #d4e6f3;
        --blue: #8cc4ee;
        --blue-d: #4a8fc4;
        --blue-txt: #3a79ad;
        --mint: #a8e0cb;
        --mint-d: #2a7254;
        --peach: #f6c7b6;
        --peach-d: #9a5640;
        --rose: #f4b6c0;
        --rose-d: #9b4a5a;
        --shadow: 0 10px 30px rgba(74, 143, 196, 0.14);
        --shadow-hover: 0 18px 38px rgba(74, 143, 196, 0.22);
        --ease: cubic-bezier(0.16, 1, 0.3, 1);
    }

    /* ---------- Nền và font chung ---------- */
    html, body, [class*="css"], .stApp {
        font-family: 'Be Vietnam Pro', 'Segoe UI', sans-serif;
        color: var(--ink);
    }
    [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(circle at 12% 8%, #dcecfa 0, transparent 42%),
            radial-gradient(circle at 88% 18%, #e3f5ee 0, transparent 38%),
            radial-gradient(circle at 60% 95%, #f3ecfa 0, transparent 40%),
            var(--bg);
    }
    [data-testid="stHeader"] { background: transparent; }
    .block-container { padding-top: 2rem; max-width: 1200px; }
    h1, h2, h3, h4, h5, h6, label, [data-testid="stWidgetLabel"] p {
        color: var(--ink) !important;
        font-weight: 600;
    }
    [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {
        color: var(--ink-soft) !important;
    }

    /* Chữ chỉ dành cho trình đọc màn hình */
    .sr-only {
        position: absolute;
        width: 1px; height: 1px;
        margin: -1px; padding: 0;
        overflow: hidden;
        clip: rect(0, 0, 0, 0);
        white-space: nowrap;
        border: 0;
    }

    /* ---------- Keyframes (chỉ chạy một lần khi vào trang) ---------- */
    @keyframes rise {
        from { opacity: 0; transform: translateY(14px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes grow { from { width: 0; } }
    @keyframes countI { from { --ci: 0; } }
    @keyframes countD { from { --cd: 0; } }

    /* ---------- Banner đầu trang ---------- */
    .hero {
        position: relative;
        overflow: hidden;
        border-radius: 24px;
        padding: 22px 28px;
        margin-bottom: 16px;
        background: linear-gradient(120deg, #cfe6f7, #dff3ea 55%, #e8e1f7);
        border: 1px solid rgba(255, 255, 255, 0.85);
        box-shadow: var(--shadow);
        animation: rise 0.7s var(--ease) both;
    }
    .hero-title {
        font-size: 1.9rem;
        font-weight: 700;
        line-height: 1.25;
        color: #24445e;
    }
    .hero-sub { margin-top: 4px; color: #46667d; font-size: 1rem; }

    /* ---------- Thẻ số liệu ---------- */
    .m-card {
        position: relative;
        overflow: hidden;
        background: var(--card);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.9);
        border-radius: 22px;
        padding: 18px 20px 16px 24px;
        box-shadow: var(--shadow);
        transition: transform 0.35s var(--ease), box-shadow 0.35s var(--ease);
        animation: rise 0.6s var(--ease) both;
        animation-delay: var(--d, 0s);
    }
    .m-card::before {
        content: "";
        position: absolute;
        left: 0; top: 0; bottom: 0;
        width: 6px;
        background: var(--accent);
    }
    .m-card:hover { transform: translateY(-4px); box-shadow: var(--shadow-hover); }
    .m-top { display: flex; align-items: center; gap: 10px; }
    .m-icon {
        width: 36px; height: 36px;
        border-radius: 12px;
        display: grid; place-items: center;
        background: var(--tint);
        font-size: 1.1rem;
    }
    .m-label { font-size: 0.9rem; color: var(--ink-soft); font-weight: 500; }
    .m-value { position: relative; font-size: 2.1rem; font-weight: 700; margin: 10px 0 2px; line-height: 1.1; color: var(--ink); }
    .m-sub { font-size: 0.9rem; color: var(--ink-soft); }

    /* Số đếm tăng dần: giá trị cuối đặt qua --ci (phần nguyên) và --cd (phần thập phân) */
    .count {
        counter-reset: ci var(--ci) cd var(--cd);
        animation: countI 1.4s var(--ease) both, countD 1.4s var(--ease) both;
    }
    .count::before { content: counter(ci) "." counter(cd, decimal-leading-zero); }
    .count-pct::before { content: counter(ci) "%"; }

    /* ---------- Badge xếp loại ---------- */
    .badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 14px;
        border-radius: 999px;
        font-size: 0.9rem;
        font-weight: 600;
        transition: transform 0.25s var(--ease);
    }
    .badge:hover { transform: scale(1.04); }
    .badge::before {
        content: "";
        width: 8px; height: 8px;
        border-radius: 50%;
        background: currentColor;
    }
    .badge-gioi { background: #d7eefc; color: #2f6a95; }
    .badge-kha { background: #daf3e9; color: #2a7254; }
    .badge-tb { background: #fde6dc; color: #9a5640; }
    .badge-yeu { background: #fbe1e5; color: #9b4a5a; }

    /* ---------- Dòng chào ở tab Tổng quan ---------- */
    .welcome {
        background: var(--card);
        border: 1px solid rgba(255, 255, 255, 0.9);
        border-radius: 18px;
        padding: 12px 20px;
        margin-bottom: 16px;
        color: var(--ink);
        box-shadow: var(--shadow);
    }

    /* ---------- Hồ sơ cá nhân ---------- */
    .profile {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 20px;
        background: var(--card);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.9);
        border-radius: 28px;
        padding: 22px 26px;
        box-shadow: var(--shadow);
        animation: rise 0.6s var(--ease) both;
    }
    .avatar {
        width: 72px; height: 72px;
        padding: 3px;
        border-radius: 50%;
        background: conic-gradient(#8cc4ee, #a8e0cb, #f6c7b6, #cfc6ef, #8cc4ee);
    }
    .avatar span {
        display: grid; place-items: center;
        width: 100%; height: 100%;
        border-radius: 50%;
        background: #fff;
        color: var(--blue-txt);
        font-size: 1.5rem;
        font-weight: 700;
    }
    .p-name { font-size: 1.6rem; font-weight: 700; line-height: 1.2; }
    .p-meta { color: var(--ink-soft); font-size: 0.92rem; margin-top: 2px; }
    .p-right { margin-left: auto; display: flex; align-items: center; flex-wrap: wrap; gap: 10px; }
    .pill {
        padding: 6px 14px;
        border-radius: 999px;
        background: #fff;
        border: 1px solid var(--line);
        font-size: 0.9rem;
        font-weight: 600;
    }

    /* ---------- Ô điểm thành phần ---------- */
    .s-tile {
        background: var(--card);
        border: 1px solid rgba(255, 255, 255, 0.9);
        border-radius: 20px;
        padding: 16px 18px;
        box-shadow: var(--shadow);
        height: 100%;
        transition: transform 0.35s var(--ease), box-shadow 0.35s var(--ease);
        animation: rise 0.6s var(--ease) both;
        animation-delay: var(--d, 0s);
    }
    .s-tile:hover { transform: translateY(-4px); box-shadow: var(--shadow-hover); }
    .s-label { font-size: 0.88rem; color: var(--ink-soft); font-weight: 500; }
    .s-value { position: relative; font-size: 1.9rem; font-weight: 700; margin: 6px 0 8px; line-height: 1.1; }
    .delta { display: inline-block; padding: 3px 10px; border-radius: 999px; font-size: 0.8rem; font-weight: 600; }
    .delta-up { background: #daf3e9; color: #2a7254; }
    .delta-down { background: #fde6dc; color: #9a5640; }
    .delta-eq { background: #e8eef4; color: #46667d; }

    /* ---------- Thanh tiến độ ---------- */
    .pbar { height: 16px; border-radius: 999px; background: #e0edf7; overflow: hidden; }
    .pfill {
        height: 100%;
        width: var(--w);
        border-radius: 999px;
        background: linear-gradient(90deg, #8cc4ee, #a8e0cb);
        animation: grow 1.2s var(--ease) both;
    }
    .pscale { display: flex; justify-content: space-between; margin-top: 6px; font-size: 0.85rem; color: var(--ink-soft); }

    .note {
        background: var(--card);
        border: 1px solid rgba(255, 255, 255, 0.9);
        border-radius: 22px;
        padding: 18px 20px;
        margin-top: 16px;
        box-shadow: var(--shadow);
        line-height: 1.6;
    }

    /* ---------- Thẻ tác giả ở sidebar ---------- */
    .dev-card {
        display: flex;
        gap: 14px;
        align-items: center;
        margin-top: 18px;
        padding: 16px;
        border-radius: 20px;
        background: rgba(255, 255, 255, 0.75);
        border: 1px solid rgba(255, 255, 255, 0.95);
        box-shadow: var(--shadow);
    }
    .dev-avatar {
        flex: none;
        width: 48px; height: 48px;
        padding: 3px; border-radius: 50%;
        background: conic-gradient(#8cc4ee, #a8e0cb, #f6c7b6, #cfc6ef, #8cc4ee);
    }
    .dev-avatar span {
        display: grid; place-items: center;
        width: 100%; height: 100%;
        border-radius: 50%;
        background: #fff;
        color: var(--blue-txt);
        font-weight: 700;
        font-size: 0.95rem;
    }
    .dev-card h4 { margin: 0 0 6px 0; font-size: 1rem; }
    .dev-card p { margin: 2px 0; font-size: 0.86rem; color: var(--ink-soft); }

    /* ---------- Tùy biến thành phần Streamlit ---------- */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #d9eaf7, #e9f3fa 60%, #eef6fc);
        border-right: 1px solid var(--line);
    }

    /* Tab: dùng !important vì CSS mặc định của Streamlit có độ ưu tiên cao hơn */
    .stTabs [data-baseweb="tab-list"],
    [data-testid="stTabs"] [data-baseweb="tab-list"] {
        gap: 8px !important;
        width: fit-content !important;
        max-width: 100% !important;
        overflow-x: auto !important;
        padding: 6px !important;
        border-radius: 999px !important;
        background: rgba(255, 255, 255, 0.65) !important;
        border: 1px solid var(--line) !important;
    }
    .stTabs [data-baseweb="tab"],
    [data-testid="stTabs"] [data-baseweb="tab"] {
        height: 42px !important;
        padding: 0 20px !important;
        border-radius: 999px !important;
        background: transparent !important;
        color: var(--ink-soft) !important;
        font-weight: 600 !important;
        transition: background 0.3s var(--ease), color 0.3s var(--ease), box-shadow 0.3s var(--ease);
    }
    .stTabs [data-baseweb="tab"]:hover,
    [data-testid="stTabs"] [data-baseweb="tab"]:hover {
        background: rgba(140, 196, 238, 0.22) !important;
        color: var(--ink) !important;
    }
    .stTabs [aria-selected="true"],
    [data-testid="stTabs"] [aria-selected="true"] {
        background: linear-gradient(120deg, #8cc4ee, #a8e0cb) !important;
        color: #1f3f58 !important;
        box-shadow: 0 6px 16px rgba(74, 143, 196, 0.25) !important;
    }
    .stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"],
    [data-testid="stTabs"] [data-baseweb="tab-highlight"],
    [data-testid="stTabs"] [data-baseweb="tab-border"] { display: none !important; }

    /* Ô chọn (selectbox) */
    [data-baseweb="select"] > div,
    [data-testid="stSelectbox"] [data-baseweb="select"] > div {
        border-radius: 14px !important;
        background: #fff !important;
        border: 1px solid var(--line) !important;
        transition: box-shadow 0.25s ease, border-color 0.25s ease;
    }
    [data-baseweb="select"] > div:hover, [data-baseweb="select"] > div:focus-within {
        border-color: var(--blue-txt) !important;
        box-shadow: 0 0 0 4px rgba(140, 196, 238, 0.3) !important;
    }

    [data-testid="stPlotlyChart"] {
        background: var(--card);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.9);
        border-radius: 24px;
        padding: 14px;
        box-shadow: var(--shadow);
    }
    [data-testid="stDataFrame"] {
        border-radius: 20px;
        overflow: hidden;
        border: 1px solid var(--line);
        box-shadow: var(--shadow);
    }

    /* Nút tải bảng điểm: là hành động chính của trang nên được làm nổi bật */
    .stDownloadButton button {
        border-radius: 999px;
        border: 1px solid #2f6a95;
        background: linear-gradient(120deg, #3a79ad, #2f6a95);
        color: #fff;
        font-weight: 600;
        padding: 0.45rem 1.2rem;
        white-space: nowrap;
        transition: transform 0.3s var(--ease), box-shadow 0.3s var(--ease), filter 0.3s ease;
    }
    .stDownloadButton button p, .stDownloadButton button span { color: #fff !important; }
    .stDownloadButton button:hover:not(:disabled) {
        transform: translateY(-2px);
        filter: brightness(1.08);
        box-shadow: 0 8px 18px rgba(47, 106, 149, 0.3);
    }
    .stDownloadButton button:disabled { opacity: 0.55; }

    /* Viền focus rõ ràng cho người dùng bàn phím */
    .stTabs [data-baseweb="tab"]:focus-visible,
    [data-testid="stTabs"] [data-baseweb="tab"]:focus-visible,
    .stDownloadButton button:focus-visible,
    [data-baseweb="select"]:focus-within {
        outline: 3px solid rgba(58, 121, 173, 0.55) !important;
        outline-offset: 2px;
    }

    .footer { text-align: center; color: var(--ink-soft); font-size: 0.88rem; margin-top: 2.5rem; padding: 1rem; }

    ::-webkit-scrollbar { width: 10px; height: 10px; }
    ::-webkit-scrollbar-thumb { background: #bcdaf0; border-radius: 10px; border: 2px solid var(--bg); }
    ::-webkit-scrollbar-track { background: transparent; }

    /* ---------- Responsive ---------- */
    @media (max-width: 640px) {
        .block-container { padding-left: 1rem; padding-right: 1rem; padding-top: 1.2rem; }
        .hero { padding: 18px 20px; }
        .hero-title { font-size: 1.5rem; }
        .m-value { font-size: 1.7rem; }
        .profile { padding: 18px; }
        .p-right { margin-left: 0; }
    }

    /* Tôn trọng người dùng muốn giảm chuyển động */
    @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==========================================
# 4. HÀM TIỆN ÍCH
# ==========================================
def html(markup):
    """Hiển thị HTML: gộp xuống dòng để Markdown không hiểu nhầm thành code."""
    st.markdown(re.sub(r"\s*\n\s*", " ", markup.strip()), unsafe_allow_html=True)


def _width_kwargs(func):
    """Dùng width='stretch' nếu phiên bản Streamlit hỗ trợ, ngược lại dùng use_container_width."""
    try:
        if "width" in inspect.signature(func).parameters:
            return {"width": "stretch"}
    except (TypeError, ValueError):
        pass
    return {"use_container_width": True}


PLOTLY_KW = _width_kwargs(st.plotly_chart)
DATAFRAME_KW = _width_kwargs(st.dataframe)


def count_up(value, kind="dec"):
    """Số đếm tăng dần bằng CSS. kind='dec' -> 7.63, kind='pct' -> 100%.

    Phần hiển thị do CSS tạo ra (ẩn với trình đọc màn hình), nên có thêm
    một thẻ .sr-only chứa số thật để trình đọc màn hình và việc sao chép văn bản hoạt động.
    """
    if kind == "pct":
        return (
            f'<span class="count count-pct" style="--ci:{int(round(value))}" aria-hidden="true"></span>'
            f'<span class="sr-only">{value:.0f}%</span>'
        )
    value = round(float(value), 2)
    whole = int(value)
    frac = int(round((value - whole) * 100))
    return (
        f'<span class="count" style="--ci:{whole};--cd:{frac}" aria-hidden="true"></span>'
        f'<span class="sr-only">{value:.2f}</span>'
    )


def initials(name):
    parts = name.split()
    return (parts[0][0] + (parts[-1][0] if len(parts) > 1 else "")).upper()


def style_fig(fig, height):
    """Áp dụng phong cách pastel chung cho mọi biểu đồ Plotly."""
    fig.update_layout(
        height=height,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=16, r=16, t=24, b=16),
        font=dict(family="Be Vietnam Pro, sans-serif", color=INK),
        hoverlabel=dict(
            bgcolor="white", font=dict(family="Be Vietnam Pro, sans-serif", color=INK)
        ),
    )
    fig.update_xaxes(showgrid=False, linecolor=LINE)
    fig.update_yaxes(gridcolor="#e3eef7", zeroline=False)
    return fig


# ==========================================
# 5. CHUẨN BỊ & XỬ LÝ DỮ LIỆU (GIỮ NGUYÊN LOGIC)
# ==========================================
@st.cache_data
def get_student_data():
    data = {
        "Họ và tên": [
            "An", "Bình", "Chi", "Dũng", "Hà",
            "Lan", "Minh", "Nam", "Phúc", "Trang",
        ],
        "Điểm chuyên cần": [8.0, 8.5, 6.5, 9.0, 7.5, 6.0, 8.5, 7.0, 7.5, 9.5],
        "Điểm giữa kỳ": [8.0, 8.0, 6.0, 9.0, 7.0, 5.5, 8.0, 6.5, 7.0, 9.0],
        "Điểm cuối kỳ": [8.0, 8.5, 6.5, 9.0, 7.5, 5.5, 8.5, 7.0, 7.5, 9.0],
    }
    df = pd.DataFrame(data)

    # Công thức: 20% Chuyên cần + 30% Giữa kỳ + 50% Cuối kỳ
    df["Tong_ket"] = (
        0.2 * df["Điểm chuyên cần"]
        + 0.3 * df["Điểm giữa kỳ"]
        + 0.5 * df["Điểm cuối kỳ"]
    ).round(2)

    # Xếp loại
    def phan_loai(score):
        if score >= 8.5:
            return "Giỏi"
        elif score >= 7.0:
            return "Khá"
        elif score >= 5.0:
            return "Trung bình"
        else:
            return "Yếu"

    df["Xep_loai"] = df["Tong_ket"].apply(phan_loai)

    # Thứ hạng trong lớp (điểm cao nhất = hạng 1)
    df["Hang"] = df["Tong_ket"].rank(ascending=False, method="min").astype(int)
    return df


df_students = get_student_data()
TOTAL = len(df_students)
COMPONENTS = ["Điểm chuyên cần", "Điểm giữa kỳ", "Điểm cuối kỳ"]
SHORT_NAMES = {
    "Điểm chuyên cần": "Chuyên cần",
    "Điểm giữa kỳ": "Giữa kỳ",
    "Điểm cuối kỳ": "Cuối kỳ",
}
# Tên cột hiển thị (bảng trên web và file CSV xuất ra dùng chung)
RENAME_COLUMNS = {"Hang": "Hạng", "Tong_ket": "Tổng kết", "Xep_loai": "Xếp loại"}
TABLE_COLUMNS = ["Hang", "Họ và tên"] + COMPONENTS + ["Tong_ket", "Xep_loai"]

class_avg = df_students[COMPONENTS + ["Tong_ket"]].mean()
student_names = df_students["Họ và tên"].tolist()

# ==========================================
# 6. THANH BÊN (SIDEBAR) & BỘ LỌC
# ==========================================
with st.sidebar:
    st.title("🎓 Bảng điều khiển")
    st.subheader("Lọc và tìm kiếm")

    search_options = ["Tất cả sinh viên"] + student_names
    selected_student_search = st.selectbox(
        "Tìm kiếm hoặc chọn sinh viên",
        options=search_options,
        index=0,
        help="Bấm vào ô hoặc gõ chữ cái đầu của tên để chọn nhanh sinh viên.",
    )

    present_grades = set(df_students["Xep_loai"])
    categories = ["Tất cả xếp loại"] + [g for g in GRADE_ORDER if g in present_grades]
    selected_category = st.selectbox("Lọc theo xếp loại", categories)

    st.caption(
        "Bộ lọc áp dụng cho bảng điểm và file CSV. "
        "Chọn một sinh viên cũng sẽ mở sẵn hồ sơ của bạn đó ở tab Tra cứu. "
        "Biểu đồ luôn thống kê cả lớp."
    )

    # Xử lý dữ liệu sau lọc
    df_filtered = df_students.copy()
    if selected_student_search != "Tất cả sinh viên":
        df_filtered = df_filtered[df_filtered["Họ và tên"] == selected_student_search]
    if selected_category != "Tất cả xếp loại":
        df_filtered = df_filtered[df_filtered["Xep_loai"] == selected_category]

    html(
        f"""
        <div class="dev-card">
            <div class="dev-avatar"><span>{initials(AUTHOR_NAME)}</span></div>
            <div>
                <h4>Thông tin tác giả</h4>
                <p><b>Họ và tên:</b> {AUTHOR_NAME}</p>
                <p><b>MSSV:</b> {AUTHOR_ID_MASKED}</p>
                <p><b>Lớp:</b> {AUTHOR_CLASS}</p>
                <p><b>Trường:</b> {AUTHOR_SCHOOL}</p>
            </div>
        </div>
        """
    )

# ==========================================
# 7. TIÊU ĐỀ TRANG WEB
# ==========================================
html(
    """
    <div class="hero">
        <div class="hero-title" role="heading" aria-level="1">Quản lý điểm sinh viên</div>
        <div class="hero-sub">Thống kê tự động, biểu đồ tương tác và tra cứu hồ sơ học tập của cả lớp.</div>
    </div>
    """
)

# ==========================================
# 8. BỐ CỤC TABS (tên ngắn để không bị cuộn ngang trên điện thoại)
# ==========================================
tab1, tab2, tab3 = st.tabs(["📊 Tổng quan", "📈 Biểu đồ", "🔍 Tra cứu"])

# ------------------------------------------
# TAB 1: TỔNG QUAN & BẢNG ĐIỂM
# ------------------------------------------
with tab1:
    avg_score = df_students["Tong_ket"].mean()
    max_student = df_students.loc[df_students["Tong_ket"].idxmax()]
    min_student = df_students.loc[df_students["Tong_ket"].idxmin()]
    passed_count = int((df_students["Tong_ket"] >= 5.0).sum())
    pass_rate = passed_count / TOTAL * 100

    html(
        f"""
        <div class="welcome">
            Xin chào! Lớp hiện có <b>{TOTAL}</b> sinh viên (dữ liệu minh họa) với điểm trung bình
            <b>{avg_score:.2f}</b>. Bảng điểm đang hiển thị <b>{len(df_filtered)}/{TOTAL}</b>
            sinh viên theo bộ lọc ở thanh bên.
        </div>
        """
    )

    cards = [
        ("🎯", "Điểm TB lớp", count_up(avg_score), "Thang điểm 10", BLUE, "#e3f1fc"),
        ("🏆", "Điểm cao nhất", count_up(max_student["Tong_ket"]), max_student["Họ và tên"], MINT, "#e1f5ee"),
        ("📉", "Điểm thấp nhất", count_up(min_student["Tong_ket"]), min_student["Họ và tên"], PEACH, "#fdeee7"),
        ("✅", "Tỷ lệ đạt", count_up(pass_rate, "pct"), f"{passed_count}/{TOTAL} sinh viên", "#cfc6ef", "#ece7f8"),
    ]
    for col, (icon, label, value, sub, accent, tint), i in zip(
        st.columns(4), cards, range(4)
    ):
        with col:
            html(
                f"""
                <div class="m-card" style="--accent:{accent};--tint:{tint};--d:{i * 0.08}s">
                    <div class="m-top">
                        <div class="m-icon" aria-hidden="true">{icon}</div>
                        <div class="m-label">{label}</div>
                    </div>
                    <div class="m-value">{value}</div>
                    <div class="m-sub">{sub}</div>
                </div>
                """
            )

    st.write("")

    # Bảng hiển thị + file CSV dùng chung một dữ liệu: đúng tên cột, đúng bộ lọc, xếp theo hạng
    df_show = (
        df_filtered.sort_values(["Hang", "Họ và tên"])[TABLE_COLUMNS]
        .rename(columns=RENAME_COLUMNS)
    )

    head_col, btn_col = st.columns([3, 1])
    with head_col:
        st.subheader("📋 Bảng điểm sinh viên")
    with btn_col:
        csv_bytes = df_show.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "⬇ Tải CSV",
            data=csv_bytes,
            file_name="bang_diem_sinh_vien.csv",
            mime="text/csv",
            disabled=df_show.empty,
            help="Tải đúng danh sách đang hiển thị trong bảng (mở được bằng Excel).",
        )

    if df_show.empty:
        st.info("Không có sinh viên nào khớp bộ lọc. Hãy đổi điều kiện ở thanh bên.")
    else:

        def highlight_xep_loai(val):
            bg, fg = GRADE_BADGE.get(val, GRADE_BADGE["Yếu"])
            return f"background-color: {bg}; color: {fg}; font-weight: 600;"

        styler = df_show.style
        apply_cell = styler.map if hasattr(styler, "map") else styler.applymap
        styled_df = apply_cell(highlight_xep_loai, subset=["Xếp loại"]).format(
            {
                "Điểm chuyên cần": "{:.1f}",
                "Điểm giữa kỳ": "{:.1f}",
                "Điểm cuối kỳ": "{:.1f}",
                "Tổng kết": "{:.2f}",
            }
        )
        st.dataframe(styled_df, hide_index=True, height=390, **DATAFRAME_KW)

    with st.expander("ℹ️ Cách tính điểm và xếp loại"):
        st.markdown(
            "- **Điểm tổng kết** = 20% Chuyên cần + 30% Giữa kỳ + 50% Cuối kỳ\n"
            "- **Xếp loại:** Giỏi từ 8.5 · Khá từ 7.0 · Trung bình từ 5.0 · Yếu dưới 5.0\n"
            "- **Đạt:** điểm tổng kết từ 5.0 trở lên\n"
            "- **Hạng:** điểm cao nhất là hạng 1, điểm bằng nhau cùng hạng"
        )

# ------------------------------------------
# TAB 2: BIỂU ĐỒ & PHÂN TÍCH
# ------------------------------------------
with tab2:
    st.subheader("📈 Phân tích trực quan kết quả học tập")

    col_chart1, col_chart2 = st.columns([6, 4])

    with col_chart1:
        st.markdown("##### Điểm tổng kết từng sinh viên")
        df_sorted = df_students.sort_values("Tong_ket", ascending=False)
        class_mean = df_students["Tong_ket"].mean()
        fig_bar = px.bar(
            df_sorted,
            x="Họ và tên",
            y="Tong_ket",
            color="Xep_loai",
            color_discrete_map=GRADE_FILL,
            category_orders={
                "Họ và tên": df_sorted["Họ và tên"].tolist(),
                "Xep_loai": GRADE_ORDER,
            },
            text="Tong_ket",
            labels={"Tong_ket": "Điểm tổng kết", "Họ và tên": "Sinh viên", "Xep_loai": "Xếp loại"},
        )
        fig_bar.update_traces(
            textposition="outside",
            texttemplate="%{text:.2f}",
            hovertemplate="<b>%{x}</b><br>Điểm tổng kết: %{y:.2f}<extra></extra>",
        )
        try:  # Bo góc cột (chỉ có ở Plotly bản mới)
            fig_bar.update_traces(marker_cornerradius=10)
        except Exception:
            pass
        # Viền đậm hơn màu nền để cột pastel vẫn nổi bật trên nền trắng
        fig_bar.for_each_trace(
            lambda t: t.update(
                marker_line_color=GRADE_EDGE.get(t.name, BLUE_D), marker_line_width=1.5
            )
        )
        # Nhãn "TB lớp" đặt ngoài vùng cột (bên phải) để không đè lên nhãn điểm
        fig_bar.add_hline(
            y=class_mean,
            line_dash="dot",
            line_color=BLUE_TXT,
            annotation_text=f"TB lớp {class_mean:.2f}",
            annotation_position="right",
            annotation_font_color=BLUE_TXT,
        )
        style_fig(fig_bar, 420)
        fig_bar.update_layout(
            yaxis=dict(range=[0, 10.8], title="Điểm số"),
            xaxis=dict(title=""),
            legend=dict(orientation="h", y=-0.15, title_text=""),
            bargap=0.28,
            margin=dict(l=16, r=96, t=24, b=16),
        )
        st.plotly_chart(fig_bar, **PLOTLY_KW)

    with col_chart2:
        st.markdown("##### Tỷ lệ phân bổ xếp loại của lớp")
        rank_counts = (
            df_students["Xep_loai"].value_counts().reindex(GRADE_ORDER).dropna().astype(int).reset_index()
        )
        rank_counts.columns = ["Xếp loại", "Số lượng"]
        fig_pie = px.pie(
            rank_counts,
            names="Xếp loại",
            values="Số lượng",
            color="Xếp loại",
            color_discrete_map=GRADE_FILL,
            hole=0.55,
        )
        fig_pie.update_traces(
            sort=False,
            textposition="inside",
            textinfo="percent",
            insidetextorientation="horizontal",
            marker=dict(line=dict(color="white", width=3)),
            hovertemplate="<b>%{label}</b>: %{value} SV (%{percent})<extra></extra>",
        )
        style_fig(fig_pie, 420)
        fig_pie.update_layout(
            showlegend=True,
            legend=dict(orientation="h", y=-0.08, title_text=""),
            annotations=[
                dict(
                    text=f"<b>{TOTAL}</b><br>sinh viên",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=18, color=INK),
                )
            ],
        )
        st.plotly_chart(fig_pie, **PLOTLY_KW)

    st.write("")
    col_chart3, col_chart4 = st.columns(2)

    with col_chart3:
        st.markdown("##### Điểm trung bình theo từng thành phần")
        comp_avg = pd.DataFrame(
            {
                "Thành phần": ["Chuyên cần (20%)", "Giữa kỳ (30%)", "Cuối kỳ (50%)"],
                "Điểm TB": [class_avg[c] for c in COMPONENTS],
            }
        )
        comp_edge = {
            "Chuyên cần (20%)": BLUE_D,
            "Giữa kỳ (30%)": "#5fbf9a",
            "Cuối kỳ (50%)": "#e8927c",
        }
        fig_comp = px.bar(
            comp_avg,
            x="Điểm TB",
            y="Thành phần",
            orientation="h",
            color="Thành phần",
            color_discrete_sequence=[BLUE, MINT, PEACH],
            text="Điểm TB",
        )
        fig_comp.update_traces(texttemplate="%{text:.2f}", textposition="outside")
        try:
            fig_comp.update_traces(marker_cornerradius=10)
        except Exception:
            pass
        fig_comp.for_each_trace(
            lambda t: t.update(
                marker_line_color=comp_edge.get(t.name, BLUE_D), marker_line_width=1.5
            )
        )
        style_fig(fig_comp, 340)
        fig_comp.update_layout(
            showlegend=False,
            xaxis=dict(range=[0, 10.5], title="Điểm số"),
            yaxis=dict(title="", autorange="reversed"),
            bargap=0.35,
        )
        st.plotly_chart(fig_comp, **PLOTLY_KW)

    with col_chart4:
        st.markdown("##### So sánh ba loại điểm của từng sinh viên")
        # Cột nhóm thay cho biểu đồ đường: mỗi sinh viên là một nhóm riêng, không nối các bạn với nhau
        df_long = df_students.melt(
            id_vars="Họ và tên",
            value_vars=COMPONENTS,
            var_name="Thành phần",
            value_name="Điểm",
        )
        df_long["Thành phần"] = df_long["Thành phần"].map(SHORT_NAMES)
        fig_grp = px.bar(
            df_long,
            x="Họ và tên",
            y="Điểm",
            color="Thành phần",
            barmode="group",
            color_discrete_map={"Chuyên cần": BLUE, "Giữa kỳ": MINT, "Cuối kỳ": PEACH},
            category_orders={
                "Họ và tên": student_names,
                "Thành phần": list(SHORT_NAMES.values()),
            },
        )
        grp_edge = {"Chuyên cần": BLUE_D, "Giữa kỳ": "#5fbf9a", "Cuối kỳ": "#e8927c"}
        fig_grp.update_traces(
            hovertemplate="<b>%{x}</b><br>%{fullData.name}: %{y:.1f}<extra></extra>"
        )
        fig_grp.for_each_trace(
            lambda t: t.update(
                marker_line_color=grp_edge.get(t.name, BLUE_D), marker_line_width=1.5
            )
        )
        style_fig(fig_grp, 340)
        fig_grp.update_layout(
            yaxis=dict(range=[0, 10.5], title="Điểm số"),
            xaxis=dict(title=""),
            legend=dict(orientation="h", y=-0.2, title_text=""),
            bargap=0.25,
        )
        st.plotly_chart(fig_grp, **PLOTLY_KW)

# ------------------------------------------
# TAB 3: TRA CỨU CÁ NHÂN
# ------------------------------------------
with tab3:
    st.subheader("🔍 Tra cứu chi tiết hồ sơ thành tích cá nhân")

    # Nếu đã chọn một sinh viên ở thanh bên thì mở sẵn hồ sơ của bạn đó
    default_index = (
        student_names.index(selected_student_search)
        if selected_student_search in student_names
        else 0
    )
    selected_student_name = st.selectbox(
        "Chọn sinh viên cần tra cứu hồ sơ",
        options=student_names,
        index=default_index,
    )
    student_info = df_students[df_students["Họ và tên"] == selected_student_name].iloc[0]
    rank_class = GRADE_CLASS.get(student_info["Xep_loai"], "badge-yeu")
    rank_pos = int(student_info["Hang"])

    html(
        f"""
        <div class="profile">
            <div class="avatar"><span>{initials(student_info['Họ và tên'])}</span></div>
            <div>
                <div class="p-meta">Hồ sơ học tập cá nhân</div>
                <div class="p-name">{student_info['Họ và tên']}</div>
            </div>
            <div class="p-right">
                <span class="pill"><span aria-hidden="true">🏅</span> Hạng {rank_pos}/{TOTAL}</span>
                <span class="badge {rank_class}">Xếp loại: {student_info['Xep_loai']}</span>
            </div>
        </div>
        """
    )
    st.write("")

    def delta_chip(diff):
        if abs(diff) < 0.005:
            return '<span class="delta delta-eq">Bằng TB lớp</span>'
        cls, arrow = ("delta-up", "▲") if diff > 0 else ("delta-down", "▼")
        return f'<span class="delta {cls}">{arrow} {abs(diff):.2f} so với TB lớp</span>'

    tiles = [
        ("🎯 Chuyên cần (20%)", f"{student_info['Điểm chuyên cần']:.1f}", student_info["Điểm chuyên cần"] - class_avg["Điểm chuyên cần"], BLUE_TXT),
        ("📝 Giữa kỳ (30%)", f"{student_info['Điểm giữa kỳ']:.1f}", student_info["Điểm giữa kỳ"] - class_avg["Điểm giữa kỳ"], BLUE_TXT),
        ("✍️ Cuối kỳ (50%)", f"{student_info['Điểm cuối kỳ']:.1f}", student_info["Điểm cuối kỳ"] - class_avg["Điểm cuối kỳ"], BLUE_TXT),
        ("🏆 Điểm tổng kết", count_up(student_info["Tong_ket"]), student_info["Tong_ket"] - class_avg["Tong_ket"], MINT_D),
    ]
    for col, (label, value, diff, color), i in zip(st.columns(4), tiles, range(4)):
        with col:
            html(
                f"""
                <div class="s-tile" style="--d:{i * 0.08}s">
                    <div class="s-label">{label}</div>
                    <div class="s-value" style="color:{color}">{value}</div>
                    {delta_chip(diff)}
                </div>
                """
            )

    st.write("")
    col_cmp, col_info = st.columns([5, 4])

    with col_cmp:
        st.markdown("##### So sánh với điểm trung bình lớp")
        cats = [SHORT_NAMES[c] for c in COMPONENTS]
        mine = [float(student_info[c]) for c in COMPONENTS]
        avg = [float(class_avg[c]) for c in COMPONENTS]

        # Thanh ngang thay cho biểu đồ radar 3 trục: đọc được giá trị chính xác
        fig_cmp = go.Figure()
        fig_cmp.add_trace(
            go.Bar(
                y=cats, x=mine, orientation="h", name=selected_student_name,
                marker=dict(color=BLUE, line=dict(color=BLUE_D, width=1.5)),
                text=[f"{v:.1f}" for v in mine], textposition="outside",
                hovertemplate="%{y}: %{x:.1f}<extra>" + selected_student_name + "</extra>",
            )
        )
        fig_cmp.add_trace(
            go.Bar(
                y=cats, x=avg, orientation="h", name="Trung bình lớp",
                marker=dict(color=PEACH, line=dict(color="#e8927c", width=1.5)),
                text=[f"{v:.2f}" for v in avg], textposition="outside",
                hovertemplate="%{y}: %{x:.2f}<extra>Trung bình lớp</extra>",
            )
        )
        style_fig(fig_cmp, 340)
        fig_cmp.update_layout(
            barmode="group",
            bargap=0.3,
            xaxis=dict(range=[0, 10.8], title="Điểm số"),
            yaxis=dict(title="", autorange="reversed"),
            legend=dict(orientation="h", y=-0.2, title_text=""),
        )
        st.plotly_chart(fig_cmp, **PLOTLY_KW)

    with col_info:
        st.markdown("##### Tiến độ điểm số (thang 10)")
        progress_pct = float(student_info["Tong_ket"]) / 10.0 * 100
        html(
            f"""
            <div class="pbar" role="img" aria-label="Điểm tổng kết {student_info['Tong_ket']:.2f} trên thang 10">
                <div class="pfill" style="--w:{progress_pct:.0f}%"></div>
            </div>
            <div class="pscale"><span>0</span><span>5</span><span>10</span></div>
            """
        )

        scores = {c: float(student_info[c]) for c in COMPONENTS}
        comments = {
            "Giỏi": "Kết quả rất tốt, các thành phần điểm đều ở mức cao. Hãy duy trì phong độ này.",
            "Khá": "Kết quả khá tốt. Cải thiện thêm thành phần điểm thấp nhất sẽ giúp tiến gần mức Giỏi.",
            "Trung bình": "Đã đạt yêu cầu. Nên ôn tập thêm để nâng điểm ở các bài kiểm tra tới.",
            "Yếu": "Cần cố gắng nhiều hơn. Hãy trao đổi với giảng viên để có kế hoạch ôn tập phù hợp.",
        }
        if max(scores.values()) - min(scores.values()) < 0.01:
            focus_line = "Ba thành phần điểm đang <b>đồng đều</b>."
        else:
            weakest = min(COMPONENTS, key=lambda c: scores[c])
            focus_line = (
                f"Thành phần cần chú ý nhất: <b>{SHORT_NAMES[weakest]}</b> "
                f"({scores[weakest]:.1f} điểm)."
            )
        html(
            f"""
            <div class="note"><span aria-hidden="true">💡</span> <b>Nhận xét tự động</b><br>
            {comments.get(student_info['Xep_loai'], '')}<br>
            {focus_line}
            </div>
            """
        )

# ==========================================
# 9. FOOTER
# ==========================================
html(
    """
    <div class="footer">
        Hệ thống quản lý điểm sinh viên · Xây dựng với Streamlit, Pandas và Plotly
    </div>
    """
)
