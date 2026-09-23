#!/usr/bin/env python3
"""Страница /books/civic/ — собирается из соседней s2000-страницы.

Почему не build.py: он брошен с 01.09.2026 и его прогон переписывает все 43 страницы
старыми шаблонами, откатывая три недели правок. Точечная пересборка одной страницы из
проверенного соседа — тот же приём, что в make_pajerosport_page.py.

Донор выбран не случайно: у S2000 нет блока hardcover и нет страницы источников,
то есть ровно та же комплектация, что нужна Civic. Адрес на сайте — civic, а папка
книги и каталог A+ называются civic-type-r / civic_type_r.

Ролик здесь ВЕРТИКАЛЬНЫЙ (9:16, фото-викторина), а у донора был квадратный, поэтому
video получает class="vertical" — правило под этот класс в странице уже есть.
"""
import base64, io, json, re, shutil, subprocess
from pathlib import Path
from PIL import Image

KDP = Path('/Users/jexxx/autopapyrus-kdp')
DEPLOY = KDP / 'site' / '_deploy'
SRC = DEPLOY / 'books' / 's2000' / 'index.html'
OUT = DEPLOY / 'books' / 'civic'
SLUG = 'civic'                 # адрес на сайте
BOOK = 'civic-type-r'          # папка книги и ролика
APLUS = 'civic_type_r'         # каталог модулей A+

PB, KIN = 'B0HKNQKDCH', 'B0HKP2C6M6'
TITLE_RAW = 'Civic Type R Trivia & Fun Facts'
TITLE = SHORT = 'Civic Type R Trivia &amp; Fun Facts'
PITCH = ("Honda put a racing badge on a family hatchback in 1997, sold it only in Japan, and left "
         "the rest of the world to work out what it had missed. Ninety verified questions across "
         "seven chassis codes — the shell welded twice, the British factory that built four "
         "generations of it, the saloon Japan still treats as the high point, and three "
         "N&uuml;rburgring records with an asterisk on every one.")

# те же названия, что в модуле A+ «Inside the book» (aplus-batch/configs/civic_type_r.py)
PARTS = [
    ('Before the R.', 'The badge started on a supercar'),
    ('EK9.', '185 PS from 1.6 litres, Japan only'),
    ('EP3.', 'The one Britain built for Japan'),
    ('The Split Years.', 'A saloon east, a hatchback west'),
    ('K20.', 'The engine that refused a turbo'),
    ('FK2.', 'The turbo arrives, and the +R button'),
    ('FK8.', 'The lap, the wing, and America'),
    ('FL5.', 'Back to Japan, and 330 PS'),
    ('Racing.', 'Three records, three asterisks'),
    ('What They Cost Now.', 'Grey imports and the red badge'),
]

ALSO = [  # (href, короткое имя, путь к ebook-обложке)
    ('s2000',   'Honda S2000 Trivia',      's2000/s2000-ebook-cover.jpg'),
    ('miata',   'Mazda MX-5 Miata Trivia', 'miata/miata-ebook-cover.jpg'),
    ('skyline', 'Skyline GT-R Trivia',     'skyline/skyline-ebook-cover.jpg'),
    ('supra',   'Toyota Supra Trivia',     'supra/supra-ebook-cover.jpg'),
]

# Q10 книги дословно. В A+ показан Q66 (круг на Нюрбургринге), на главной — вопрос про
# Суиндон, здесь третий: ни одна витрина не повторяет другую.
QUIZ = dict(
    top='Q10  &middot;  PART 2  &middot;  UNDER THE BONNET',
    q='How much power did the B16B in the EK9 Civic Type R produce?',
    opts=['160 PS', '185 PS', '200 PS', '215 PS'],
    correct=1,
    reveal=("185 PS at 8,200 rpm, from 1,595 cubic centimetres, without forced induction, in 1997. "
            "That is a little over 115 PS per litre &mdash; more than a contemporary Ferrari F355 "
            "managed. The torque figure was the price of it: 160 newton metres, arriving at "
            "7,500 rpm, which is where most engines of the period had stopped pulling."),
)

# что заменяем в исходной странице
SRC_TITLE = 'Honda S2000 Trivia'
SRC_PITCH = ("A company turned fifty and built itself a present with no automatic gearbox, no "
             "turbocharger and no glovebox. Ninety verified questions about the 9,000 rpm roadster "
             "— the two-litre engine that held the naturally aspirated power-per-litre record for a "
             "decade, and the day in 2009 when it stopped with no successor.")


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
new_blobs = [datauri(KDP / BOOK / f'{BOOK}-ebook-cover.jpg', 640, 82)]
new_blobs += [datauri(KDP / p, 300, 80) for _, _, p in ALSO]
for m, nb in zip(reversed(blobs), reversed(new_blobs)):
    s = s[:m.start()] + nb + s[m.end():]

# --- 2. видео: вертикальный мастер 9:16, версионное имя по размеру, постер с обложкой книги ---
mp4 = KDP / 'video' / 'out' / f'{BOOK[:5]}-quiz-vertical.mp4'   # civic-quiz-vertical.mp4
w, h = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
                       '-show_entries', 'stream=width,height', '-of', 'csv=p=0', str(mp4)],
                      capture_output=True, text=True).stdout.strip().split(',')[:2]
