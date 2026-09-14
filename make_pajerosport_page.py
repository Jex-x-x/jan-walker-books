#!/usr/bin/env python3
"""Страница /books/pajerosport/ — собирается из соседней toyota-страницы.

Почему не build.py: его словарь BOOKS отстал, а запуск перезаписал бы index.html
главной. Точечная пересборка одной страницы из проверенного соседа — тот же приём,
что в make_toyota_page.py.

Адрес на сайте — pajerosport (на него ведут QR и строка источников в книге), а папка
книги — pajerosport-classic: 14.09.2026 упаковку «Ultimate Pajero Sport Challenge»
заменили классической, файлы лежат в копии. Обложку, ролик и A+ берём из копии.
"""
import base64, io, json, re, shutil, subprocess
from pathlib import Path
from PIL import Image

KDP = Path('/Users/jexxx/autopapyrus-kdp')
DEPLOY = KDP / 'site' / '_deploy'
SRC = DEPLOY / 'books' / 'toyota' / 'index.html'
OUT = DEPLOY / 'books' / 'pajerosport'
SLUG = 'pajerosport'            # адрес на сайте
BOOK = 'pajerosport-classic'    # папка книги, ролика и A+

PB, KIN = 'B0HJRR8WNK', 'B0HJRLJMG6'
TITLE_RAW = 'Pajero Sport Trivia & Fun Facts'
TITLE = SHORT = 'Pajero Sport Trivia &amp; Fun Facts'
PITCH = ("It was meant to be the sensible one: a lower, lighter, cheaper relative of a four-wheel "
         "drive whose maker won the Dakar Rally a record twelve times. Abroad it changed its name at "
         "the border, was rebuilt on a working pickup frame and ended up on sale in some ninety "
         "countries. Ninety verified questions across ten themed parts — the name that had to be "
         "dropped in Spanish, the tail lamps that divided reviewers, the four-wheel drive that runs on "
         "dry tarmac and the safety rule that ended its Australian sales.")
DESC_META = ("It was meant to be the sensible one: a lower, lighter, cheaper relative of a "
             "rally-winning four-wheel drive, and abroad it changed its name at the border. Ninety "
             "verified questions, ten themed parts.")

# те же названия, что в модуле A+ «Inside the book» (приёмка ChatGPT 14.09)
PARTS = [
    ('The Name.', 'And why it changed in Spanish'),
    ('Built for the City.', 'The first generation at home'),
    ('Other Passports.', 'One car, several badges abroad'),
    ('Moves House.', 'A pickup frame and a new factory'),
    ('Gets a Face.', 'The tail lamps people argued about'),
    ('Under the Bonnet.', 'A diesel with a light-alloy block'),
    ('Super Select.', 'What each setting really does'),
    ('Factories.', 'Five million, and one closed plant'),
    ('Crash Tests.', 'Stars, and the rule that ended it'),
    ('End of the Line.', 'Special editions and what came next'),
]

ALSO = [  # (href, короткое имя, путь к ebook-обложке)
    ('wrangler',     'Jeep Wrangler Trivia',    'wrangler/wrangler-ebook-cover.jpg'),
    ('4runner',      'Toyota 4Runner Trivia',   '4runner/4runner-ebook-cover.jpg'),
    ('gwagon',       'Mercedes G-Wagon Trivia', 'gwagon/gwagon-ebook-cover.jpg'),
    ('japanese-car', 'Japanese Cars Trivia',    'jdm/jdm-ebook-cover.jpg'),
]

# Q1.2 книги дословно; пример в A+ — Q1.1, поэтому здесь другой вопрос
QUIZ = dict(
    top='Q2  &middot;  PART 1  &middot;  A NAME BORROWED',
    q='In Spain and in most of Spanish-speaking America, the full-size model was sold under a '
      'different name. Which?',
    opts=['Montero', 'Cordillera', 'Serrano', 'Condor'],
    correct=0,
    reveal=("In Spanish slang <i>pajero</i> is a vulgar insult, and no dealer wanted to sell a car "
            "called that. <i>Montero</i> is a Spanish word for a huntsman, which kept the outdoor "
            "idea and lost the problem. When the smaller model arrived, it simply added a word to "
            "whichever name the local big brother carried."),
)

