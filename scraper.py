import os
import re
from datetime import datetime
from curl_cffi import requests as cffi_requests
import requests
from bs4 import BeautifulSoup

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
GITHUB_REPOSITORY = os.environ.get('GITHUB_REPOSITORY')
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

PRODUCT_URL = "https://www.coupang.com/vp/products/7151451350"
ISSUE_TITLE = "캐너디언 샌드 9kg 2개 가격 추적 (Cat Sand Price History)"

def get_product_price():
    # 쿠팡의 차단 정책을 우회하기 위해 curl_cffi의 chrome impersonation 기능 사용
    response = cffi_requests.get(PRODUCT_URL, impersonate="chrome110", timeout=15)
    
    if response.status_code != 200:
        raise Exception(f"페이지 로드 실패: {response.status_code}")
        
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 쿠팡의 다양한 가격 표시 클래스 시도
    price_element = soup.select_one('span.total-price > strong')
    if not price_element:
        price_element = soup.select_one('.prod-price .total-price strong')
    if not price_element:
        price_element = soup.select_one('.price-value')
        
    if not price_element:
        raise Exception("페이지에서 가격 요소를 찾을 수 없습니다. (구조 변경 또는 차단 의심)")
        
    price_str = price_element.text.strip().replace(',', '')
    price_match = re.search(r'\d+', price_str)
    
    if not price_match:
        raise Exception(f"가격을 파싱할 수 없습니다: {price_str}")
        
    return int(price_match.group())

def get_or_create_issue():
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    api_url = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/issues"
    
    response = requests.get(api_url, headers=headers, params={"state": "open"})
    if response.status_code != 200:
        raise Exception(f"이슈 목록 조회 실패: {response.status_code} - {response.text}")
    issues = response.json()
    
    for issue in issues:
        if issue.get('title') == ISSUE_TITLE:
            return issue
            
    # 존재하지 않으면 새로 생성
    data = {"title": ISSUE_TITLE, "body": f"이 이슈는 {PRODUCT_URL} 의 가격 변동을 기록합니다. 댓글을 통해 가격 변화가 저장됩니다."}
    response = requests.post(api_url, headers=headers, json=data)
    if response.status_code != 201:
        raise Exception(f"이슈 생성 실패: {response.status_code} - {response.text}")
    return response.json()

def get_last_price(issue):
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    comments_url = issue['comments_url']
    response = requests.get(comments_url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"코멘트 조회 실패: {response.status_code} - {response.text}")
    
    comments = response.json()
    if not comments:
        return None
        
    # 마지막 코멘트에서 가격 추출
    last_comment = comments[-1]['body']
    match = re.search(r'가격:\s*(\d+)원', last_comment)
    if match:
        return int(match.group(1))
    return None

def add_price_comment(issue, current_price):
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    comments_url = issue['comments_url']
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    body = f"[{now_str}] 가격: {current_price}원"
    response = requests.post(comments_url, headers=headers, json={"body": body})
    if response.status_code != 201:
        raise Exception(f"코멘트 등록 실패: {response.status_code} - {response.text}")

def send_telegram_message(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("텔레그램 토큰 또는 채팅방 ID가 설정되지 않았습니다. 메시지 전송을 건너뜁니다.")
        return
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    response = requests.post(url, json=payload)
    if not response.ok:
        print(f"텔레그램 메시지 전송 실패: {response.status_code} - {response.text}")

def main():
    if not GITHUB_TOKEN or not GITHUB_REPOSITORY:
        print("경고: GITHUB_TOKEN이나 GITHUB_REPOSITORY 환경변수가 없습니다. (로컬 테스트 모드일 수 있습니다.)")

    try:
        current_price = get_product_price()
        print(f"현재 수집된 가격: {current_price}원")
        
        if not GITHUB_TOKEN:
            return  # GitHub 토큰이 없으면 이슈 업데이트 및 텔레그램 진행 안함
            
        issue = get_or_create_issue()
        last_price = get_last_price(issue)
        
        if last_price:
            print(f"이슈에 기록된 이전 가격: {last_price}원")
        else:
            print("이전 기록이 없습니다.")
        
        # 가격이 변경되었거나, 최초 기록인 경우 모두 커멘트 및 알림 기록
        if last_price is None or last_price != current_price:
            print("가격 변동 (또는 최초 기록) 이 감지되었습니다! 이슈 업데이트를 진행합니다...")
            add_price_comment(issue, current_price)
            
            diff_str = ""
            if last_price:
                diff = current_price - last_price
                if diff > 0:
                    diff_str = f"(+{diff:,}원 🔺)"
                else:
                    diff_str = f"({diff:,}원 🔻)"
            else:
                diff_str = "(최초 기록)"
                
            msg = f"🐈 캐너디언 샌드 가격 변동 알림!\n\n현재 가격: {current_price:,}원 {diff_str}\n링크: {PRODUCT_URL}"
            
            # 3만원대(혹은 그 이하)로 진입/유지 중인 경우 강조 메시지 추가
            if current_price < 40000:
                msg = f"🎉 3만원대(또는 그 이하) 할인 중!\n\n" + msg
            
            send_telegram_message(msg)
                
        else:
            print("가격이 기존과 동일합니다. 아무 작업도 수행하지 않습니다.")
            
    except Exception as e:
        print(f"수집 중 오류 발생: {e}")
        # 오류 시 GitHub Actions의 로그에서 확인되도록 함. (필요시 알림 추가 가능)

if __name__ == "__main__":
    main()
