## Session Plan

### Task 1: 텔레그램 메시지 분할 전송 구현 (4096자 제한 대응)
Files: src/delivery/telegram_bot.py, tests/test_telegram_split.py
Description:
현재 `send_message()`는 단일 메시지로 전송하며 텔레그램 API 4096자 제한을 처리하지 않는다. 15개 이상 섹션이 포함된 일일 리포트는 거의 확실히 이 제한을 초과하여 발송이 실패한다.

구현:
- HTML 태그를 깨뜨리지 않는 안전한 메시지 분할 함수 `split_message(text, limit=4096)` 추가
- 분할 기준: `\n\n` (섹션 경계) 우선, 불가능 시 `\n` 기준으로 분할
- 각 파트가 4096자 이하가 되도록 보장
- `send_message()`가 분할된 파트를 순차 전송하도록 수정
- 테스트: 짧은 메시지(분할 불필요), 긴 메시지(다중 분할), 빈 줄 없는 긴 텍스트, 정확히 4096자 경계

### Task 2: 주간 추이 요약 섹션 추가
Files: src/analysis/weekly_summary.py, src/analysis/report.py, src/analysis/commentary.py, src/main.py, tests/test_weekly_summary.py, tests/test_report.py, tests/test_commentary.py, tests/test_main.py
Description:
투자자에게 일일 스냅샷만 제공하면 맥락이 부족하다. DB에 이미 signal_history 테이블과 daily_prices에 일별 이력이 저장되어 있으므로, 이를 활용한 주간 추이 요약을 추가한다.

구현:
- `src/analysis/weekly_summary.py` 신규 모듈:
  - 최근 5거래일 주가 데이터 + 시그널 이력 조회
  - 주간 수익률 (시가 대비 종가 변동%), 거래량 평균 대비 변화
  - 시그널 점수 변화 (5일 전 → 현재), 등급 전환 이벤트
  - 외국인 5일 순매수 누적
  - 주간 핵심 이벤트: 일중 변동폭 3% 이상인 날, 시그널 등급 변경일
- 리포트에 "📊 주간 요약" 섹션 추가 (종합 시그널 바로 아래)
- 코멘터리에 주간 흐름 한 줄 서술 추가
- main.py에서 주간 요약 분석 호출 후 리포트/코멘터리에 전달
- 테스트 작성: 주간 수익률 계산, 이벤트 식별, 데이터 부족 시 graceful 처리
