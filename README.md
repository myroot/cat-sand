# 고양이 모래 가격 추적기 (Coupang Price Tracker)

**캐너디언 샌드 9kg 2개**의 쿠팡 가격을 주기적으로 확인하고, 가격 변동이 감지될 때 Github Issues에 가격을 기록하며, Telegram으로 알림을 보내는 자동화 툴입니다.

## 기능 요약

1. **GitHub Actions를 통한 주기적 실행**: 백그라운드 서버가 필요 없이 하루 4회 가격을 추적합니다.
2. **별도 DB 없음**: 가격 이력은 본 GitHub Repository의 **Issues 탭**에 작성되고, 댓글로 변동 내역이 추가됩니다.
3. **Telegram 알림**: 가격 변동이 발생하면 알림을 전송하며, 특히 3만원대로 하락 시 강조된 알림이 발송됩니다.

## 초기 설정 방법

### 1. 텔레그램 봇 생성 및 정보 확인
1. 텔레그램에서 **BotFather**를 검색하여 대화창을 엽니다.
2. `/newbot` 명령어를 전송하여 새로운 봇을 생성합니다. (봇 이름과 username 입력)
3. BotFather가 발급해주는 **봇 토큰(Bot Token)** 을 복사해 저장합니다.
4. 생성한 봇을 검색하여 채팅방에 들어가 시작(`/start`)합니다.
5. 브라우저에서 `https://api.telegram.org/bot<위에서받은토큰>/getUpdates`에 접속하여 `"chat":{"id": 숫자 }` 부분에 있는 자신의 **Chat ID**를 확인합니다.

### 2. GitHub 저장소 연동 및 Secrets 설정
1. 이 폴더(`/Volumes/SSD/dev/workspace/cat-sand`)를 사용자 본인의 GitHub Repository로 Push합니다.
2. 본인의 GitHub Repository에서 **Settings** > **Secrets and variables** > **Actions** 메뉴로 이동합니다.
3. `New repository secret` 버튼을 클릭하여 아래 2개의 시크릿을 등록합니다:
   - Name: `TELEGRAM_BOT_TOKEN` / Secret: (BotFather에게 받은 봇 토큰)
   - Name: `TELEGRAM_CHAT_ID` / Secret: (확인한 Chat ID 숫자)
4. (중요) 해당 레포지토리의 **Settings** -> **Actions** -> **General** -> **Workflow permissions** 에 들어가서 `Read and write permissions` 로 설정되어 있는지 확인합니다. (이슈 작성용)

### 3. 수동으로 테스트 실행하기
1. 저장소의 **Actions** 탭으로 들어갑니다.
2. 왼쪽 메뉴에서 **Coupang Price Tracker** 워크플로우를 선택합니다.
3. 우측에 보이는 **Run workflow** 드롭다운 버튼을 눌러 즉시 실행해 볼 수 있습니다.

### 주요 파일 설명
* `.github/workflows/price-tracker.yml`: 설정된 시간에 따라 파이썬 스크립트를 주기적으로 실행하는 메인 GitHub Action 설정 파일
* `scraper.py`: 실질적으로 쿠팡 페이지에서 가격을 수집하고 이슈를 업데이트 및 텔레그램 알림을 발송하는 파이썬 스크립트
* `requirements.txt`: 파이썬 실행시 필요한 외부 패키지 목록 (`curl_cffi`, `beautifulsoup4`, `requests`)
