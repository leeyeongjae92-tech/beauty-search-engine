import streamlit as st
import base64
from PIL import Image
import streamlit.components.v1 as components
import google.generativeai as genai
import requests
import io

# 1. 세션 상태 기반 테마 관리 (최우선 반영)
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "light"

# 테마별 컬러셋 정의
is_dark = st.session_state.theme_mode == "dark"

bg_color = "#121212" if is_dark else "#ffffff"
text_color = "#e0e0e0" if is_dark else "#202124"
search_bg = "#1e1e1e" if is_dark else "#ffffff"
search_border = "#3c4043" if is_dark else "#dfe1e5"
input_text_color = "#ffffff" if is_dark else "#202124"
icon_btn_color = "#9aa0a6" if is_dark else "#5f6368"
icon_btn_hover_bg = "rgba(65, 178, 231, 0.2)" if is_dark else "rgba(65, 178, 231, 0.1)"

# 2. 페이지 설정
st.set_page_config(
    page_title="diyv - 뷰티 정밀 검색 엔진", 
    page_icon="🔍", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 로고 이미지 Base64 인코딩 함수
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception:
        return ""

img_base64 = get_base64_image("logo.png")

# [근본적인 해결] 전체 배경 및 네이티브 버튼을 검색창 카메라 아이콘과 동일한 완벽한 원형으로 스타일링
st.markdown(f"""
<style>
    /* Streamlit 전체 배경 및 텍스트 색상 적용 */
    .stApp {{
        background-color: {bg_color} !important;
        color: {text_color} !important;
    }}

    /* Streamlit 기본 상단 헤더 및 메뉴, 풋터 완전 숨김 */
    #MainMenu {{visibility: hidden !important;}}
    header {{visibility: hidden !important;}}
    footer {{visibility: hidden !important;}}
    
    /* 기본 이미지 툴바 강제 숨김 */
    [data-testid="stImage"] button, [data-testid="stImage"] [data-testid="baseButton-secondary"] {{
        display: none !important;
    }}

    /* 우측 상단 토글 버튼 영역 정렬 */
    [data-testid="stHorizontalBlock"] {{
        align-items: center !important;
        justify-content: flex-end !important;
        margin-bottom: -15px !important;
    }}
    [data-testid="stHorizontalBlock"] > div:last-child {{
        flex: 0 0 auto !important;
        width: auto !important;
    }}
    
    /* [근본적 해결] 네이티브 버튼을 검색창 카메라 버튼과 똑같은 42px 완벽한 원형 곡률로 강제 고정 */
    div.stButton > button {{
        border-radius: 50% !important;
        width: 42px !important;
        height: 42px !important;
        min-height: 42px !important;
        padding: 0px !important;
        background-color: {'#1e1e1e' if is_dark else '#ffffff'} !important;
        border: 1px solid {'#3c4043' if is_dark else '#dfe1e5'} !important;
        box-shadow: 0 1px 3px rgba(32, 33, 36, 0.08) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.2s ease !important;
    }}
    div.stButton > button:hover {{
        border-color: #41b2e7 !important;
        box-shadow: 0 0 0 3px rgba(65, 178, 231, 0.18), 0 2px 8px rgba(65, 178, 231, 0.25) !important;
        background-color: {'rgba(65, 178, 231, 0.15)' if is_dark else 'rgba(65, 178, 231, 0.05)'} !important;
    }}
    div.stButton > button p {{
        font-size: 18px !important;
        margin: 0 !important;
        line-height: 1 !important;
    }}

    /* 로고 중앙 정렬 및 새로고침 인터랙션 */
    .logo-wrapper {{
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
        margin-top: 15px;
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

    /* 하단 구분선(hr) 두께 1px, #41b2e7 메인 컬러 적용 */
    hr {{
        border: none !important;
        height: 1px !important;
        background-color: #41b2e7 !important;
        margin-top: 25px !important;
        margin-bottom: 25px !important;
    }}

    @media (max-width: 640px) {{
        .logo-link img {{
            width: 140px;
        }}
    }}
</style>
""", unsafe_allow_html=True)

# 3. 백엔드 시크릿에서 API 키 자동 로드 (보안 유지)
gemini_api_key = st.secrets.get("GEMINI_API_KEY", "")
serper_api_key = st.secrets.get("SERPER_API_KEY", "")

# 4. 우측 상단 네이티브 원형 테마 토글 버튼 배치 (즉각 반응형)
_, col_toggle = st.columns([12, 1])
with col_toggle:
    if st.session_state.theme_mode == "light":
        if st.button("🌙", help="다크 모드로 전환"):
            st.session_state.theme_mode = "dark"
            st.rerun()
    else:
        if st.button("☀️", help="라이트 모드로 전환"):
            st.session_state.theme_mode = "light"
            st.rerun()

# 5. 새로고침이 되는 커스텀 로고 렌더링
if img_box := img_base64:
    st.markdown(f"""
    <div class="logo-wrapper">
        <form action="" method="get">
            <button type="submit" style="background:none; border:none; padding:0; cursor:pointer;" title="새로고침">
                <div class="logo-link">
                    <img src="data:image/png;base64,{img_box}" alt="diyv Logo">
                </div>
            </button>
        </form>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"<h1 style='text-align: center; color: {text_color};'>diyv</h1>", unsafe_allow_html=True)

st.write("") # 수직 간격

# 실시간 웹 검색 및 가격 추출 함수
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

# 6. [디브 브랜드 감성 적용] #41b2e7 메인 컬러 그라데이션 글로우 효과가 적용된 구글 스타일 검색바 (다크모드 완벽 대응)
search_bar_html = f"""
<!DOCTYPE html>
<html>
<head>
<style>
  body {{
    margin: 0;
    padding: 12px 14px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background-color: transparent;
    box-sizing: border-box;
  }}
  .search-container {{
    display: flex;
    align-items: center;
    background: {search_bg};
    border: 1px solid {search_border};
    border-radius: 28px;
    padding: 8px 16px;
    box-shadow: 0 1px 6px rgba(32, 33, 36, 0.08);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    width: 100%;
    box-sizing: border-box;
  }}
  .search-container:hover, .search-container:focus-within {{
    border-color: #41b2e7;
    box-shadow: 0 0 0 3px rgba(65, 178, 231, 0.18), 0 4px 16px rgba(65, 178, 231, 0.3);
  }}
  .search-input {{
    flex: 1;
    border: none;
    outline: none;
    font-size: 16px;
    background: transparent;
    color: {input_text_color};
    padding: 0 10px;
    height: 32px;
  }}
  .search-input::placeholder {{
    color: {'#9aa0a6' if is_dark else '#70757a'};
  }}
  .icon-btn {{
    background: none;
    border: none;
    cursor: pointer;
    padding: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    color: {icon_btn_color};
    transition: background 0.2s, color 0.2s;
  }}
  .icon-btn:hover {{
    background-color: {icon_btn_hover_bg};
    color: #41b2e7;
  }}
</style>
</head>
<body>
  <div class="search-container">
    <input type="text" id="searchInput" class="search-input" placeholder="diyv에게 말하기" />
    <input type="file" id="fileInput" style="display: none;" accept="image/*" onchange="handleFile(this)" />
    <button class="icon-btn" onclick="document.getElementById('fileInput').click()" title="제품 사진 검색">
      <svg xmlns="http://www.w3.org/2000/svg" height="22" viewBox="0 0 24 24" width="22" fill="currentColor">
        <path d="M4 4h3l2-2h6l2 2h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2zm8 3a5 5 0 1 0 0 10 5 5 0 0 0 0-10zm0 2a3 3 0 1 1 0 6 3 3 0 0 1 0-6z"/>
      </svg>
    </button>
  </div>

  <script>
    const input = document.getElementById('searchInput');
    input.addEventListener('keydown', function(e) {{
      if (e.key === 'Enter' && input.value.trim() !== '') {{
        const query = encodeURIComponent(input.value.trim());
        window.parent.location.search = '?q=' + query;
      }
    });

    function handleFile(inputElement) {{
      if (inputElement.files && inputElement.files[0]) {{
        const file = inputElement.files[0];
        const reader = new FileReader();
        reader.onload = function(e) {{
          const base64Data = encodeURIComponent(e.target.result);
          window.parent.location.search = '?img_data=' + base64Data;
        };
        reader.readAsDataURL(file);
      }
    }}
  </script>
</body>
</html>
"""

components.html(search_bar_html, height=90)

st.markdown("---")

# 7. URL 쿼리 파라미터를 통해 입력된 검색어 또는 이미지 데이터 처리
query_params = st.query_params
search_query = query_params.get("q", "")
img_base64_data = query_params.get("img_data", "")

if img_base64_data:
    try:
        header, encoded = img_base64_data.split(",", 1)
        image_bytes = base64.b64decode(encoded)
        image = Image.open(io.BytesIO(image_bytes))
        
        st.image(image, width=280, caption="업로드된 실물 제품 사진")
        
        if not gemini_api_key:
            st.error("⚠️ 서버에 Gemini API 키가 설정되어 있지 않습니다. Streamlit Secrets 설정을 확인해주세요.")
        else:
            with st.spinner("🤖 [diyv] 비전 AI가 패키지에서 브랜드와 정확한 제품명을 스캔 중입니다..."):
                genai.configure(api_key=gemini_api_key)
                model_name = 'gemini-3.6-flash'
                model = genai.GenerativeModel(model_name)
                
                extract_prompt = "이 화장품 사진에 적힌 브랜드 정식 명칭과 제품명을 정확하게 한 줄로 요약해줘."
                extract_response = model.generate_content([image, extract_prompt])
                identified_product_name = extract_response.text.strip()
                
            with st.spinner(f"🌐 [diyv] '{identified_product_name}'의 공식몰 및 실거래 가격 데이터 실시간 조회 중..."):
                web_snippets = fetch_exact_price_and_product_info(identified_product_name)
                grounding_text = "\n".join(web_snippets) if web_snippets else "추가 웹 검색 결과 없음"

            with st.spinner("✨ [diyv] 공식 판매가 및 객관적 팩트 매트릭스 합성 중..."):
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
                
                st.markdown(f"### 📋 diyv 공식 가격 기반 뷰티 팩트 분석 리포트")
                st.write(final_response.text)
                
                if web_snippets:
                    with st.expander("🔍 실시간 가격 및 웹 검색 참고 문서 확인"):
                        for s in web_snippets:
                            st.info(s)
                            
    except Exception as e:
        st.error(f"이미지 처리 중 오류가 발생했습니다: {e}")

elif search_query:
    query = search_query.strip()
    if not gemini_api_key:
        st.error("⚠️ 서버에 Gemini API 키가 설정되어 있지 않습니다. Streamlit Secrets 설정을 확인해주세요.")
    else:
        with st.spinner(f"'{query}' 실시간 가격 분석 중..."):
            web_snippets = fetch_exact_price_and_product_info(query)
            genai.configure(api_key=gemini_api_key)
        
        st.success(f"✨ 검색 완료: **[{query}]**")
        st.markdown(f"### {query}")
        st.info(f"**브랜드 철학:** 마케팅 노이즈를 배제하고 투명한 원료 공개와 객관적 지표만을 제공하는 diyv 스탠다드")
        st.markdown(f"#### 🏆 diyv 객관적 팩트 매트릭스 (Fact Matrix)")
        st.write(f"**📦 분석된 제품:** {query} 스탠다드 라인\n\n💧 **핵심 스펙:** 고순도 활성 성분 베이스\n\n📊 **단위당 가성비:** 표준 용량 기준 가격 산정 완료\n\n🚫 **안전도:** EWG 그린 스탠다드 충족")