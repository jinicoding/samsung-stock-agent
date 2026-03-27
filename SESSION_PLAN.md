## Session Plan

### Task 1: 스토캐스틱 오실레이터(%K, %D) 추가 및 시그널·리포트 통합
Files: src/analysis/technical.py, src/analysis/signal.py, src/analysis/report.py, src/analysis/commentary.py, tests/test_technical.py, tests/test_signal.py, tests/test_report.py, tests/test_commentary.py
Description: Stochastic Oscillator(%K 14일, %D 3일)를 기술적 분석 모듈에 추가한다. RSI와 함께 과매수/과매도 판단의 이중 확인 역할을 하며, 한국 투자자들이 가장 많이 참고하는 보조지표 중 하나다. (1) technical.py에 _stochastic() 함수 구현 — %K = (현재가 - N일 최저가) / (N일 최고가 - N일 최저가) × 100, %D = %K의 M일 SMA. (2) compute_technical_indicators()에 stoch_k, stoch_d 키 추가. (3) signal.py의 _score_technical()에 스토캐스틱 점수 반영 — %K 20 이하 매수, 80 이상 매도. (4) report.py에 스토캐스틱 섹션 추가 — %K/%D 값, 과매수/과매도/골든크로스/데드크로스 표시. (5) commentary.py에 스토캐스틱 과매수/과매도 경고 문구 추가. 테스트를 먼저 작성하고 구현한다.

### Task 2: 네이버 금융 뉴스 헤드라인 수집 및 키워드 감정 분석 모듈 구축
Files: src/data/news_fetcher.py (신규), src/analysis/news_sentiment.py (신규), tests/test_news_sentiment.py (신규), tests/test_news_fetcher.py (신규)
Description: 삼성전자 관련 뉴스 헤드라인을 수집하고 키워드 기반 감정을 분석하는 모듈을 구축한다. (1) src/data/news_fetcher.py — Naver 모바일 증권 API(https://m.stock.naver.com/api/news/stock/005930?pageSize=20)에서 최근 뉴스 헤드라인을 JSON으로 가져온다. 제목, 언론사, 날짜를 파싱하여 list[dict] 반환. (2) src/analysis/news_sentiment.py — 한국어 주식 뉴스에 특화된 긍정/부정 키워드 사전(예: 긍정=['실적 호조', '상향', '매수', '신고가', '수주'], 부정=['하락', '하향', '매도', '적자', '리스크'])으로 각 헤드라인의 감정 점수(-1~+1)를 산출하고, 전체 뉴스의 종합 감정 점수를 계산한다. LLM 호출 없이 규칙 기반으로 안정성 확보. (3) 테스트를 먼저 작성 — 키워드 매칭, 점수 계산, API 응답 파싱을 검증한다. 이 세션에서는 리포트/시그널 통합은 하지 않고 모듈 구축까지만 진행. 통합은 다음 세션에서.
