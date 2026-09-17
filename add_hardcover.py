#!/usr/bin/env python3
"""Hardcover-издание на странице книги: кнопка в герое + блок «Also in hardcover» с премиальным A+.

Страницы правятся точечно (см. make_pajerosport_page.py), поэтому отдельный идемпотентный шаг:
повторный запуск заменяет свой блок и кнопку, а не дублирует.

  python3 add_hardcover.py pajerosport
"""
import re, sys
from pathlib import Path
from PIL import Image

KDP = Path('/Users/jexxx/autopapyrus-kdp')
DEPLOY = KDP / 'site' / '_deploy'

BOOKS = {   # slug на сайте: ASIN hardcover, папка премиального A+, название для alt
    'pajerosport': dict(asin='B0HK3BG73Y', aplus='pajerosport-hc', title='Pajero Sport Trivia &amp; Fun Facts'),
}

slug = sys.argv[1]
B = BOOKS[slug]
page = DEPLOY / 'books' / slug / 'index.html'
s = page.read_text()

apd = DEPLOY / 'aplus' / slug
for n, key in [(1, 'hero'), (3, 'sample')]:
    im = Image.open(KDP / 'aplus-batch' / 'out' / B['aplus'] / f'module{n}_{key}.png').convert('RGB')
    im.save(apd / f'hc-{n}.jpg', 'JPEG', quality=84, optimize=True, progressive=True)

url = f'https://www.amazon.com/dp/{B["asin"]}'
btn = f'<a class="btn ghost hc" href="{url}" target="_blank" rel="noopener">Hardcover</a>'
# стили .aplus-banners на странице привязаны к #aplus — свои, иначе на телефоне картинка 970 px распирает страницу
STYLE = ('<style>#hardcover .aplus-banners{max-width:900px;margin:40px auto 0;display:flex;flex-direction:column;gap:22px}'
         '#hardcover .aplus-banners img{width:100%;height:auto;display:block;border-radius:10px;border:1px solid var(--line);'
         'box-shadow:0 22px 44px -28px rgba(29,33,48,.42)}#hardcover .buy{margin-top:30px;display:flex;justify-content:center}</style>')
section = f'''<section id="hardcover">
  {STYLE}
  <div class="wrap">
    <div class="sec-head" style="text-align:center">
      <div class="kicker">Hardcover edition</div>
      <h2>Also in hardcover.</h2>
      <div class="rule" style="margin-left:auto;margin-right:auto"></div>
      <p class="sub" style="margin-left:auto;margin-right:auto">The same ninety verified questions, printed in full colour under a matte hard cover — and every part opens with its own full-page image.</p>
    </div>
    <div class="aplus-banners">
      <img src="/aplus/{slug}/hc-1.jpg" alt="{B['title']} hardcover — front cover and features" loading="lazy">
      <img src="/aplus/{slug}/hc-3.jpg" alt="{B['title']} hardcover — a full-page image opens each part" loading="lazy">
    </div>
    <div class="buy"><a class="btn primary" href="{url}" target="_blank" rel="noopener">Hardcover on Amazon</a></div>
  </div>
</section>

'''

# кнопка в герое — между Paperback и Kindle
s = re.sub(r'\s*<a class="btn ghost hc"[^>]*>[^<]*</a>', '', s)
m = re.search(r'(<div class="buy">\s*<a class="btn primary"[^>]*>[^<]*</a>)', s)
assert m, 'нет блока покупки в герое'
s = s[:m.end()] + '\n        ' + btn + s[m.end():]

# блок — после «A closer look», перед «What's inside»
s = re.sub(r'<section id="hardcover">.*?</section>\n\n', '', s, flags=re.S)
assert s.count('<section id="inside">') == 1
s = s.replace('<section id="inside">', section + '<section id="inside">')

assert s.count(url) == 2 and s.count('<section id="hardcover">') == 1
page.write_text(s)
print(page.relative_to(DEPLOY), 'OK', sorted(p.name for p in apd.iterdir()))
