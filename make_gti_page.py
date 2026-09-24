#!/usr/bin/env python3
"""Страница /books/gti/ — собирается из соседней civic-страницы.
Почему не build.py: он брошен с 01.09.2026, его прогон переписывает все страницы
старыми шаблонами и откатывает недели правок. Точечная пересборка одной страницы
из проверенного соседа — тот же приём, что в make_civic_page.py.
Донор выбран не случайно: у Civic та же комплектация — нет hardcover, нет страницы
источников, ролик ВЕРТИКАЛЬНЫЙ. Адрес на сайте, папка книги и каталог A+ у GTI
называются одинаково — gti.
"""
import base64, io, json, re, shutil, subprocess
from pathlib import Path
from PIL import Image

KDP = Path('/Users/jexxx/autopapyrus-kdp')
DEPLOY = KDP / 'site' / '_deploy'
SRC = DEPLOY / 'books' / 'civic' / 'index.html'
OUT = DEPLOY / 'books' / 'gti'
SLUG = 'gti'                   # адрес на сайте
BOOK = 'gti'                   # папка книги и ролика
APLUS = 'gti'                  # каталог модулей A+

PB, KIN = 'B0HKVWQPBF', 'B0GX2WLP2B'
TITLE_RAW = 'Golf GTI Trivia & Fun Facts'
TITLE = SHORT = 'Golf GTI Trivia &amp; Fun Facts'
PITCH = ("Nobody at Volkswagen asked for it. A handful of employees built a fast Golf in the margins "
         "of their real jobs, without a project number, and showed it to management once it already "
         "existed. Ninety verified questions across eight generations — the injection system with "
         "no computer in it, the supercharged four-wheel-drive homologation special, the twelve years "
         "when the badge stopped meaning the fast one, and a N&uuml;rburgring record taken from far "
         "more expensive machinery.")

# те же названия, что в модуле A+ «Inside the book» (aplus-batch/configs/civic_type_r.py)
PARTS = [
    ('The Car Nobody Ordered.', 'Built after hours, with no project number'),
    ('Mk1.', '1.6 litres, 110 PS, 810 kilograms'),
    ('Mk2.', 'Sixteen valves, four-wheel drive, a supercharger'),
    ('The Wilderness Years.', 'Twelve years when the badge meant less'),
    ('Mk5.', 'The comeback, and the suspension that did it'),
    ('One Engine Family.', 'EA888, from the Mk6 onwards'),
    ('The Special Ones.', 'Clubsport, Edition 30, Rallye Golf'),
    ('Racing and the Ring.', '7:49.21, and the two rivals who took it back'),
    ('What Owners Argue About.', 'The golf ball, the tartan, the red stripe'),
    ('What They Cost Now.', 'Why a 1976 hatchback outgrew the showroom'),
]

ALSO = [  # (href, короткое имя, путь к ebook-обложке)
    ('civic',  'Civic Type R Trivia',     'civic-type-r/civic-type-r-ebook-cover.jpg'),
    ('german', 'German Cars Trivia',      'german/german-ebook-cover.jpg'),
    ('miata',  'Mazda MX-5 Miata Trivia', 'miata/miata-ebook-cover.jpg'),
    ('supra',  'Toyota Supra Trivia',     'supra/supra-ebook-cover.jpg'),
]

# Q10 книги дословно. В A+ показан Q66 (круг на Нюрбургринге), на главной — вопрос про
# Суиндон, здесь третий: ни одна витрина не повторяет другую.
QUIZ = dict(
    top='Q8  &middot;  PART 1  &middot;  THE UNAUTHORISED CAR',
    q='The golf-ball gear knob and the tartan seat cloth were the work of a designer trained in which field?',
    opts=['Aircraft interiors', 'Furniture design', 'Textile engineering', 'Porcelain painting'],
    correct=3,
    reveal=("Porcelain painting. Gunhild Liljequist trained as a porcelain painter and worked in "
            "Volkswagen&rsquo;s interior design department, where she was responsible for the two "
            "details that people who have never driven a GTI can still describe. Neither was "
            "engineering, and both have outlived every technical specification the car was sold on."),
)

# что заменяем в исходной странице
SRC_TITLE = 'Civic Type R Trivia'
SRC_PITCH = ("Honda put a racing badge on a family hatchback in 1997, sold it only in Japan, and left "
             "the rest of the world to work out what it had missed. Ninety verified questions across "
             "seven chassis codes — the shell welded twice, the British factory that built four "
             "generations of it, the saloon Japan still treats as the high point, and three "
             "N&uuml;rburgring records with an asterisk on every one.")


def datauri(path, width, quality):
    im = Image.open(path).convert('RGB')
    im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, 'JPEG', quality=quality, optimize=True, progressive=True)
    return 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()


s = SRC.read_text()
DONOR_VER = re.search(r'/video/civic-promo-(\d+)\.mp4', s).group(1)

