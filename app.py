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

# 2. 세션 상태 관리
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "light"

if "show_cam" not in st.session_state:
    st.session_state.show_cam = False

if "confirmed_query" not in st.session_state:
    st.session_state.confirmed_query = ""

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

# 로고 Base64 인코딩
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return ""

img_base64 = get_base64_image("logo.png")

# 3. CSS 주입 (원래 정상이었던 우측 상단 고정 + 28px Pill 검색바 100% 동일 복원)
app_css = f"""
<style>
    /* 전체 배경 */
    .stApp {{
        background-color: {bg_color} !important;
        color: {text_color} !important;
    }}

    #MainMenu, header, footer {{
        visibility: hidden !important;
        display: none !important;
    }}

    /* [원복] 우측 상단 테마 버튼 위치 및 완전한 원형 고정 */
    .top-right-theme-area {{
        position: fixed !important;
        top: 24px !important;
        right: 28px !important;
        z-index: 999999 !important;
    }}
    .top-right-theme-area button {{
        border-radius: 50% !important;
        width: 42px !important;
        height: 42px !important;
        min-width: 42px !important;
        max-width: 42px !important;
        min-height: 42px !important;
        max-height: 42px !important;
        padding: 0 !important;
        background-color: {card_bg} !important;
        border: 1px solid {card_border} !important;
        box-shadow: 0 1px 4px rgba(32, 33, 36, 0.08) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.2s ease !important;
        cursor: pointer !important;
    }}
    .top-right-theme-area button:hover {{
        border-color: #41b2e7 !important;
        box-shadow: 0 0 0 3px {hover_glow}, 0 2px 8px {hover_shadow} !important;
    }}
    .top-right-theme-area button p {{
        font-size: 18px !important;
        margin: 0 !important;
        line-height: 1 !important;
    }}

    /* 로고 중앙 정렬 */
    .logo-wrapper {{
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
        margin-top: 50px;
        margin-bottom: 25px;
    }}
    .logo-link {{
        cursor: pointer;
        display: inline-block;
        transition: transform 0.2s ease;
    }}
    .logo-link:hover {{
        transform: scale(1.02);
    }}
    .logo-link img {{
        width: 180px;
        max-width: 100%;
        height: auto;
        display: block;
    }}

    /* [원복] 일체형 Pill 검색 컨테이너 */
    .search-box-pill {{
        max-width: 720px;
        margin: 0 auto;
        background: {card_bg};
        border: 1px solid {card_border};
        border-radius: 28px;
        padding: 6px 16px 6px 20px;
        box-shadow: 0 1px 6px rgba(32, 33, 36, 0.08);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        display: flex;
        align-items: center;
        position: relative;
    }}
    .search-box-pill:hover, .search-box-pill:focus-within {{
        border-color: #41b2e7;
        box-shadow: 0 0 0 3px {hover_glow}, 0 4px 16px {hover_shadow};
    }}

    /* 텍스트 인풋 스타일: 배경/테두리 투명화로 깔끔하게 통합 */
    div[data-testid="stTextInput"] {{
        width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
    }}
    div[data-testid="stTextInput"] > div {{
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
    }}
    div[data-testid="stTextInput"] > div > div {{
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
    }}
    div[data-testid="stTextInput"] input {{
        color: {input_text} !important;
        background: transparent !important;
        border: none !important;
        font-size: 16px !important;
        padding: 0 !important;
        height: 38px !important;
        caret-color: #41b2e7 !important;
    }}
    div[data-testid="stTextInput"] input::placeholder {{
        color: {placeholder_color} !important;
        font-size: 15px !important;
    }}

    /* [원복] 검색창 내부 카메라 버튼: 사각 박스 제거 및 순수 아이콘화 */
    .inline-cam-btn {{
        margin-left: 8px;
    }}
    .inline-cam-btn button {{
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        width: 36px !important;
        height: 36px !important;
        min-height: 36px !important;
        padding: 0 !important;
        border-radius: 50% !important;
        color: {icon_color} !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.2s ease !important;
        cursor: pointer !important;
    }}
    .inline-cam-btn button:hover {{
        background-color: {hover_glow} !important;
        color: #41b2e7 !important;
        border: none !important;
    }}

    /* 하단 구분선 */
    hr {{
        border: none !important;
        height: 1px !important;
        background-color: #41b2e7 !important;
        margin-top: 35px !important;
        margin-bottom: 35px !important;
    }}

    @media (max-width: 640px) {{
        .top-right-theme-area {{ top: 16px !important; right: 16px !important; }}
        .logo-link img {{ width: 140px; }}
    }}
</style>
"""
st.markdown(app_css, unsafe_allow_html=True)

# 4. 백엔드 시크릿에서 API 키 로드
gemini_api_key = st.secrets.get("GEMINI_API_KEY", "")
serper_api_key = st.secrets.get("SERPER_API_KEY", "")

# 5. [원복] 우측 상단 고정 원형 테마 토글
st.markdown('<div class="top-right-theme-area">', unsafe_allow_html=True)
toggle_label = "☀️" if is_dark else "🌙"
if st.button(toggle_label, key="main_theme_btn", help="테마 전환"):
    st.session_state.theme_mode = "light" if is_dark else "dark"
    st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# 6. 새로고침 로고
