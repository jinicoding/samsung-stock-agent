## Session Plan

### Task 1: 증권사 컨센서스 데이터 수집 모듈 구축 및 종합 시그널 통합

Files: src/data/consensus.py, src/analysis/signal.py, src/analysis/report.py, src/analysis/commentary.py, src/main.py, tests/test_consensus.py, tests/test_signal.py, tests/test_report.py, tests/test_commentary.py, tests/test_main.py

Description:
네이버 증권 통합 API(`m.stock.naver.com/api/stock/005930/integration`)에서 증권사 컨센서스 데이터를 수집하는 모듈을 구축한다.

수집 대상:
- `consensusInfo.priceTargetMean`: 컨센서스 목표주가 (현재 252,720원 vs 주가 ~180,000원)
- `consensusInfo.recommMean`: 투자의견 평균 (1=Strong Sell ~ 5=Strong Buy)
- `researches[]`: 최근 증권사 리포트 제목/브로커명/날짜 (상위 5건)

분석 로직:
- 목표가 괴리율(%) = (목표가 - 현재가) / 현재가 × 100
- 괴리율 기반 밸류에이션 판단: >30% 저평가, 10~30% 적정하단, -10~10% 적정, <-10% 고평가
- 투자의견 해석: ≥4.5 매수, 3.5~4.5 매수유지, 2.5~3.5 중립, <2.5 매도
- 리포트 제목 키워드로 증권가 톤 파악 (긍정/부정/중립)

통합:
- composite signal에 consensus 축 추가 (가중치 10%, 기존 축 비례 조정)
- 리포트에 "🏦 증권사 컨센서스" 섹션 추가 (목표가, 괴리율, 투자의견, 최근 리포트 Top 3)
- commentary에 컨센서스 관련 자연어 코멘트 추가
- main.py 파이프라인에 연결

테스트 우선 작성: 목표가 괴리율 계산, 투자의견 해석, 시그널 통합, 리포트 섹션, 코멘터리 반영.


### Task 2: 텔레그램 리포트 4096자 제한 관리

Files: src/analysis/report.py, tests/test_report.py

Description:
텔레그램 메시지 최대 길이(4096자)를 초과하면 리포트 전송이 실패한다. 리포트 섹션이 계속 늘어나고 있으므로 길이 관리 로직이 필요하다.

구현:
- `generate_daily_report()` 마지막에 `len(report)` 검사
- 4096자 초과 시, 우선순위 낮은 섹션부터 축소/제거:
  1. 시그널 정확도 상세 → 요약 1줄로 축소
  2. 상대강도 상세 → 1줄 요약으로 축소
  3. 지지/저항 상세 → 핵심 1줄만 남김
  4. 뉴스 헤드라인 → Top 3 → Top 1로 축소
  5. 추세전환 상세 → 등급만 표시
- 최종 길이가 4096 이하가 될 때까지 순차적으로 축소
- 축소 시 리포트 하단에 "(일부 섹션 축소됨)" 표시

테스트: 정상 길이 리포트는 변경 없음 확인, 초과 시 truncation 동작 확인, 최종 길이 ≤ 4096 보장.