# --- 1. картинки: герой 640 + четыре соседа 300 ---
blobs = list(re.finditer(r'data:image/jpeg;base64,[A-Za-z0-9+/=]+', s))
assert len(blobs) == 5, len(blobs)
new_blobs = [datauri(KDP / BOOK / f'{BOOK}-ebook-cover.jpg', 640, 82)]
new_blobs += [datauri(KDP / p, 300, 80) for _, _, p in ALSO]
for m, nb in zip(reversed(blobs), reversed(new_blobs)):
    s = s[:m.start()] + nb + s[m.end():]

# --- 2. видео: вертикальный мастер 9:16, версионное имя по размеру, постер с обложкой книги ---
mp4 = KDP / 'video' / 'out' / f'{BOOK}-quiz-vertical.mp4'   # gti-quiz-vertical.mp4
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
for old, new in ((f'/video/civic-promo-{DONOR_VER}-poster.jpg', f'/video/{pname}'),
                 (f'/video/civic-promo-{DONOR_VER}.mp4', f'/video/{vname}')):
    assert old in s, old
    s = s.replace(old, new)
# донор был квадратным; 9:16 при ширине 560 вытянулся бы почти на 1000 px
assert '<video class="vertical"' in s   # донор уже вертикальный

# --- 3. A+ модули 1,5,6 (модуль 4 «THE SERIES» со страниц снят — коммит 76d7156) ---
apd = DEPLOY / 'aplus' / SLUG
apd.mkdir(parents=True, exist_ok=True)
for n, key, wmax in [(1, 'hero', 970), (5, 'gift', 700), (6, 'author', 700)]:
    im = Image.open(KDP / 'aplus-batch' / 'out' / APLUS / f'module{n}_{key}.png').convert('RGB')
    if im.width > wmax:
        im = im.resize((wmax, round(im.height * wmax / im.width)), Image.LANCZOS)
    im.save(apd / f'{n}.jpg', 'JPEG', quality=82, optimize=True, progressive=True)
s = s.replace('/aplus/civic/', f'/aplus/{SLUG}/')

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
s = s.replace(old_c, f"const CORRECT = {QUIZ['correct']};   // D — porcelain painting")

# --- 6. тексты, ссылки, ASIN ---
# ASIN встречается не только в ссылках: блок отзывов держит его в переменной JS
s = s.replace('B0HKNQKDCH', PB).replace('B0HKP2C6M6', KIN)
s = s.replace('/books/civic/', f'/books/{SLUG}/')
s = s.replace('/covers/civic.jpg', f'/covers/{SLUG}.jpg')
# питч лежит четырежды: целиком в JSON-LD и в <p class="sub">, обрезанным — в meta и og
assert SRC_PITCH in s
s = s.replace(SRC_PITCH, PITCH)
cut = re.search(r'content="(Honda put a racing badge[^"]*)"', s)
assert cut, 'обрезанный питч не найден'
s = s.replace(cut.group(1), PITCH[:len(cut.group(1))].rsplit(' ', 1)[0])
# в JSON-LD сущности HTML не раскрываются — там название сырым, в разметке через &amp;
ld = re.search(r'<script type="application/ld\+json">(.*?)</script>', s, re.S)
s = s[:ld.start(1)] + ld.group(1).replace(f'"{SRC_TITLE}', f'"{TITLE_RAW.split(" Trivia")[0]} Trivia') + s[ld.end(1):]
s = s.replace('Civic Type R Trivia &amp; Fun Facts', TITLE)
s = s.replace('Civic Type R Trivia & Fun Facts', TITLE_RAW)
s = s.replace(SRC_TITLE, 'Golf GTI Trivia')

# --- 7. «Also on this shelf» — СТРОГО после блока 6 ---
old_also = re.search(r'<div class="also">.*?</div></a></div>', s, re.S).group(0)
cards = '\n'.join(
    f'<a href="/books/{sl}/"><img src="{nb}" alt="{nm} cover"><div class="t">{nm}</div></a>'
    for (sl, nm, _), nb in zip(ALSO, new_blobs[1:]))
s = s.replace(old_also, f'<div class="also">{cards}</div>')

# следов S2000 не должно остаться нигде, КРОМЕ карточек соседей
probe = re.sub(r'<div class="also">.*?</div>\n  </div>', '', s, flags=re.S)
probe = re.sub(r'data:image/\w+;base64,[A-Za-z0-9+/=]+', '', probe)
# коды кузовов ищем со ГРАНИЦАМИ СЛОВА: без них «FK8» находится внутри base64
leftovers = re.findall(r'(?i)\b(?:civic|type r|honda|swindon)\b|\b(?:EK9|EP3|FD2|FK8|FL5)\b|B0HKNQKDCH|B0HKP2C6M6', probe)
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
