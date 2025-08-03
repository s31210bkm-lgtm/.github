import os
import requests
import smtplib
import traceback
from email.mime.text import MIMEText
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# 프로젝트 루트에서 .env 로드
script_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(dotenv_path=os.path.join(script_dir, ".env"))

# 환경 변수 읽기
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
RECIPIENT  = os.getenv("RECIPIENT")

# 카테고리별 Naver SID1 매핑
CATEGORIES = {
    "사회": "102",
    "경제": "101",
    "IT/과학": "105",
    "생활": "103",
    "세계": "104"
}

# 가져올 기사 수
COUNT_PER_CATEGORY = 10


def fetch_naver_headlines(sid1, count=10):
    """Naver 뉴스 지정 카테고리에서 헤드라인 스크래핑"""
    url = f"https://news.naver.com/main/list.naver?mode=LSD&mid=shm&sid1={sid1}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")

    # 주요 헤드라인만 추출 (type06_headline 리스트)
    items = soup.select("ul.type06_headline li dt a")
    print(f"▶ 주요 헤드라인 수: {len(items)}")
    # type06_headline이 비어있으면 바로 빈 리스트 반환
    if not items:
        return []

    headlines = []
    for a in items:
        title = a.get_text(strip=True)
        if not title:
            img = a.find('img')
            title = img['alt'] if img and img.has_attr('alt') else None
        if not title:
            continue
        link = a.get("href", "")
        headlines.append({"title": title, "url": link})
        if len(headlines) >= count:
            break
    return headlines


def send_email(subject, body):
    """SMTP를 이용해 이메일 전송"""
    try:
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['Subject'] = subject
        msg['From'] = EMAIL_USER
        msg['To'] = RECIPIENT

        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT, timeout=10)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)
        server.quit()
        print("이메일 전송 성공")
    except Exception as e:
        print(f"[ERROR] 이메일 전송 실패: {e}")
        traceback.print_exc()


def create_and_send_summary():
    """카테고리별 Naver 뉴스 헤드라인 수집 후 이메일 전송 (중복 제거)"""
    seen_urls = set()
    body_lines = []
    for cat_name, sid1 in CATEGORIES.items():
        print(f"뉴스 스크래핑: {cat_name}")
        articles = fetch_naver_headlines(sid1, COUNT_PER_CATEGORY)
        print(f"{cat_name} 기사 수: {len(articles)}")
        body_lines.append(f"=== {cat_name} 뉴스 ===")
        count = 0
        for art in articles:
            if art['url'] in seen_urls:
                continue
            seen_urls.add(art['url'])
            body_lines.append(f"■ {art['title']}\n  URL: {art['url']}")
            count += 1
            if count >= COUNT_PER_CATEGORY:
                break
        if count == 0:
            body_lines.append("(해당 카테고리 뉴스 없음)")
        body_lines.append("")

    subject = f"오늘의 Naver 뉴스 하이라이트: {', '.join(CATEGORIES.keys())}"
    body = "\n".join(body_lines)
    print("이메일 전송 중...")
    send_email(subject, body)


if __name__ == "__main__":
    print("테스트 모드: 즉시 실행")
    create_and_send_summary()
