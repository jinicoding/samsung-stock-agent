## Session Plan

### Task 1: 주간 추이 요약 분석 모듈 구축
Files: src/analysis/weekly_summary.py, tests/test_weekly_summary.py
Description: 최근 5거래일의 데이터를 종합하여 주간 추이를 요약하는 분석 모듈을 구축한다. 기존 시그널이 "오늘의 스냅샷"만 보여주는 반면, 주간 요약은 "이번 주 전체 흐름"을 조감도로 제공한다. 구체적으로:
- 주간 시가/종가, 고가/저가, 등락률 계산
- 주간 거래량 합계 및 일평균 대비 비교
- 주간 외국인·기관 순매수 합계
- 시그널 점수 변화(주초→주말) 및 등급 변화
- 주간 요약 판정: "상승 전환", "하락 전환", "상승 지속", "하락 지속", "횡보"
- 테스트를 먼저 작성하고 구현한다.

### Task 2: 주간 요약을 리포트·코멘터리·파이프라인에 통합
Files: src/analysis/report.py, src/analysis/commentary.py, src/main.py, tests/test_report.py, tests/test_commentary.py
Description: Task 1에서 구축한 주간 요약 모듈을 텔레그램 리포트, 자연어 코멘터리, 일일 파이프라인에 통합한다. 리포트에 "📊 주간 요약" HTML 섹션을 추가하고, 코멘터리에 주간 흐름을 반영하는 자연어 문장을 생성한다. main.py에서 DB로부터 주간 데이터를 조회하여 주간 요약을 계산하고 리포트·코멘터리에 전달하는 흐름을 연결한다. 기존 테스트를 확장하여 주간 요약 섹션 렌더링과 코멘터리 생성을 검증한다.
