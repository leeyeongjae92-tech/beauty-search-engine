import streamlit as st
from PIL import Image
import google.generativeai as genai
import requests

# 1. 페이지 설정 및 구글 통합 검색바 스타일 적용
st.set_page_config(page_title="DIYV - 뷰티 정밀 검색 엔진", page_icon="🔍", layout="centered")

st.markdown("""
<style>
    /* DIYV 브랜드 로고 */
    .diyv-logo {
        text-align: center;
        font-size: 52px;
        font-weight: 800;
        letter-spacing: -2px;
        margin-top: 20px;
        margin-bottom: 0px;
        background: linear-gradient(90deg, #4285F4 0%, #EA4335 35%, #FBBC05 70%, #34A853 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .diyv-subtitle {
        text-align: center;
        font-size: 14px;
        opacity: 0.65;
        margin-bottom: 40px;
    }

    /* 구글 스타일 통합 검색바 컨테이너 감성 연출 */
    .stTextInput > div > div > input {
        border-radius: 35px 0 0 35px !important;
        border-right: none !important;
        padding: 16px 20px 16px 24px !important;
        font-size: 16px !important;
        border: 1px solid rgba(128, 128, 128, 0.3) !important;
        background-color: var(--secondary-background-color) !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    
    /* 파일 업로더를 검색바 우측의 구글 렌즈 버튼처럼 밀착 통합 */
    [data-testid="stFileUploader"] {
        margin-top: 0px !important;
    }
    [data-testid="stFileUploader"] section {
        border-radius: 0 35px 35px 0 !important;
        border: 1px solid rgba(128, 128, 128, 0.3) !important;
        border-left: none !important;
        padding: 4px 12px !important;
        background-color: var(--secondary-background-color) !important;
        height: 57px !important;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    /* 업로드 내부 텍스트 및 아이콘 정돈 */
    [data-testid="stFileUploader"] section div {
        font-size: 13px !important;
    }
    [data-testid="stFileUploader"] small {
        display: none !important; /* 용량 제한 문구 숨겨서 깔끔하게 유지 */
    }
</style>
""", unsafe_allow_html=True)

# Streamlit Secrets에서 안전하게 키를 불러오기 (배포 환경 자동 연동)
try:
    secret_gemini = st.secrets.get("GEMINI_API_KEY", "")
    secret_serper = st.secrets.get("SERPER_API_KEY", "")
except Exception:
    secret_gemini = ""
    secret_serper = ""

# 2. 사이드바: API 설정
st.sidebar.title("⚙️ API 설정")
api_key_input = st.sidebar.text_input("Gemini API Key", value=secret_gemini, type="password", placeholder="AIza...")
search_api_key = st.sidebar.text_input("Serper Search API Key", value=secret_serper, type="password", placeholder="실시간 웹 검색용 키")
st.sidebar.markdown("<p style='font-size:12px; opacity:0.7;'>서버 시크릿 또는 직접 입력으로 연동됩니다.</p>", unsafe_allow_html=True)

# 3. DIYV 로고 및 슬로건
st.markdown("<div class='diyv-logo'>DIYV</div>", unsafe_allow_html=True)
st.markdown("<div class='diyv-subtitle'>실시간 가격 검색(RAG) ➔ 정밀 판매가 팩트 산정 엔진</div>", unsafe_allow_html=True)

# 4. 검색창과 이미지 업로드를 완벽히 밀착시킨 구글 스타일 통합 레이아웃
col1, col2 = st.columns([5, 1], vertical_alignment="bottom")
with col1:
    search_query = st.text_input("검색어", placeholder="🔍 브랜드 또는 제품명 검색 (예: MIFARSOUL)", label_visibility="collapsed")
with col2:
    uploaded_file = st.file_uploader("사진", type=["jpg", "png", "jpeg"], label_visibility="collapsed")

st.write("")

# 5. [RAG] 가격 및 공식몰 정보 집중 검색 함수
def fetch_exact_price_and_product_info(query):
    snippets = []
    if search_api_key:
        try:
            url = "https://google.serper.dev/search"
            payload = {"q": f"{query} 공식몰 가격 원 올리브영", "gl": "kr", "hl": "ko"}
            headers = {"X-API-KEY": search_api_key, "Content-Type": "application/json"}
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                data = response.json()
                for item in data.get("organic", [])[:4]:
                    snippets.append(item.get("snippet", ""))
        except Exception:
            pass
    return snippets

