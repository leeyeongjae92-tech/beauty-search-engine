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

# 2. 테마 모드 및 상태 세션 관리
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "light"

if "show_cam" not in st.session_state:
    st.session_state.show_cam = False

if "search_query" not in st.session_state:
    st.session_state.search_query = ""

is_dark = (st.session_state.theme_mode == "dark")

# 테마별 색상 매핑
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

# 3. CSS 주입 (기존 UI 100% 보존: 네이티브 요소를 기존 Pill 형태로 정확히 변환)
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

    /* 우측 상단 토글 버튼 래퍼 */
    div[data-testid="stButton"]:has(button[kind="secondary"]) {{
        position: fixed !important;
        top: 24px !important;
        right: 28px !important;
        z-index: 99999 !important;
        width: auto !important;
    }}

    /* 원형 테마 토글 버튼 스타일링 */
    div[data-testid="stButton"] button {{
        border-radius: 50% !important;
        width: 42px !important;
        height: 42px !important;
        min-width: 42px !important;
        max-width: 42px !important;
        min-height: 42px !important;
        max-height: 42px !important;
        aspect-ratio: 1 / 1 !important;
        padding: 0px !important;
        background-color: {card_bg} !important;
        border: 1px solid {card_border} !important;
        box-shadow: 0 1px 4px rgba(32, 33, 36, 0.08) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.2s ease !important;
        cursor: pointer !important;
    }}
    div[data-testid="stButton"] button:hover {{
        border-color: #41b2e7 !important;
        box-shadow: 0 0 0 3px {hover_glow}, 0 2px 8px {hover_shadow} !important;
        background-color: rgba(65, 178, 231, 0.1) !important;
    }}
    div[data-testid="stButton"] button p {{
        font-size: 18px !important;
        margin: 0 !important;
        padding: 0 !important;
        line-height: 1 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
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

    /* [핵심] 네이티브 st.text_input을 기존 검색바 디자인(Pill + 글로우)으로 100% 동일하게 매핑 */
    div[data-testid="stTextInput"] {{
        max-width: 720px !important;
        margin: 0 auto !important;
    }}
    div[data-testid="stTextInput"] > div {{
        background: {card_bg} !important;
        border: 1px solid {card_border} !important;
        border-radius: 28px !important;
        padding: 6px 48px 6px 20px !important;
        box-shadow: 0 1px 6px rgba(32, 33, 36, 0.08) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        height: 50px !important;
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

    /* 카메라 아이콘을 검색창 내부 우측 끝에 정확히 배치 */
    .cam-btn-overlay {{
        max-width: 720px;
        margin: -48px auto 0 auto;
        display: flex;
        justify-content: flex-end;
        padding-right: 14px;
        position: relative;
        z-index: 5;
        pointer-events: none;
    }}
    .cam-btn-overlay div[data-testid="stButton"] button {{
        pointer-events: auto !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        width: 36px !important;
        height: 36px !important;
        min-height: 36px !important;
        border-radius: 50% !important;
        color: {icon_color} !important;
        padding: 0 !important;
    }}
    .cam-btn-overlay div[data-testid="stButton"] button:hover {{
        background-color: {hover_glow} !important;
        color: #41b2e7 !important;
        border: none !important;
        box-shadow: none !important;
    }}

    /* 구분선 */
    hr {{
        border: none !important;
        height: 1px !important;
        background-color: #41b2e7 !important;
        margin-top: 35px !important;
        margin-bottom: 35px !important;
    }}

    @media (max-width: 640px) {{
        div[data-testid="stButton"]:has(button[kind="secondary"]) {{
            top: 16px !important;
            right: 16px !important;
        }}
        .logo-link img {{
            width: 140px;
        }}
    }}
</style>
"""
st.markdown(app_css, unsafe_allow_html=True)

# 4. 백엔드 시크릿에서 API 키 로드
gemini_api_key = st.secrets.get("GEMINI_API_KEY", "")
serper_api_key = st.secrets.get("SERPER_API_KEY", "")

# 5. 테마 토글 버튼 (네이티브 안정 렌더링)
toggle_icon = "☀️" if is_dark else "🌙"
help_text = "라이트 모드로 전환" if is_dark else "다크 모드로 전환"

if st.button(toggle_icon, key="diyv_theme_toggle_btn", help=help_text):
    st.session_state.theme_mode = "light" if is_dark else "dark"
    st.rerun()

# 6. 새로고침 로고 렌더링
def reset_home():
    st.session_state.search_query = ""
    st.session_state.show_cam = False

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

# 실시간 웹 검색 함수
def fetch_exact_price_and_product_info(query):
    snippets = []
    if serper_api_key:
        try:
            url = "https://google.serper.dev/search"
            payload = {"q": f"{query} 공식몰 가격 원 올리브영", "gl": "kr", "hl": "ko"}
            headers = {"X-API-KEY": serper_api_key, "Content-Type": "application/json"}
            response = requests.post(url, json=payload, headers=headers, timeout=6)
            if response.status_code == 200:
                data = response.json()
                for item in data.get("organic", [])[:4]:
                    snippets.append(item.get("snippet", ""))
        except Exception:
            pass
    return snippets

# 7. 네이티브 검색창 (엔터 입력 시 즉시 파이썬 백엔드로 전달)
def on_search_enter():
    st.session_state.search_query = st.session_state.text_input_val

st.text_input(
    label="검색창",
    placeholder="화장품 이름, 성분, 가격 물어보기",
    label_visibility="collapsed",
    key="text_input_val",
    on_change=on_search_enter
)

# 8. 검색창 우측 내부 카메라 버튼 오버레이
st.markdown('<div class="cam-btn-overlay">', unsafe_allow_html=True)
if st.button("📷", key="cam_modal_trigger", help="제품 사진 검색"):
    st.session_state.show_cam = not st.session_state.show_cam
    st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# 카메라 버튼 클릭 시 파일 업로더 출력
uploaded_image = None
if st.session_state.show_cam:
    st.write("")
    uploaded_image = st.file_uploader(
        "분석할 화장품 사진을 선택하세요", 
        type=["jpg", "jpeg", "png", "webp"],
        label_visibility="collapsed"
    )

# 9. 백엔드 AI 분석 파이프라인
if uploaded_image:
    st.markdown("---")
    try:
        image = Image.open(uploaded_image)
        st.image(image, width=280, caption="스캔된 실물 제품 사진")
        
        if not gemini_api_key:
            st.error("⚠️ 서버에 Gemini API 키가 설정되어 있지 않습니다.")
        else:
            with st.spinner("🤖 [diyv] 비전 AI가 패키지에서 브랜드와 제품명을 스캔 중입니다..."):
                genai.configure(api_key=gemini_api_key)
                model = genai.GenerativeModel('gemini-2.5-flash')
                extract_prompt = "이 화장품 사진에 적힌 브랜드 정식 명칭과 제품명을 정확하게 한 줄로 요약해줘."
                extract_response = model.generate_content([image, extract_prompt])
                identified_name = extract_response.text.strip()

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
                    with st.expander("🔍 실시간 가격 및 웹 검색 참고 문서 확인"):
                        for s in snippets:
                            st.info(s)

    except Exception as e:
        st.error(f"이미지 처리 중 오류가 발생했습니다: {e}")

elif st.session_state.search_query.strip():
    st.markdown("---")
    query = st.session_state.search_query.strip()
    
    if not gemini_api_key:
        st.error("⚠️ 서버에 Gemini API 키가 설정되어 있지 않습니다.")
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
                with st.expander("🔍 실시간 가격 및 웹 검색 참고 문서 확인"):
                    for s in snippets:
                        st.info(s)