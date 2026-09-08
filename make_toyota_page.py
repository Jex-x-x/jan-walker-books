#!/usr/bin/env python3
"""Страница /books/toyota/ — собирается из соседней tesla-страницы.

Почему не build.py: его словарь BOOKS отстал на шесть книг, а запуск перезаписал
бы index.html главной. Точечная пересборка одной страницы из проверенного соседа —
тот же приём, что в make_german_page.py.

Источник — уже собранная страница Теслы: у неё квадратный трейлер и правильный
набор A+ модулей, копировать проще, чем из german.
"""
import base64, io, re, shutil, subprocess
from pathlib import Path
from PIL import Image

KDP = Path('/Users/jexxx/autopapyrus-kdp')
DEPLOY = KDP / 'site' / '_deploy'
SRC = DEPLOY / 'books' / 'tesla' / 'index.html'
OUT = DEPLOY / 'books' / 'toyota'
SLUG = 'toyota'

PB, KIN = 'B0HJ5LVNKQ', 'B0HJ5JCGRW'
TITLE = TITLE_PLAIN = SHORT = 'Ultimate Toyota Challenge'
PITCH = ("The largest car company in the world began as a workshop that made machines for weaving "
         "cloth, and the man who founded it never learned to drive. The money that bought its way "
         "into cars came out of a loom patent sold to Lancashire in 1929. Ninety verified questions "
         "across ten themed parts — the best-seller nobody can draw from memory, the method everyone "
         "copied, the race it could not win, and the luxury car built in secret.")
DESC_META = ("The largest car company in the world began as a workshop that made machines for weaving "
             "cloth, and the man who founded it never learned to drive. Ninety verified questions, "
             "ten themed parts.")

PARTS = [
    ('Looms and Money.', 'A patent sold to Lancashire in 1929'),
    ('The Best-Seller.', 'The car nobody can draw from memory'),
    ('The Method.', 'Given away, and copied badly'),
    ('Goes Anywhere.', 'The name that belonged to somebody else'),
    ('The Hybrid.', 'Sold at a loss, on purpose'),
    ('The Race.', 'Won at last, after a great many tries'),
    ('Too Much Margin.', 'Iron blocks and the numbers people repeat'),
    ('Built in Secret.', 'Nine hundred prototype engines before launch'),
    ('The Biggest.', 'And the two worst years of them'),
    ('Odd Corners.', 'Hand-carved, and trimmed in wool'),
]

ALSO = [  # (href, короткое имя, путь к ebook-обложке)
    ('tesla',        'Ultimate Tesla Challenge', 'tesla/tesla-ebook-cover.jpg'),
    ('supra',        'Toyota Supra Trivia',      'supra/supra-ebook-cover.jpg'),
    ('tacoma',       'Toyota Tacoma Trivia',     'tacoma/tacoma-ebook-cover.jpg'),
    ('japanese-car', 'Japanese Cars Trivia',     'jdm/jdm-ebook-cover.jpg'),
]

QUIZ = dict(
    top='Q31  &middot;  PART 4  &middot;  GOES ANYWHERE',
    q='The first heavy four-wheel drive of 1951 wore a different name. Why was it renamed in 1954?',
    opts=['It tested badly abroad', 'Another firm owned it',
          'The engine changed', 'A printing constraint'],
    correct=1,
    reveal=("It went on sale in August 1951 as the Toyota Jeep BJ. Willys-Overland held the rights to "
            "that name, so in 1954 the vehicle was renamed Land Cruiser — a replacement that has "
            "outlived the argument by seventy years."),
)

# что заменяем в исходной странице
SRC_PITCH = ("The first car this company sold was a British sports car with the engine taken out, and "
             "the company nearly died before it built anything of its own. It borrowed $465 million "
             "from the American taxpayer and repaid the loan nine years early, with interest. Ninety "
             "verified questions across ten themed parts — the roadster, the saloon, the battery, the "
             "charging network built in secret, the tent in a car park and the car past the orbit of Mars.")
SRC_DESC = ("The first car this company sold was a British sports car with the engine taken out, and "
            "the company nearly died before it built anything of its own. Ninety verified questions, "
            "ten themed parts.")


def datauri(path, width, quality):
    im = Image.open(path).convert('RGB')
    im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, 'JPEG', quality=quality, optimize=True, progressive=True)
    return 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()


s = SRC.read_text()

# --- 1. картинки: герой 640 + четыре соседа 300 ---
blobs = list(re.finditer(r'data:image/jpeg;base64,[A-Za-z0-9+/=]+', s))
assert len(blobs) == 5, len(blobs)
new_blobs = [datauri(KDP / SLUG / f'{SLUG}-ebook-cover.jpg', 640, 82)]
new_blobs += [datauri(KDP / p, 300, 80) for _, _, p in ALSO]
for m, nb in zip(reversed(blobs), reversed(new_blobs)):
    s = s[:m.start()] + nb + s[m.end():]

# --- 2. видео: квадратный мастер, версионное имя по размеру, постер с 17.6 с ---
mp4 = KDP / 'video' / 'out' / f'{SLUG}-promo.mp4'
w, h = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
                       '-show_entries', 'stream=width,height', '-of', 'csv=p=0', str(mp4)],
                      capture_output=True, text=True).stdout.strip().split(',')[:2]
