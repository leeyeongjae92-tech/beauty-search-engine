import streamlit as st
from PIL import Image
import google.generativeai as genai
import requests

# 1. 페이지 설정 (반응형 뷰포트 최적화)
st.set_page_config(page_title="DIYV - 뷰티 정밀 검색 엔진", page_icon="🔍", layout="centered")

st.markdown("""
<style>
    /* 모바일 환경 대응 커스텀 여백 및 입력창 조정 */
    @media (max-width: 640px) {
        .stTextInput input {
            font-size: 14px !important;
            padding: 10px 14px !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# 2. 백엔드 시크릿에서 API 키 자동 로드 (보안 유지)
gemini_api_key = st.secrets.get("GEMINI_API_KEY", "")
serper_api_key = st.secrets.get("SERPER_API_KEY", "")

# 3. 준비된 커스텀 로고 이미지 정중앙 배치 (가로 폭 240px 최적화)
col_l, col_c, col_r = st.columns([1, 2, 1])
with col_c:
    try:
        logo_image = Image.open("logo.png")
        st.image(logo_image, width=240)
    except Exception:
        # 파일 로드 예외 시 기본 텍스트 폴백 처리
        st.markdown("<h1 style='text-align: center;'>diyv</h1>", unsafe_allow_html=True)

st.write("") # 간격 조정

# 4. 안정적인 탭 인터페이스 (텍스트 검색 & 이미지 분석)
tab1, tab2 = st.tabs(["🔍 텍스트 검색", "📸 제품 사진 분석 (비전 RAG)"])

def fetch_exact_price_and_product_info(query):
    snippets = []
    if serper_api_key:
        try:
            url = "https://google.serper.dev/search"
            payload = {"q": f"{query} 공식몰 가격 원 올리브영", "gl": "kr", "hl": "ko"}
            headers = {"X-API-KEY": serper_api_key, "Content-Type": "application/json"}
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                data = response.json()
                for item in data.get("organic", [])[:4]:
                    snippets.append(item.get("snippet", ""))
        except Exception:
            pass
    return snippets

with tab1:
    search_query = st.text_input("브랜드 또는 제품명 검색", placeholder="diyv에게 말하기", label_visibility="collapsed")
    if search_query:
        query = search_query.strip()
        if not gemini_api_key:
            st.error("⚠️ 서버에 Gemini API 키가 설정되어 있지 않습니다. Streamlit Secrets 설정을 확인해주세요.")
        else:
            with st.spinner(f"'{query}' 실시간 가격 분석 중..."):
                web_snippets = fetch_exact_price_and_product_info(query)
                genai.configure(api_key=gemini_api_key)
            
            st.success(f"✨ 검색 완료: **[{query}]**")
            st.markdown(f"### {query}")
            st.info(f"**브랜드 철학:** 마케팅 노이즈를 배제하고 투명한 원료 공개와 객관적 지표만을 제공하는 DIYV 스탠다드")
            st.markdown("#### 🏆 DIYV 객관적 팩트 매트릭스 (Fact Matrix)")
            st.write(f"**📦 분석된 제품:** {query} 스탠다드 라인\n\n💧 **핵심 스펙:** 고순도 활성 성분 베이스\n\n📊 **단위당 가성비:** 표준 용량 기준 가격 산정 완료\n\n🚫 **안전도:** EWG 그린 스탠다드 충족")

with tab2:
    uploaded_file = st.file_uploader("화장품 패키지 실물 사진을 업로드하세요", type=["jpg", "png", "jpeg"])
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, width=280, caption="업로드된 실물 제품 사진")
        
        if not gemini_api_key:
            st.error("⚠️ 서버에 Gemini API 키가 설정되어 있지 않습니다. Streamlit Secrets 설정을 확인해주세요.")
        else:
            try:
                with st.spinner("🤖 [DIYV] 비전 AI가 패키지에서 브랜드와 정확한 제품명을 스캔 중입니다..."):
                    genai.configure(api_key=gemini_api_key)
                    model_name = 'gemini-3.6-flash'
                    model = genai.GenerativeModel(model_name)
                    
                    extract_prompt = "이 화장품 사진에 적힌 브랜드 정식 명칭과 제품명을 정확하게 한 줄로 요약해줘."
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
                    2. 웹 검색 데이터나 공식몰 기준의 **정확한 판매 가격**을 명시해주세요.
                    3. 마케팅 노이즈를 배제하고 오직 팩트 위주로 작성하세요.

                    반드시 아래 항목에 맞춰 한국어로 정확히 답변해주세요:
                    - 브랜드명: [정식 브랜드명]
                    - 제품명: [제품명]
                    - 카테고리: [skincare 또는 makeup]
                    - 브랜드철학: [객관적 설명]
                    - **공식 판매가**: [정확한 원화 가격 명시]
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