import requests
from bs4 import BeautifulSoup

print("데이터 수집을 시작합니다...")

# 1. 타겟 주소 (스킨1004 센텔라 앰플)
url = "https://www.oliveyoung.co.kr/store/goods/getGoodsDetail.do?goodsNo=A000000187424"

# 2. 강력한 위장술 (실제 크롬 브라우저가 보내는 정보)
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.oliveyoung.co.kr/"
}

# 접속 시도 (올리브영)
response = requests.get(url, headers=headers)
print(f"서버 응답 코드: {response.status_code} (200이 나오면 통과!)")

if response.status_code == 200:
    soup = BeautifulSoup(response.text, "html.parser")
    title_tag = soup.find("meta", property="og:title")
    print("✅ 올리브영 방패 뚫기 성공!")
    if title_tag: print(f"👉 상품명: {title_tag['content']}")
else:
    print("❌ 올리브영 보안이 너무 강력해서 위장술을 간파했습니다.")
    print("💡 이럴 때는 차단이 없는 브랜드 공식 홈페이지로 타겟을 우회합니다.")
    
    # [플랜 B] 올바른 공식 홈페이지 주소(skin1004korea.com)로 변경
    print("\n[플랜 B] 브랜드 공식 홈페이지 데이터 수집 중...")
    url_b = "https://skin1004korea.com/"
    res_b = requests.get(url_b, headers=headers)
    
    soup_b = BeautifulSoup(res_b.text, "html.parser")
    title_b = soup_b.find("title")
    
    if title_b:
        print("-" * 30)
        print(f"✅ 공식 홈페이지 우회 성공!")
        print(f"👉 가져온 데이터(타이틀): [{title_b.text.strip()}]")
        print("-" * 30)