if img_box := img_base64:
    st.markdown(f"""
    <div class="logo-wrapper">
        <a href="/" target="_self" style="text-decoration:none;">
            <div class="logo-link">
                <img src="data:image/png;base64,{img_box}" alt="diyv Logo">
            </div>
        </a>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"<h1 style='text-align: center; color: {text_color}; margin-top: 50px;'><a href='/' target='_self' style='text-decoration:none; color:inherit;'>diyv</a></h1>", unsafe_allow_html=True)

st.write("")

# 7. 검색 콜백 함수 (Enter 입력 시 동작)
def trigger_search():
    val = st.session_state.get("search_bar_input", "").strip()
    if val:
        st.session_state.confirmed_query = val

# 검색창 영역 (Pill 박스 안에 인풋과 카메라 아이콘이 정돈되어 들어감)
search_cols = st.columns([11, 1])
with search_cols[0]:
    st.text_input(
        label="검색창",
        placeholder="화장품 이름, 성분, 가격 물어보기",
        label_visibility="collapsed",
        key="search_bar_input",
        on_change=trigger_search
    )

with search_cols[1]:
    st.markdown('<div class="inline-cam-btn">', unsafe_allow_html=True)
    if st.button("📷", key="search_cam_trigger", help="제품 사진으로 검색"):
        st.session_state.show_cam = not st.session_state.show_cam
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# 카메라 토글 시 나타나는 업로더
uploaded_image = None
if st.session_state.show_cam:
    st.write("")
    uploaded_image = st.file_uploader(
        "분석할 화장품 사진을 선택하세요", 
        type=["jpg", "jpeg", "png", "webp"],
        label_visibility="collapsed"
    )

# Serper 실시간 가격/정보 검색 함수
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

# 8. 백엔드 AI 팩트체크 파이프라인 (gemini-2.5-flash 표준 적용)
if uploaded_image:
    st.markdown("---")
    try:
        image = Image.open(uploaded_image)
        st.image(image, width=280, caption="스캔된 실물 제품 사진")
        
        if not gemini_api_key:
            st.error("⚠️ Streamlit Secrets에 GEMINI_API_KEY가 설정되지 않았습니다.")
        else:
            with st.spinner("🤖 [diyv] 비전 AI가 제품명을 식별 중입니다..."):
                genai.configure(api_key=gemini_api_key)
                model = genai.GenerativeModel('gemini-2.5-flash')
                extract_prompt = "이 화장품 사진에 적힌 브랜드 정식 명칭과 제품명을 정확하게 한 줄로 요약해줘."
                extract_res = model.generate_content([image, extract_prompt])
                identified_name = extract_res.text.strip()

            with st.spinner(f"🌐 [diyv] '{identified_name}' 공식몰 및 실거래 가격 데이터 조회 중..."):
                snippets = fetch_exact_price_and_product_info(identified_name)
                grounding = "\n".join(snippets) if snippets else "추가 웹 검색 결과 없음"

            with st.spinner("✨ [diyv] 공식 판매가 및 객관적 팩트 매트릭스 합성 중..."):
                prompt = f"""당신은 객관적이고 투명한 글로벌 뷰티 데이터 분석가 diyv(디브)입니다.
                제공된 이미지와 실시간 검색 데이터를 종합해 객관적인 팩트 매트릭스를 작성하세요.
                
                [실시간 검색 데이터]:
                {grounding}

                - **브랜드 및 제품명**: [정식 브랜드명 및 제품명]
                - **카테고리**: [skincare 또는 makeup]
                - **공식 판매가**: [정확한 원화 가격 명시]
                - **타겟 피부 타입**: [주요 타겟층]
                - **핵심 유효 성분 및 제형**: [성분 및 제형 스펙]
                - **가성비 및 안전도 평가**: [용량당 가성비 및 안전성 특징]"""

                res = model.generate_content([image, prompt])
                st.markdown("### 📋 diyv 공식 가격 기반 뷰티 팩트 분석 리포트")
                st.write(res.text)

                if snippets:
                    with st.expander("🔍 실시간 가격 및 웹 검색 출처"):
                        for s in snippets:
                            st.info(s)

    except Exception as e:
        st.error(f"이미지 분석 중 오류가 발생했습니다: {e}")

elif st.session_state.confirmed_query:
    st.markdown("---")
    query = st.session_state.confirmed_query
    
    if not gemini_api_key:
        st.error("⚠️ Streamlit Secrets에 GEMINI_API_KEY가 설정되지 않았습니다.")
    else:
        with st.spinner(f"🌐 [diyv] '{query}' 실시간 가격 데이터 및 웹 정보 검색 중..."):
            snippets = fetch_exact_price_and_product_info(query)
            grounding = "\n".join(snippets) if snippets else "추가 웹 검색 결과 없음"
            genai.configure(api_key=gemini_api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')

        with st.spinner("✨ [diyv] AI 팩트 매트릭스 리포트 생성 중..."):
            prompt = f"""당신은 객관적이고 투명한 글로벌 뷰티 데이터 분석가 diyv(디브)입니다.
            사용자가 입력한 검색어와 실시간 웹 검색 데이터를 바탕으로 객관적인 팩트 매트릭스를 생성해주세요.

            [사용자 검색어]: {query}
            [실시간 웹 검색 참고 데이터]:
            {grounding}

            - **브랜드 및 제품명**: [명칭]
            - **카테고리**: [스킨케어/메이크업 등]
            - **공식 판매가 및 가격대**: [정확한 원화 가격]
            - **핵심 유효 성분 및 제형**: [성분 분석]
            - **장점 및 가성비 평가**: [객관적 지표]
            - **주의 사항 및 권장 피부 타입**: [주의 성분 및 타겟]"""

            res = model.generate_content(prompt)
            st.success(f"✨ 검색 완료: **[{query}]**")
            st.markdown("### 📋 diyv 뷰티 팩트체크 리포트")
            st.write(res.text)

            if snippets:
                with st.expander("🔍 실시간 가격 및 웹 검색 출처"):
                    for s in snippets:
                        st.info(s)