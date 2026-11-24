#!/usr/bin/env python3
"""Раздел «Premium Editions» на главной: полка твёрдых книг (отдельная серия KDP).
Идемпотентно: повторный запуск заменяет свой блок. Правит index.html точечно (build.py не гоняем).
Новая твёрдая = добавить slug в PREMIUM (карточка берёт название/крючок/обложку из CARS/COVERS)."""
import re
from pathlib import Path
PAGE = Path(__file__).parent / 'index.html'
PREMIUM = ['miata', 'miata2', 'supra', 'skyline', 'wrx', 'gwagon', 'pajerosport', 'tacoma',
           '4runner', 's2000', 'rx8', '300zx']
s = PAGE.read_text()

# убрать прошлую версию
s = re.sub(r'<section id="premium">.*?</section>\n\n', '', s, flags=re.S)
s = re.sub(r'\nconst PREMIUM = \[.*?\];\nPREMIUM\.forEach[^\n]*\n', '\n', s, flags=re.S)
s = re.sub(r'\s*<a href="#premium">Premium Editions</a>', '', s)
s = re.sub(r'\s*<a href="#premium">Trivia &amp; Fun Facts: Premium Editions</a>', '', s)

section = '''<section id="premium">
  <div class="wrap">
    <div class="sec-head rv">
      <div class="kicker">Trivia &amp; Fun Facts · Premium Editions</div>
      <h2>Premium Editions. Hardcover, full colour.</h2>
      <div class="rule"></div>
      <p class="sub">The same verified questions in a matte-finish hardcover, with a full-page colour image opening every part. A separate series, made to be given and kept.</p>
    </div>
    <div class="shelf" id="premium-shelf"></div>
  </div>
</section>

'''
m = re.search(r'(<div class="shelf" id="car-shelf"></div>\s*</div>\s*</section>\n\n)', s)
assert m, 'нет секции garage'
s = s[:m.end()] + section + s[m.end():]

js = f"\nconst PREMIUM = {PREMIUM!r};\nPREMIUM.forEach(sl => {{ const b = CARS.find(x => x.slug === sl); if (b) document.getElementById('premium-shelf').appendChild(card({{ ...b, badge: 'Hardcover' }})); }});\n"
m = re.search(r"CARS\.forEach\(b => document\.getElementById\('car-shelf'\)\.appendChild\(card\(b\)\)\);\n", s)
assert m
s = s[:m.end()] + js.lstrip('\n') + s[m.end():]

s = s.replace('<a href="#family">Family Table</a>', '<a href="#premium">Premium</a>\n    <a href="#family">Family Table</a>', 1)
s = s.replace('<a href="#family">Family Table Books</a>', '<a href="#premium">Trivia &amp; Fun Facts: Premium Editions</a>\n        <a href="#family">Family Table Books</a>', 1)
PAGE.write_text(s)
print('ok', len(PREMIUM), 'книг')
