#!/usr/bin/env python3
"""Страница книги «скоро в продаже» → страница вышедшей книги.

Обратная операция к make_soon_page.py: возвращает кнопки покупки с реальными
ASIN, подпись под ними и секцию отзывов, которую make_soon_page убирал (без
ASIN ссылка на отзыв была битой).

    python3 make_live_page.py <slug> <paperback ASIN> <kindle ASIN>
"""
import re
import sys
from pathlib import Path

slug, pb_asin, kdl_asin = sys.argv[1], sys.argv[2], sys.argv[3]
page = Path('books') / slug / 'index.html'
s = page.read_text()

# 1. кнопки: заглушки «скоро» → ссылки на Amazon
soon = re.search(
    r'<span class="btn primary" style="cursor:default">[^<]*</span>\s*'
    r'<span class="btn ghost" style="cursor:default">[^<]*</span>', s)
assert soon, 'блок «скоро» не найден — страница уже живая?'
s = s[:soon.start()] + (
    f'<a class="btn primary" href="https://www.amazon.com/dp/{pb_asin}" target="_blank" rel="noopener">Paperback on Amazon</a>\n'
    f'        <a class="btn ghost" href="https://www.amazon.com/dp/{kdl_asin}" target="_blank" rel="noopener">Kindle edition</a>'
) + s[soon.end():]

# 2. подпись под кнопками — как у вышедших книг серии
note = 'Printed and proofread, in the last checks before release · paperback and Kindle, worldwide from Amazon'
assert note in s, 'подпись «скоро» не найдена'
s = s.replace(note, 'Ships worldwide from Amazon · Great as a gift')

# 3. хвост карточки вопроса
s = s.replace('Coming soon on Amazon — or <a href="/#quiz">',
              f'<a href="https://www.amazon.com/dp/{pb_asin}" target="_blank" rel="noopener">Get the book</a> — or <a href="/#quiz">')

page.write_text(s)
left = s.count('Coming soon')
print(f'{slug}: paperback {pb_asin}, kindle {kdl_asin}, осталось «Coming soon»: {left}')