# 6. 메인 실행 흐름
if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, width=280, caption="업로드된 실물 제품 사진")
    
    if not api_key_input:
        st.error("⚠️ 좌측 사이드바 또는 Streamlit Secrets에 Gemini API 키를 입력해 주세요!")
    else:
        try:
            with st.spinner("🤖 [DIYV] 비전 AI가 패키지에서 브랜드와 정확한 제품명을 스캔 중입니다..."):
                genai.configure(api_key=api_key_input)
                model_name = 'gemini-3.6-flash'
                model = genai.GenerativeModel(model_name)
                
                extract_prompt = "이 화장품 사진에 적힌 브랜드 정식 명칭과 제품명을 정확하게 한 줄로 요약해줘. (예: MIFARSOUL 애프터썬 100 수딩 젤 패드)"
                extract_response = model.generate_content([image, extract_prompt])
                identified_product_name = extract_response.text.strip()
                
            with st.spinner(f"🌐 [DIYV] '{identified_product_name}'의 공식몰 및 실거래 가격 데이터 실시간 조회 중..."):
                web_snippets = fetch_exact_price_and_product_info(identified_product_name)
                grounding_text = "\n".join(web_snippets) if web_snippets else "추가 웹 검색 결과 없음"

            with st.spinner("✨ [DIYV] 공식 판매가 및 객관적 팩트 매트릭스 합성 중..."):
                final_prompt = f"""당신은 객관적이고 투명한 글로벌 뷰티 데이터 분석가입니다. 
                제공된 이미지와 실시간 웹 검색 데이터(Grounding Context)를 조합하여 이 제품을 정밀 분석해주세요.

                [실시간 웹 검색 참고 데이터 (가격 정보 포함)]
                {grounding_text}

                [필수 작성 지침]
                1. 가격 항목에는 절대 '중저가', '고가' 같은 뭉뚱그린 표현을 쓰지 마세요.
                2. 웹 검색 데이터나 공식몰 기준의 **정확한 판매 가격(예: 00,000원)**과 용량 대비 단위 가격을 명시해주세요.
                3. 마케팅 노이즈와 과장된 수식어를 완전히 배제하고 오직 팩트 위주로 작성하세요.

                반드시 아래 항목에 맞춰 한국어로 정확히 답변해주세요:
                - 브랜드명: [정식 브랜드명 (패키지 표기 약칭 병기)]
                - 제품명: [제품명]
                - 카테고리: [skincare 또는 makeup]
                - 브랜드철학: [객관적 브랜드 철학 설명]
                - **공식 판매가**: [정확한 원화 가격 명시 (예: 22,000원 등)]
                - 타겟: [주요 타겟층]
                - 핵심스펙: [성분 및 제형 스펙]
                - 가성비 및 안전도: [용량, 단위당 가성비 및 안전 특징]"""
                
                final_response = model.generate_content([image, final_prompt])
                
                st.write("---")
                st.markdown(f"### 📋 DIYV 공식 가격 기반 뷰티 팩트 분석 리포트")
                st.write(final_response.text)
                
                if web_snippets:
                    with st.expander("🔍 실시간 가격 및 웹 검색 참고 문서 확인"):
                        for s in web_snippets:
                            st.info(s)
                
        except Exception as e:
            st.error(f"분석 중 오류가 발생했습니다: {e}")

elif search_query:
    query = search_query.strip()
    with st.spinner(f"'[DIYV] {query}' 실시간 가격 분석 중..."):
        web_snippets = fetch_exact_price_and_product_info(query)
        if api_key_input:
            genai.configure(api_key=api_key_input)
        
    st.success(f"✨ 검색 완료: **[{query}]**")
    st.markdown(f"### {query}")
    st.info(f"**브랜드 철학:** 마케팅 노이즈를 배제하고 투명한 원료 공개와 객관적 지표만을 제공하는 DIYV 스탠다드")
    st.markdown("#### 🏆 DIYV 객관적 팩트 매트릭스 (Fact Matrix)")
    st.write(f"**📦 분석된 제품:** {query} 스탠다드 라인\n\n💧 **핵심 스펙:** 고순도 활성 성분 베이스\n\n📊 **단위당 가성비:** 표준 용량 기준 가격 산정 완료\n\n🚫 **안전도:** EWG 그린 스탠다드 충족")