## Session Plan

Day 31 (2026-04-21 15:30) — Volume Profile 리포트·코멘터리·파이프라인 통합 + 지지/저항 연동

### 자기 평가 요약

1068개 테스트 전부 통과, 커뮤니티 이슈 없음. 오전(11:30)에 volume_profile.py 모듈을 구축 완료했으나 파이프라인에 미통합 상태. report.py에 volume_profile 섹션 없음, commentary.py에 VP 해석 없음, main.py에서 VP 함수 호출 없음. 2단계 확장 패턴의 2단계(파이프라인 통합)가 남아 있다. 추가로, VP의 HVN은 기존 지지/저항 분석(이동평균·볼린저밴드·피보나치)에 네 번째 독립 방법론("수급 기반 레벨")으로 통합 가능하다.

### Task 1: Volume Profile 리포트·코멘터리·파이프라인 통합
Files: src/analysis/report.py, src/analysis/commentary.py, src/main.py, tests/test_volume_profile_integration.py (new)
Description: 오전에 구축한 volume_profile.py 모듈을 일일 파이프라인에 완전 통합한다. (1) main.py에서 OHLCV 데이터를 volume_profile 모듈에 전달하여 POC/VAH/VAL/HVN/LVN을 계산하고 결과를 리포트·코멘터리에 전달하는 배관 연결, (2) report.py에 Volume Profile 섹션 추가 — POC 가격, Value Area 범위, 현재가의 VA 내외 위치, 주요 HVN/LVN 표시를 HTML로 렌더링, (3) commentary.py에 Volume Profile 기반 자연어 해석 추가 — "현재가가 POC 위/아래", "VA 상단 돌파 시도 중" 등 맥락 설명, (4) generate_daily_report() 시그니처에 volume_profile 파라미터 추가. 테스트를 먼저 작성하여 통합 정합성을 검증한다. 2단계 확장 패턴 16회째 적용.

### Task 2: Volume Profile HVN을 지지/저항 분석에 통합 — 수급 기반 레벨 추가
Files: src/analysis/support_resistance.py, src/main.py, tests/test_support_resistance.py
Description: 기존 지지/저항 분석이 이동평균·볼린저밴드·피보나치 3가지 방법론을 사용하는데, Volume Profile의 HVN(High Volume Node)을 네 번째 독립 방법론으로 추가한다. HVN은 "실제로 많은 거래가 체결된 가격대"이므로 강한 지지/저항으로 작용하는 경향이 있다. (1) support_resistance.py의 analyze_support_resistance()가 volume_profile 결과(선택적 파라미터)를 받아, HVN 가격대를 지지/저항 후보에 포함시키고 "volume_based" 소스 태그를 부여, (2) main.py에서 VP 결과를 support_resistance 호출에 전달하는 배관 추가, (3) 기존 테스트에 VP 연동 케이스를 추가. 테스트를 먼저 작성한다.
