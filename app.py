import streamlit as st
import base64
from PIL import Image
import google.generativeai as genai
import requests
import io

# 1. 페이지 설정
st.set_page_config(
    page_title="diyv - 뷰티 정밀 검색 엔진", 
    page_icon="🔍", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 2. 테마 및 상태 관리
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "light"

if "show_cam" not in st.session_state:
    st.session_state.show_cam = False

is_dark = (st.session_state.theme_mode == "dark")

# 테마 색상 팔레트
bg_color = "#0F172A" if is_dark else "#f8fafd"
text_color = "#F1F5F9" if is_dark else "#202124"
card_bg = "#1E293B" if is_dark else "#ffffff"
card_border = "#334155" if is_dark else "#dfe1e5"
input_text = "#F8FAFC" if is_dark else "#202124"
placeholder_color = "#94A3B8" if is_dark else "#70757a"
icon_color = "#94A3B8" if is_dark else "#5f6368"
hover_glow = "rgba(65, 178, 231, 0.18)"
hover_shadow = "rgba(65, 178, 231, 0.3)"

# 로고 인코딩
def get_base64_image(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return ""

img_base64 = get_base64_image("logo.png")

# 3. CSS 주입 (iframe 없이 네이티브 DOM을 완벽한 Pill 형태로 변환)
st.markdown(f"""
<style>
    /* 전체 배경 */
    .stApp {{
        background-color: {bg_color} !important;
        color: {text_color} !important;
    }}

    /* Streamlit 기본 헤더/푸터 숨김 */
    #MainMenu, header, footer {{
        visibility: hidden !important;
        display: none !important;
    }}

    /* 우측 상단 테마 토글 버튼 고정 */
    .theme-btn-fixed {{
        position: fixed;
        top: 24px;
        right: 28px;
        z-index: 999999;
    }}
    .theme-btn-fixed button {{
        border-radius: 50% !important;
        width: 42px !important;
        height: 42px !important;
        min-width: 42px !important;
        padding: 0 !important;
        background-color: {card_bg} !important;
        border: 1px solid {card_border} !important;
        box-shadow: 0 1px 3px rgba(32, 33, 36, 0.08) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.2s ease !important;
    }}
    .theme-btn-fixed button:hover {{
        border-color: #41b2e7 !important;
        box-shadow: 0 0 0 3px {hover_glow}, 0 2px 8px {hover_shadow} !important;
    }}

    /* 로고 중앙 정렬 */
    .logo-box {{
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 55px;
        margin-bottom: 25px;
    }}
    .logo-box img {{
        width: 180px;
        max-width: 100%;
        height: auto;
    }}

    /* 검색창 영역 래퍼: 완벽한 Pill 디자인 강제 적용 */
    div[data-testid="stTextInput"] > div {{
        background: {card_bg} !important;
        border: 1px solid {card_border} !important;
        border-radius: 28px !important;
        padding: 4px 50px 4px 20px !important;
        box-shadow: 0 1px 6px rgba(32, 33, 36, 0.08) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        height: 48px !important;
    }}
    div[data-testid="stTextInput"] > div:hover,
    div[data-testid="stTextInput"] > div:focus-within {{
        border-color: #41b2e7 !important;
        box-shadow: 0 0 0 3px {hover_glow}, 0 4px 16px {hover_shadow} !important;
    }}
    div[data-testid="stTextInput"] input {{
        color: {input_text} !important;
        background: transparent !important;
        border: none !important;
        font-size: 16px !important;
        padding: 0 !important;
        height: 100% !important;
    }}
    div[data-testid="stTextInput"] input::placeholder {{
        color: {placeholder_color} !important;
        font-size: 15px !important;
    }}

    /* 카메라 버튼 위치를 검색창 우측 내부로 완벽 삽입 */
    .cam-btn-wrap {{
        position: relative;
        margin-top: -45px;
        float: right;
        margin-right: 14px;
        z-index: 10;
    }}
    .cam-btn-wrap button {{
        background: transparent !important;
        border: none !important;
        color: {icon_color} !important;
        padding: 4px !important;
        width: 34px !important;
        height: 34px !important;
        border-radius: 50% !important;
        transition: all 0.2s ease !important;
    }}
    .cam-btn-wrap button:hover {{
        background: {hover_glow} !important;
        color: #41b2e7 !important;
    }}

    /* 구분선 */
    hr {{
        border: none !important;
        height: 1px !important;
        background-color: #41b2e7 !important;
        margin: 35px 0 !important;
    }}

    @media (max-width: 640px) {{
        .theme-btn-fixed {{ top: 16px; right: 16px; }}
        .logo-box img {{ width: 140px; }}
    }}
</style>
""", unsafe_allow_html=True)

# 4. API 키 설정
gemini_api_key = st.secrets.get("GEMINI_API_KEY", "")
serper_api_key = st.secrets.get("SERPER_API_KEY", "")

# 5. 테마 토글 버튼 (fixed 고정)
st.markdown('<div class="theme-btn-fixed">', unsafe_allow_html=True)
toggle_label = "☀️" if is_dark else "🌙"
if st.button(toggle_label, key="theme_toggle"):
    st.session_state.theme_mode = "light" if is_dark else "dark"
    st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# 6. 새로고침 로고
if img_base64:
    st.markdown(f"""
    <div class="logo-box">
        <a href="/" target="_self">
            <img src="data:image/png;base64,{img_base64}" alt="diyv">
        </a>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"<h1 style='text-align:center; color:{text_color}; margin-top:55px;'><a href='/' target='_self' style='text-decoration:none; color:inherit;'>diyv</a></h1>", unsafe_allow_html=True)

# 7. 검색 인풋 + 우측 내장 카메라 버튼
search_input = st.text_input(
    label="검색창",
    placeholder="화장품 이름, 성분, 가격 물어보기",
    label_visibility="collapsed",
    key="search_query_input"
)

st.markdown('<div class="cam-btn-wrap">', unsafe_allow_html=True)
if st.button("📷", key="cam_btn", help="사진으로 제품 검색"):
    st.session_state.show_cam = not st.session_state.show_cam
    st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# 카메라 토글 시 파일 업로더 출력
uploaded_image = None
if st.session_state.show_cam:
    st.write("")
    uploaded_image = st.file_uploader(
        "분석할 화장품 사진을 선택하세요", 
        type=["jpg", "jpeg", "png", "webp"],
        label_visibility="collapsed"
    )

# Serper 실시간 검색 함수
def fetch_exact_price_and_product_info(query):
    snippets = []
    if serper_api_key:
        try:
            url = "https://google.serper.dev/search"
            payload = {"q": f"{query} 공식몰 가격 원 올리브영", "gl": "kr", "hl": "ko"}
            headers = {"X-API-KEY": serper_api_key, "Content-Type": "application/json"}
            res = requests.post(url, json=payload, headers=headers, timeout=6)
            if res.status_code == 200:
                for item in res.json().get("organic", [])[:4]:
                    snippets.append(item.get("snippet", ""))
        except Exception:
            pass
    return snippets

# 8. 백엔드 AI 팩트체크 실행 (Enter 키 입력 또는 이미지 업로드 시 즉시 동작)
if uploaded_image:
    st.markdown("---")
    try:
        image = Image.open(uploaded_image)
        st.image(image, width=280, caption="스캔된 실물 제품 사진")
        
        if not gemini_api_key:
            st.error("⚠️ GEMINI_API_KEY가 Streamlit Secrets에 설정되지 않았습니다.")
        else:
            with st.spinner("🤖 [diyv] 비전 AI가 제품명을 식별 중입니다..."):
                genai.configure(api_key=gemini_api_key)
                model = genai.GenerativeModel('gemini-2.5-flash')
                extract_res = model.generate_content([image, "이 화장품 사진에 적힌 정식 브랜드명과 제품명을 한 줄로 요약해줘."])
                identified_name = extract_res.text.strip()

            with st.spinner(f"🌐 [diyv] '{identified_name}' 공식몰 가격 및 실거래가 조회 중..."):
                snippets = fetch_exact_price_and_product_info(identified_name)
                grounding = "\n".join(snippets) if snippets else "추가 웹 검색 결과 없음"

            with st.spinner("✨ [diyv] AI 팩트 매트릭스 리포트 생성 중..."):
                prompt = f"""당신은 객관적이고 투명한 글로벌 뷰티 데이터 분석가 diyv(디브)입니다.
                제공된 이미지와 실시간 검색 데이터를 종합해 객관적인 팩트 매트릭스를 작성하세요.
                
                [실시간 검색 데이터]:
                {grounding}

                - **브랜드 및 제품명**: [명칭]
                - **카테고리**: [스킨케어/메이크업 등]
                - **공식 판매가 및 가격대**: [정확한 원화 가격]
                - **핵심 유효 성분 및 제형**: [성분 분석]
                - **장점 및 가성비 평가**: [객관적 지표]
                - **주의 사항 및 권장 피부 타입**: [주의 성분 및 타겟]"""
                
                res = model.generate_content([image, prompt])
                st.markdown("### 📋 diyv 공식 뷰티 팩트 분석 리포트")
                st.write(res.text)

    except Exception as e:
        st.error(f"이미지 분석 중 오류가 발생했습니다: {e}")

elif search_input.strip():
    st.markdown("---")
    query = search_input.strip()
    
    if not gemini_api_key:
        st.error("⚠️ GEMINI_API_KEY가 Streamlit Secrets에 설정되지 않았습니다.")
    else:
        with st.spinner(f"🌐 [diyv] '{query}' 실시간 데이터 및 가격 조회 중..."):
            snippets = fetch_exact_price_and_product_info(query)
            grounding = "\n".join(snippets) if snippets else "추가 웹 검색 결과 없음"
            genai.configure(api_key=gemini_api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')

        with st.spinner("✨ [diyv] AI 팩트 매트릭스 리포트 생성 중..."):
            prompt = f"""당신은 객관적이고 투명한 글로벌 뷰티 데이터 분석가 diyv(디브)입니다.
            사용자 검색어와 실시간 웹 데이터를 바탕으로 마케팅 수식어를 배제하고 핵심 팩트 위주로 작성하세요.

            [검색어]: {query}
            [실시간 검색 데이터]:
            {grounding}

            - **브랜드 및 제품명**: [명칭]
            - **카테고리**: [스킨케어/메이크업 등]
            - **공식 판매가 및 가격대**: [정확한 원화 가격]
            - **핵심 유효 성분 및 제형**: [성분 분석]
            - **장점 및 가성비 평가**: [객관적 지표]
            - **주의 사항 및 권장 피부 타입**: [주의 성분 및 타겟]"""

            res = model.generate_content(prompt)
            st.success(f"✨ 분석 완료: **[{query}]**")
            st.markdown("### 📋 diyv 뷰티 팩트체크 리포트")
            st.write(res.text)

            if snippets:
                with st.expander("🔍 실시간 가격 및 웹 검색 출처"):
                    for s in snippets:
                        st.info(s)