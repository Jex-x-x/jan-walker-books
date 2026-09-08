#!/usr/bin/env python3
"""Поставить книгу на полку главной страницы: карточка в массив CARS и обложка
в словарь COVERS. Новинка встаёт ПЕРВОЙ и забирает бейдж «New» у предыдущей.

build.py целиком не гоняется (его словарь BOOKS отстал на несколько книг и он
перезаписал бы index.html, потеряв правки руками) — правим страницу точечно.

  python3 add_shelf_book.py <slug> "<Название на карточке>" <ASIN> "<крючок>"
"""
import base64, io, re, sys
from pathlib import Path
from PIL import Image

DEPLOY = Path('/Users/jexxx/autopapyrus-kdp/site/_deploy')
KDP = Path('/Users/jexxx/autopapyrus-kdp')
slug, title, asin, hook = sys.argv[1:5]
page = DEPLOY / 'index.html'
s = page.read_text()

if f"slug: '{slug}'" in s:
    print(f'{slug} уже на полке — ничего не делаю'); sys.exit(0)

# --- обложка 420 px, как у остальных ---
im = Image.open(KDP / slug / f'{slug}-ebook-cover.jpg').convert('RGB')
im = im.resize((420, round(im.height * 420 / im.width)), Image.LANCZOS)
buf = io.BytesIO(); im.save(buf, 'JPEG', quality=82, optimize=True, progressive=True)
uri = 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()

# --- карточка первой, бейдж «New» переезжает на неё ---
head = "const CARS = [\n"
i = s.index(head) + len(head)
first_end = s.index('\n', i) + 1
first = s[i:first_end]
assert ", badge: 'New' }" in first, 'у первой карточки нет бейджа New — проверь порядок'
s = s[:i] + first.replace(", badge: 'New' }", ' }') + s[first_end:]

q = '"' if "'" in hook else "'"
card = (f"  {{ slug: '{slug}', t: '{title}', asin: '{asin}', "
        f"hook: {q}{hook}{q}, badge: 'New' }},\n")
i = s.index(head) + len(head)
s = s[:i] + card + s[i:]

# --- обложка в COVERS ---
k = s.index('const COVERS = {') + len('const COVERS = {')
s = s[:k] + f" '{slug}': '{uri}'," + s[k:]

# --- заголовок полки со СЛОВОМ-числом: он был вшит и протухал ---
# «The garage. Eighteen machines.» стояло на живой странице, когда книг было уже
# двадцать. Считаем карточки и переписываем число словом.
WORDS = {14:'Fourteen',15:'Fifteen',16:'Sixteen',17:'Seventeen',18:'Eighteen',19:'Nineteen',
         20:'Twenty',21:'Twenty-one',22:'Twenty-two',23:'Twenty-three',24:'Twenty-four',
         25:'Twenty-five',26:'Twenty-six',27:'Twenty-seven',28:'Twenty-eight'}
i = s.index('const CARS = ['); j = s.index('];', i)
n = s[i:j].count("slug: '")
m = re.search(r'<h2>The garage\. (\w+(?:-\w+)?) machines\.</h2>', s)
if m and WORDS.get(n) and m.group(1) != WORDS[n]:
    s = s[:m.start()] + f'<h2>The garage. {WORDS[n]} machines.</h2>' + s[m.end():]
    print(f'заголовок полки: {m.group(1)} → {WORDS[n]} machines')
elif not m:
    print('⚠ заголовок полки не найден — проверь руками')

page.write_text(s)
print(f"{slug}: карточка на полке первой, обложка {im.size[0]}×{im.size[1]}, "
      f"страница {len(s)/1e3:.0f} KB")