# что заменяем в исходной странице
SRC_TITLE = 'Ultimate Toyota Challenge'
SRC_PITCH = ("The largest car company in the world began as a workshop that made machines for weaving "
             "cloth, and the man who founded it never learned to drive. The money that bought its way "
             "into cars came out of a loom patent sold to Lancashire in 1929. Ninety verified questions "
             "across ten themed parts — the best-seller nobody can draw from memory, the method everyone "
             "copied, the race it could not win, and the luxury car built in secret.")
SRC_DESC = ("The largest car company in the world began as a workshop that made machines for weaving "
            "cloth, and the man who founded it never learned to drive. Ninety verified questions, "
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
new_blobs = [datauri(KDP / BOOK / f'{BOOK}-ebook-cover.jpg', 640, 82)]
new_blobs += [datauri(KDP / p, 300, 80) for _, _, p in ALSO]
for m, nb in zip(reversed(blobs), reversed(new_blobs)):
    s = s[:m.start()] + nb + s[m.end():]

# --- 2. видео: квадратный мастер, версионное имя по размеру, постер с 17.6 с ---
mp4 = KDP / 'video' / 'out' / f'{BOOK}-promo.mp4'
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
for old, new in (('/video/toyota-promo-3290564-poster.jpg', f'/video/{pname}'),
                 ('/video/toyota-promo-3290564.mp4', f'/video/{vname}')):
    assert old in s, old
    s = s.replace(old, new)

# --- 3. A+ модули 1,5,6 (модуль 4 «THE SERIES» со страниц снят — коммит 76d7156) ---
apd = DEPLOY / 'aplus' / SLUG
apd.mkdir(parents=True, exist_ok=True)
for n, key, wmax in [(1, 'hero', 970), (5, 'gift', 700), (6, 'author', 700)]:
    im = Image.open(KDP / 'aplus-batch' / 'out' / BOOK / f'module{n}_{key}.png').convert('RGB')
    if im.width > wmax:
        im = im.resize((wmax, round(im.height * wmax / im.width)), Image.LANCZOS)
    im.save(apd / f'{n}.jpg', 'JPEG', quality=82, optimize=True, progressive=True)
s = s.replace('/aplus/toyota/', f'/aplus/{SLUG}/')

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
old_c = 'const CORRECT = 1;   // B — имя принадлежало Willys-Overland'
assert old_c in s
s = s.replace(old_c, f"const CORRECT = {QUIZ['correct']};   // A — Montero")

# --- 6. тексты, ссылки, ASIN ---
# ASIN встречается не только в ссылках: блок отзывов держит его в переменной JS
s = s.replace('B0HJ5LVNKQ', PB).replace('B0HJ5JCGRW', KIN)
s = s.replace('/books/toyota/', f'/books/{SLUG}/')
s = s.replace('/covers/toyota.jpg', f'/covers/{SLUG}.jpg')
assert SRC_PITCH in s and SRC_DESC in s
s = s.replace(SRC_PITCH, PITCH).replace(SRC_DESC, DESC_META)
# у пяти врезок один источник (честно помечены на странице источников), у всех 90 ответов — два и больше
assert s.count('<div class="lbl">Sources per fact</div>') == 1
s = s.replace('<div class="lbl">Sources per fact</div>', '<div class="lbl">Sources per answer</div>')
# в JSON-LD сущности HTML не раскрываются — там название сырым, в разметке через &amp;
ld = re.search(r'<script type="application/ld\+json">(.*?)</script>', s, re.S)
s = s[:ld.start(1)] + ld.group(1).replace(f'"{SRC_TITLE}"', json.dumps(TITLE_RAW)) + s[ld.end(1):]
s = s.replace(SRC_TITLE, TITLE)

# --- 7. «Also on this shelf» — СТРОГО после блока 6 ---
old_also = re.search(r'<div class="also">.*?</div></a></div>', s, re.S).group(0)
cards = '\n'.join(
    f'<a href="/books/{sl}/"><img src="{nb}" alt="{nm} cover"><div class="t">{nm}</div></a>'
    for (sl, nm, _), nb in zip(ALSO, new_blobs[1:]))
s = s.replace(old_also, f'<div class="also">{cards}</div>')

# следов Toyota и старой упаковки не должно остаться нигде, КРОМЕ карточек соседей
probe = re.sub(r'<div class="also">.*?</div>\n  </div>', '', s, flags=re.S)
probe = re.sub(r'data:image/\w+;base64,[A-Za-z0-9+/=]+', '', probe)
leftovers = re.findall(r'(?i)toyota|loom|lancashire|willys|land cruiser|corolla|ultimate|'
                       r'B0HJ5LVNKQ|B0HJ5JCGRW', probe)
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
