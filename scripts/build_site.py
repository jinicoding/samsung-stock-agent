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
