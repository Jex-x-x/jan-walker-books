#!/usr/bin/env python3
"""Главная: короткий анонс отдельной серии «Premium Editions» (сами карточки живут на /premium/, см. make_premium_pages.py).
Идемпотентно: заменяет свой блок. index.html правится точечно (build.py не гоняем)."""
import re
from pathlib import Path
PAGE = Path(__file__).parent / 'index.html'
TEASER = ['911', 'corvette', 'gwagon', 'supra', 'skyline']
s = PAGE.read_text()

s = re.sub(r'<section id="premium">.*?</section>\n\n', '', s, flags=re.S)
s = re.sub(r'const PREMIUM = \[.*?\];\nPREMIUM\.forEach[^\n]*\n', '', s, flags=re.S)
s = re.sub(r'<a href="#premium">[^<]*</a>\s*', '', s)
s = re.sub(r'<a href="/premium/">[^<]*</a>\s*', '', s)

imgs = ''.join(f'<a href="/premium/{x}/"><img src="/premium/img/{x}/front-s.jpg" alt="{x} premium hardcover cover" loading="lazy"></a>' for x in TEASER)
section = f'''<section id="premium">
  <style>#premium{{background:#16171a;color:#f2ece2}}#premium .sec-head h2,#premium .kicker{{color:#f2ece2}}#premium .kicker{{color:#cdba96}}#premium .sub{{color:#a8a196}}
  #premium .pt{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:22px;margin:34px 0 30px}}#premium .pt img{{width:100%;height:auto;display:block;border-radius:3px;box-shadow:0 24px 36px -20px #000}}
  #premium .go{{display:inline-block;font-family:var(--mono);font-size:13px;letter-spacing:.2em;text-transform:uppercase;text-decoration:none;color:#16171a;background:#cdba96;padding:14px 24px;border-radius:2px}}</style>
  <div class="wrap">
    <div class="sec-head rv">
      <div class="kicker">Trivia &amp; Fun Facts · Premium Editions</div>
      <h2>Premium Editions. A series of its own.</h2>
      <div class="rule"></div>
      <p class="sub">Full-colour matte hardcovers with a full-page image opening every part. Fourteen editions, each with its own page.</p>
    </div>
    <div class="pt">{imgs}</div>
    <a class="go" href="/premium/">See all Premium Editions &rarr;</a>
  </div>
</section>

'''
m = re.search(r'(<div class="shelf" id="car-shelf"></div>\s*</div>\s*</section>\n\n)', s)
assert m, 'нет секции garage'
s = s[:m.end()] + section + s[m.end():]
s = s.replace('<a href="#family">Family Table</a>', '<a href="/premium/">Premium</a>\n    <a href="#family">Family Table</a>', 1)
s = s.replace('<a href="#family">Family Table Books</a>', '<a href="/premium/">Trivia &amp; Fun Facts: Premium Editions</a>\n        <a href="#family">Family Table Books</a>', 1)
PAGE.write_text(s)
print('ok')
