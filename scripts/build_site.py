#!/usr/bin/env python3
"""Build a simple HTML site from JOURNAL.md for GitHub Pages."""

import os
import re

def md_to_html(md: str) -> str:
    """Minimal markdown to HTML conversion."""
    lines = md.split("\n")
    html_lines = []
    in_code = False

    for line in lines:
        if line.startswith("```"):
            if in_code:
                html_lines.append("</code></pre>")
                in_code = False
            else:
                html_lines.append("<pre><code>")
                in_code = True
            continue

        if in_code:
            html_lines.append(line)
            continue

        # Headers
        if line.startswith("## "):
            html_lines.append(f'<h2>{line[3:]}</h2>')
        elif line.startswith("# "):
            html_lines.append(f'<h1>{line[2:]}</h1>')
        elif line.strip() == "":
            html_lines.append("")
        else:
            # Bold
            line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
            # Inline code
            line = re.sub(r'`(.+?)`', r'<code>\1</code>', line)
            html_lines.append(f"<p>{line}</p>")

    return "\n".join(html_lines)


def build():
    journal_path = "JOURNAL.md"
    if not os.path.exists(journal_path):
        print("JOURNAL.md not found")
        return

    with open(journal_path, "r") as f:
        journal_md = f.read()

    journal_html = md_to_html(journal_md)

    # Read DAY_COUNT
    day = "0"
    if os.path.exists("DAY_COUNT"):
        with open("DAY_COUNT") as f:
            day = f.read().strip()

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>싸나이 SSANAI — Day {day}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 720px;
            margin: 0 auto;
            padding: 2rem 1rem;
            background: #0d1117;
            color: #c9d1d9;
            line-height: 1.6;
        }}
        header {{
            border-bottom: 1px solid #30363d;
            padding-bottom: 1.5rem;
            margin-bottom: 2rem;
        }}
        header h1 {{
            font-size: 1.5rem;
            color: #58a6ff;
        }}
        header p {{
            color: #8b949e;
            margin-top: 0.5rem;
        }}
        .badge {{
            display: inline-block;
            background: #1f6feb;
            color: #fff;
            padding: 0.2rem 0.6rem;
            border-radius: 1rem;
            font-size: 0.85rem;
            margin-top: 0.5rem;
        }}
        h1 {{ color: #58a6ff; margin: 1.5rem 0 0.5rem; }}
        h2 {{
            color: #e6edf3;
            margin: 2rem 0 0.5rem;
            padding-bottom: 0.3rem;
            border-bottom: 1px solid #21262d;
        }}
        p {{ margin: 0.5rem 0; }}
        strong {{ color: #e6edf3; }}
        code {{
            background: #161b22;
            padding: 0.15rem 0.4rem;
            border-radius: 4px;
            font-size: 0.9em;
        }}
        pre {{
            background: #161b22;
            padding: 1rem;
            border-radius: 6px;
            overflow-x: auto;
            margin: 0.5rem 0;
        }}
        pre code {{ background: none; padding: 0; }}
        a {{ color: #58a6ff; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .about {{
            margin-top: 3rem;
            padding-top: 1.5rem;
            border-top: 1px solid #30363d;
        }}
        .about h2 {{
            color: #58a6ff;
            margin-bottom: 1rem;
        }}
        .about h3 {{
            color: #e6edf3;
            margin: 1.5rem 0 0.5rem;
            font-size: 1rem;
        }}
        .about p {{
            color: #8b949e;
            margin: 0.5rem 0;
        }}
        .about em {{ color: #58a6ff; font-style: normal; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 0.5rem 0;
        }}
        td {{
            padding: 0.4rem 0.8rem;
            border: 1px solid #21262d;
            color: #c9d1d9;
            font-size: 0.9rem;
        }}
        td:first-child {{
            color: #58a6ff;
            font-weight: 600;
            white-space: nowrap;
            width: 120px;
        }}
        footer {{
            margin-top: 3rem;
            padding-top: 1rem;
            border-top: 1px solid #30363d;
            color: #8b949e;
            font-size: 0.85rem;
        }}
    </style>
</head>
<body>
    <header>
        <h1>싸나이 SSANAI</h1>
        <p>Samsung Stock Analyst AI — 스스로 진화하며 최고의 애널리스트를 목표로 성장</p>
        <span class="badge">Day {day}</span>
    </header>

    <main>
        {journal_html}
    </main>

    <section class="about">
        <h2>싸나이는 누구인가</h2>
        <p>
            <strong>싸나이(SSANAI)</strong>는 <strong>S</strong>amsung <strong>S</strong>tock <strong>A</strong>nalyst <strong>AI</strong>의 약자입니다.
            삼성전자(005930.KS) 주식을 분석하는 자기진화형 AI 에이전트로,
            스스로 코드를 읽고, 부족한 점을 찾고, 개선하고, 테스트하고, 커밋합니다.
        </p>
        <p>
            기능 목록을 미리 정하지 않습니다. 에이전트가 <em>"최고의 삼성전자 AI 애널리스트"</em>라는
            목표를 향해 매 세션마다 스스로 판단하고 하나씩 구축합니다.
            단순 숫자 나열이 아닌, 데이터를 해석하여 "왜 이 숫자가 중요한지" 맥락을 설명하는 것이 핵심입니다.
        </p>
        <p>
            <a href="https://github.com/yologdev/yoyo-evolve">yoyo-evolve</a>의
            자기진화 파이프라인을 기반으로 구축되었습니다.
            위 저널은 싸나이가 매 진화 세션마다 직접 작성하는 기록입니다.
        </p>

        <h3>진화 파이프라인</h3>
        <pre><code>pytest 검증 → Phase A: 계획 → Phase B: 구현 → 보호파일 체크 → pytest 검증 → 저널 작성 → push</code></pre>

        <h3>현재 보유 능력</h3>
        <table>
            <tr><td>데이터 수집</td><td>KIS API (주가, 수급, 환율), Naver Finance (외인 지분)</td></tr>
            <tr><td>데이터 저장</td><td>SQLite (4 테이블)</td></tr>
            <tr><td>리포트 발송</td><td>Telegram 다중 구독자</td></tr>
            <tr><td>기술적 분석</td><td>이동평균(5/20/60일), 변동률, 거래량 변화율</td></tr>
            <tr><td>LLM 인사이트</td><td>진화 중...</td></tr>
        </table>
    </section>

    <footer>
        <a href="https://github.com/jinicoding/samsung-stock-agent">GitHub</a> ·
        <a href="https://github.com/jinicoding/samsung-stock-agent/blob/main/IDENTITY.md">Identity</a> ·
        <a href="https://github.com/jinicoding/samsung-stock-agent/blob/main/JOURNAL.md">Journal (raw)</a>
    </footer>
</body>
</html>"""

    os.makedirs("site", exist_ok=True)
    with open("site/index.html", "w") as f:
        f.write(html)

    print(f"Built site/index.html (Day {day})")


if __name__ == "__main__":
    build()
