#!/usr/bin/env python3
"""Страницы /r/<slug>/ — короткая ссылка «оставить отзыв», которую печатаем в книге.

Зачем через свой домен, а не прямой ссылкой на Amazon: ASIN появляется только
ПОСЛЕ публикации, а QR-код печатается ДО неё. Ссылка на janwalkerbooks.com/r/<slug>
фиксируется на бумаге навсегда, а цель правится здесь в любой момент.

Витрин три, потому что оценки на Amazon раздельные по маркетплейсам, а 54 %
сентябрьских роялти дала Германия — вести всех на .com значит терять половину.

Запуск: python3 make_review_links.py    (ASIN берутся из books/<slug>/index.html)
"""
import re
from pathlib import Path

DEPLOY = Path(__file__).parent
STORES = [('amazon.com', 'www.amazon.com', 'United States'),
          ('amazon.de',  'www.amazon.de',  'Deutschland'),
          ('amazon.co.uk', 'www.amazon.co.uk', 'United Kingdom')]

TPL = """<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, follow">
<title>Leave a review — {title}</title>
<link rel="icon" href="/favicon.ico?v=2" sizes="any">
<style>
  :root {{ --ink:#14203a; --amber:#d4581f; --paper:#f7f3ec; --muted:#6b7280; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--paper); color:var(--ink);
         font:16px/1.55 Georgia,'Times New Roman',serif;
         display:flex; align-items:center; justify-content:center; min-height:100vh; padding:28px; }}
  .card {{ max-width:420px; width:100%; text-align:center; }}
  .kicker {{ font-family:ui-monospace,Menlo,monospace; font-size:11px; letter-spacing:.18em;
             text-transform:uppercase; color:var(--amber); }}
  h1 {{ font-size:30px; line-height:1.15; margin:10px 0 4px; }}
  .bk {{ font-size:15px; color:var(--muted); margin-bottom:20px; }}
  p {{ font-size:15px; margin:0 0 24px; }}
  a.btn {{ display:block; padding:12px 18px; margin:9px 0; border-radius:10px;
           text-decoration:none; font-family:ui-monospace,Menlo,monospace; }}
  a.btn b {{ display:block; font-size:14px; letter-spacing:.06em; font-weight:600; }}
  a.btn span {{ display:block; font-size:11px; letter-spacing:.14em; text-transform:uppercase;
                opacity:.72; margin-top:3px; }}
  a.first {{ background:var(--amber); color:#fff; }}
  a.rest {{ background:transparent; color:var(--ink); border:1px solid rgba(20,32,58,.25); }}
  .note {{ font-size:13px; color:var(--muted); margin-top:22px; }}
</style>
<div class="card">
  <div class="kicker">Jan Walker Books</div>
  <h1>Thank you for reading.</h1>
  <div class="bk">{title}</div>
  <p>One honest sentence about the part you enjoyed helps this book more
     than any amount of advertising. Found an error? That matters even more —
     corrections reach the next edition.</p>
{buttons}
  <div class="note">Pick the store where you bought the book — Amazon keeps reviews separate for each one.</div>
</div>
<script data-goatcounter="https://janwalkerbooks.goatcounter.com/count" async src="https://gc.zgo.at/count.js"></script>
</html>
"""


def main():
    made = []
    for d in sorted((DEPLOY / 'books').iterdir()):
        f = d / 'index.html'
        if not f.is_dir() and f.exists():
            s = f.read_text()
        else:
            continue
        m = re.search(r'class="btn primary" href="https://www\.amazon\.com/dp/(\w+)"', s)
        if not m:
            print('нет ASIN печатного:', d.name); continue
        asin = m.group(1)
        t = re.search(r'<title>(.*?) — Jan Walker</title>', s)
        title = (t.group(1) if t else d.name).replace('&amp;', '&')
        btns = []
        for i, (label, host, sub) in enumerate(STORES):
            cls = 'first' if i == 0 else 'rest'
            url = f'https://{host}/review/create-review?&asin={asin}'
            btns.append(f'  <a class="btn {cls}" href="{url}" rel="noopener"><b>{label}</b><span>{sub}</span></a>')
        out = DEPLOY / 'r' / d.name
        out.mkdir(parents=True, exist_ok=True)
        (out / 'index.html').write_text(TPL.format(title=title, buttons='\n'.join(btns)))
        made.append((d.name, asin))
    print(f'страниц /r/: {len(made)}')
    for s, a in made:
        print(f'  janwalkerbooks.com/r/{s}  →  {a}')


if __name__ == '__main__':
    main()