assert int(h) > int(w), f'мастер не вертикальный: {w}x{h}'
vdir = DEPLOY / 'video'
ver = mp4.stat().st_size
vname, pname = f'{SLUG}-promo-{ver}.mp4', f'{SLUG}-promo-{ver}-poster.jpg'
shutil.copy(mp4, vdir / vname)
shutil.copy(mp4, vdir / f'{SLUG}-promo.mp4')
# постер — финальный кадр с обложкой и плашкой «Available now on Amazon»
subprocess.run(['ffmpeg', '-y', '-ss', '23.6', '-i', str(mp4), '-frames:v', '1', '-q:v', '4',
                str(vdir / pname), '-loglevel', 'error'], check=True)
for old, new in (('/video/s2000-promo-916649-poster.jpg', f'/video/{pname}'),
                 ('/video/s2000-promo-916649.mp4', f'/video/{vname}')):
    assert old in s, old
    s = s.replace(old, new)
# донор был квадратным; 9:16 при ширине 560 вытянулся бы почти на 1000 px
assert '<video class="wide"' in s
s = s.replace('<video class="wide"', '<video class="vertical"')

# --- 3. A+ модули 1,5,6 (модуль 4 «THE SERIES» со страниц снят — коммит 76d7156) ---
apd = DEPLOY / 'aplus' / SLUG
apd.mkdir(parents=True, exist_ok=True)
for n, key, wmax in [(1, 'hero', 970), (5, 'gift', 700), (6, 'author', 700)]:
    im = Image.open(KDP / 'aplus-batch' / 'out' / APLUS / f'module{n}_{key}.png').convert('RGB')
    if im.width > wmax:
        im = im.resize((wmax, round(im.height * wmax / im.width)), Image.LANCZOS)
    im.save(apd / f'{n}.jpg', 'JPEG', quality=82, optimize=True, progressive=True)
s = s.replace('/aplus/s2000/', f'/aplus/{SLUG}/')

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
old_c = 'const CORRECT = 1;'
assert old_c in s
s = s.replace(old_c, f"const CORRECT = {QUIZ['correct']};   // B — 185 PS")

# --- 6. тексты, ссылки, ASIN ---
# ASIN встречается не только в ссылках: блок отзывов держит его в переменной JS
s = s.replace('B0HH844JS3', PB).replace('B0HH2689CJ', KIN)
s = s.replace('/books/s2000/', f'/books/{SLUG}/')
s = s.replace('/covers/s2000.jpg', f'/covers/{SLUG}.jpg')
# питч лежит четырежды: целиком в JSON-LD и в <p class="sub">, обрезанным — в meta и og
assert SRC_PITCH in s
s = s.replace(SRC_PITCH, PITCH)
cut = re.search(r'content="(A company turned fifty[^"]*)"', s)
assert cut, 'обрезанный питч не найден'
s = s.replace(cut.group(1), PITCH[:len(cut.group(1))].rsplit(' ', 1)[0])
# в JSON-LD сущности HTML не раскрываются — там название сырым, в разметке через &amp;
ld = re.search(r'<script type="application/ld\+json">(.*?)</script>', s, re.S)
s = s[:ld.start(1)] + ld.group(1).replace(f'"{SRC_TITLE}', f'"{TITLE_RAW.split(" Trivia")[0]} Trivia') + s[ld.end(1):]
s = s.replace('Honda S2000 Trivia &amp; Fun Facts', TITLE)
s = s.replace('Honda S2000 Trivia & Fun Facts', TITLE_RAW)
s = s.replace(SRC_TITLE, 'Civic Type R Trivia')

# --- 7. «Also on this shelf» — СТРОГО после блока 6 ---
old_also = re.search(r'<div class="also">.*?</div></a></div>', s, re.S).group(0)
cards = '\n'.join(
    f'<a href="/books/{sl}/"><img src="{nb}" alt="{nm} cover"><div class="t">{nm}</div></a>'
    for (sl, nm, _), nb in zip(ALSO, new_blobs[1:]))
s = s.replace(old_also, f'<div class="also">{cards}</div>')

# следов S2000 не должно остаться нигде, КРОМЕ карточек соседей
probe = re.sub(r'<div class="also">.*?</div>\n  </div>', '', s, flags=re.S)
probe = re.sub(r'data:image/\w+;base64,[A-Za-z0-9+/=]+', '', probe)
leftovers = re.findall(r'(?i)s2000|f20c|roadster|9,000 rpm|glovebox|B0HH844JS3|B0HH2689CJ', probe)
assert not leftovers, f'остались следы: {leftovers}'
json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', s, re.S).group(1))
OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'index.html').write_text(s)

cov = Image.open(KDP / BOOK / f'{BOOK}-ebook-cover.jpg').convert('RGB')
cov = cov.resize((1000, round(cov.height * 1000 / cov.width)), Image.LANCZOS)
cov.save(DEPLOY / 'covers' / f'{SLUG}.jpg', 'JPEG', quality=85, optimize=True)

print(f'books/{SLUG}/index.html  {len(s)/1e3:.0f} KB')
print('video', vname, pname)
print('aplus', sorted(p.name for p in apd.iterdir()))