assert w == h, f'мастер не квадратный: {w}x{h}'
vdir = DEPLOY / 'video'
ver = mp4.stat().st_size
vname, pname = f'{SLUG}-promo-{ver}.mp4', f'{SLUG}-promo-{ver}-poster.jpg'
shutil.copy(mp4, vdir / vname)
shutil.copy(mp4, vdir / f'{SLUG}-promo.mp4')
subprocess.run(['ffmpeg', '-y', '-ss', '17.6', '-i', str(mp4), '-frames:v', '1', '-q:v', '4',
                str(vdir / pname), '-loglevel', 'error'], check=True)
s = s.replace('/video/tesla-promo-3586775-poster.jpg', f'/video/{pname}')
s = s.replace('/video/tesla-promo-3586775.mp4', f'/video/{vname}')

# --- 3. A+ модули 1,5,6 (модуль 4 «THE SERIES» со страниц снят — коммит 76d7156) ---
apd = DEPLOY / 'aplus' / SLUG
apd.mkdir(parents=True, exist_ok=True)
for n, key, wmax in [(1, 'hero', 970), (5, 'gift', 700), (6, 'author', 700)]:
    im = Image.open(KDP / 'aplus-batch' / 'out' / SLUG / f'module{n}_{key}.png').convert('RGB')
    if im.width > wmax:
        im = im.resize((wmax, round(im.height * wmax / im.width)), Image.LANCZOS)
    im.save(apd / f'{n}.jpg', 'JPEG', quality=82, optimize=True, progressive=True)
s = s.replace('/aplus/tesla/', f'/aplus/{SLUG}/')

# --- 4. «What's inside» ---
old_parts = re.search(r'<div class="parts">.*?</div></div>\n  </div>\n</section>', s, re.S).group(0)
rows = '\n'.join(
    f'<div class="part"><span class="num">{i:02d}</span><span><span class="pt">{t}</span> '
    f'<span class="ps">{sub}</span></span></div>'
    for i, (t, sub) in enumerate(PARTS, 1))
s = s.replace(old_parts, f'<div class="parts">{rows}</div>\n  </div>\n</section>')

# --- 5. «Try one on the house» ---
old_try = re.search(r'<div class="qtop">.*?</div>\n      </div>\n    </div>', s, re.S).group(0)
opts = '\n'.join(
    f'<button class="opt"><span class="tag">{"ABCD"[i]}</span><span>{o}</span></button>'
    for i, o in enumerate(QUIZ['opts']))
new_try = f'''<div class="qtop">{QUIZ['top']}</div>
      <div class="qbody">
        <div class="q">{QUIZ['q']}</div>
        <div class="opts" id="opts">{opts}</div>
        <div class="stamp" id="stamp"></div>
        <div class="reveal" id="reveal">{QUIZ['reveal']}<br><b>There are 89 more where that came from.</b> <a href="https://www.amazon.com/dp/{KIN}" target="_blank" rel="noopener">Get {SHORT} on Amazon &rarr;</a> or <a href="/#quiz">take the full entrance exam &rarr;</a></div>
      </div>
    </div>'''
s = s.replace(old_try, new_try)
s = s.replace('const CORRECT = 3;   // D — заявку на Model E заблокировал конкурент',
              f"const CORRECT = {QUIZ['correct']};   // B — имя принадлежало Willys-Overland")

# --- 6. тексты, ссылки, ASIN ---
# ASIN встречается не только в ссылках: блок отзывов держит его в переменной JS
s = s.replace('B0HJ3VFQWB', PB).replace('B0HHZRJR59', KIN)
s = s.replace('/books/tesla/', f'/books/{SLUG}/')
s = s.replace('/covers/tesla.jpg', f'/covers/{SLUG}.jpg')
s = s.replace('Ultimate Tesla Challenge', SHORT)
assert SRC_PITCH in s and SRC_DESC in s
s = s.replace(SRC_PITCH, PITCH).replace(SRC_DESC, DESC_META)

# --- 7. «Also on this shelf» — СТРОГО после блока 6 ---
old_also = re.search(r'<div class="also">.*?</div></a></div>', s, re.S).group(0)
cards = '\n'.join(
    f'<a href="/books/{sl}/"><img src="{nb}" alt="{nm} cover"><div class="t">{nm}</div></a>'
    for (sl, nm, _), nb in zip(ALSO, new_blobs[1:]))
s = s.replace(old_also, f'<div class="also">{cards}</div>')

# следов Теслы не должно остаться нигде, КРОМЕ карточки соседа
probe = re.sub(r'<div class="also">.*?</div>\n  </div>', '', s, flags=re.S)
probe = re.sub(r'data:image/\w+;base64,[A-Za-z0-9+/=]+', '', probe)
leftovers = re.findall(r'(?i)tesla|roadster|model e|falcon|B0HJ3VFQWB|B0HHZRJR59', probe)
assert not leftovers, f'остались следы tesla: {leftovers}'
OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'index.html').write_text(s)

cov = Image.open(KDP / SLUG / f'{SLUG}-ebook-cover.jpg').convert('RGB')
cov = cov.resize((1000, round(cov.height * 1000 / cov.width)), Image.LANCZOS)
cov.save(DEPLOY / 'covers' / f'{SLUG}.jpg', 'JPEG', quality=85, optimize=True)

print(f'books/{SLUG}/index.html  {len(s)/1e3:.0f} KB')
print('video', vname, pname)
print('aplus', sorted(p.name for p in apd.iterdir()))
