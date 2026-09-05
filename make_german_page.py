#!/usr/bin/env python3
"""Страница /books/german/ — собирается из соседней italian-страницы.

build.py для новых книг не годится: его словарь BOOKS отстал (нет italian,
japanese-car, delorean, wrangler, s2000, german), и запуск перезаписал бы
index.html главной, потеряв полки, добавленные руками. Поэтому — точечная
пересборка одной страницы из уже проверенного шаблона соседа.
"""
import base64, io, re, shutil, subprocess
from pathlib import Path
from PIL import Image

KDP = Path('/Users/jexxx/autopapyrus-kdp')
DEPLOY = KDP / 'site' / '_deploy'
SRC = DEPLOY / 'books' / 'italian' / 'index.html'
OUT = DEPLOY / 'books' / 'german'
SLUG = 'german'

PB, KIN = 'B0HHSV7NYP', 'B0HHX1DJWY'
TITLE = 'German Cars Trivia &amp; Fun Facts'
TITLE_PLAIN = 'German Cars Trivia & Fun Facts'
SHORT = 'German Cars Trivia'
PITCH = ("In 1948 the whole Wolfsburg factory was offered to Ford for nothing, and Ford's chief "
         "adviser said it wasn't worth a damn. Every marque in this book was once a week from the "
         "receiver. Ninety verified questions across ten themed parts — Volkswagen, Porsche, "
         "Mercedes-Benz, BMW, Audi, the tuning divisions and the races that made the reputations.")
# meta/og-описание — отдельная короткая фраза, а НЕ срез PITCH: срез является его
# префиксом, и .replace() тогда рвёт заодно полный питч в герое и JSON-LD.
DESC_META = ("In 1948 the whole Wolfsburg factory was offered to Ford for nothing, and Ford's chief "
             "adviser said it wasn't worth a damn. Every marque in this book was once a week from the "
             "receiver. Ninety verified questions, ten themed parts.")

PARTS = [
    ('Before the Legends.', '1886 to 1945, and the men who started it'),
    ("The People's Car.", 'Volkswagen, and the factory nobody wanted'),
    ("Stuttgart's Stubborn Idea.", 'Porsche, born in a sawmill'),
    ('The Three-Pointed Star.', 'Mercedes-Benz'),
    ('Munich.', 'BMW, eleven days from being sold for parts'),
    ('Four Rings.', 'Audi, and four companies that all went broke'),
    ('The Fast Divisions.', 'AMG, M, RS and the outside tuners'),
    ('Silver Arrows and the Green Hell.', 'Racing'),
    ('Things Invented Here.', 'Engineering firsts'),
    ('Autobahn Culture.', 'Living with these cars'),
]

ALSO = [  # (href, короткое имя, путь к ebook-обложке)
    ('italian',      'Italian Cars Trivia',    'italian/italian-ebook-cover.jpg'),
    ('japanese-car', 'Japanese Cars Trivia',   'jdm/jdm-ebook-cover.jpg'),
    ('gwagon',       'Mercedes G-Wagon Trivia','gwagon/gwagon-ebook-cover.jpg'),
    ('wrangler',     'Jeep Wrangler Trivia',   'wrangler/wrangler-ebook-cover.jpg'),
]

QUIZ = dict(
    top='Q10  ·  PART 2  ·  THE PEOPLE&rsquo;S CAR',
    q='Who restarted Volkswagen production after the Second World War?',
    opts=['Ferdinand Porsche', 'A British Army officer, Major Ivan Hirst',
          'The American occupation administration', 'Heinrich Nordhoff'],
    correct=1,
    reveal=("Wolfsburg fell in the British occupation zone. Major Ivan Hirst, a REME officer, had a "
            "surviving car painted green and presented to the army, which ordered 20,000 vehicles — "
            "enough to justify restarting the line in 1945. Heinrich Nordhoff took over in 1948 and ran "
            "the company for twenty years, but the plant was already running when he arrived."),
)


def datauri(path, width, quality):
    im = Image.open(path).convert('RGB')
    im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, 'JPEG', quality=quality, optimize=True, progressive=True)
    return 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()


s = SRC.read_text()

# --- 1. картинки: герой 640×1024 + четыре соседа 300×480 ---
blobs = list(re.finditer(r'data:image/jpeg;base64,[A-Za-z0-9+/=]+', s))
assert len(blobs) == 5, len(blobs)
new_blobs = [datauri(KDP / 'german' / 'german-ebook-cover.jpg', 640, 82)]
new_blobs += [datauri(KDP / p, 300, 80) for _, _, p in ALSO]
for m, nb in zip(reversed(blobs), reversed(new_blobs)):
    s = s[:m.start()] + nb + s[m.end():]

# --- 2. видео: версионное имя + постер из первого кадра ---
mp4 = KDP / 'video' / 'out' / f'{SLUG}-quiz-vertical.mp4'
vdir = DEPLOY / 'video'
ver = mp4.stat().st_size
vname, pname = f'{SLUG}-promo-{ver}.mp4', f'{SLUG}-promo-{ver}-poster.jpg'
shutil.copy(mp4, vdir / vname)
shutil.copy(mp4, vdir / f'{SLUG}-promo.mp4')
# 0.8 c — кадр с кикером, заголовком и подписью; после 1 c подпись уходит и
# начинается обратный отсчёт, постер становится «пустым».
subprocess.run(['ffmpeg', '-y', '-ss', '0.8', '-i', str(mp4), '-frames:v', '1', '-q:v', '4',
                str(vdir / pname), '-loglevel', 'error'], check=True)
s = s.replace('/video/italian-promo-5229786-poster.jpg', f'/video/{pname}')
s = s.replace('/video/italian-promo-5229786.mp4', f'/video/{vname}')

# --- 3. A+ модули 1,4,5,6 ---
apd = DEPLOY / 'aplus' / SLUG
apd.mkdir(parents=True, exist_ok=True)
for n, key, w in [(1, 'hero', 970), (4, 'series', 700), (5, 'gift', 700), (6, 'author', 700)]:
    im = Image.open(KDP / 'aplus-batch' / 'out' / SLUG / f'module{n}_{key}.png').convert('RGB')
    if im.width > w:
        im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    im.save(apd / f'{n}.jpg', 'JPEG', quality=82, optimize=True, progressive=True)
s = s.replace('/aplus/italian/', f'/aplus/{SLUG}/')

# --- 4. секция «What's inside» ---
old_parts = re.search(r'<div class="parts">.*?</div></div>\n  </div>\n</section>', s, re.S).group(0)
rows = '\n'.join(
    f'<div class="part"><span class="num">{i:02d}</span><span><span class="pt">{t}</span> '
    f'<span class="ps">{sub}</span></span></div>'
    for i, (t, sub) in enumerate(PARTS, 1))
s = s.replace(old_parts, f'<div class="parts">{rows}</div>\n  </div>\n</section>')

# --- 5. секция «Try one on the house» ---
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
s = s.replace('const CORRECT = 1;   // B — 36 экземпляров 250 GTO',
              f"const CORRECT = {QUIZ['correct']};   // B — Major Ivan Hirst")

# --- 7. тексты, ссылки, ASIN ---
s = s.replace('https://www.amazon.com/dp/B0HHQRHR8X', f'https://www.amazon.com/dp/{PB}')
s = s.replace('https://www.amazon.com/dp/B0HHNVXJ2X', f'https://www.amazon.com/dp/{KIN}')
s = s.replace('/books/italian/', f'/books/{SLUG}/')
s = s.replace('/covers/italian.jpg', f'/covers/{SLUG}.jpg')
s = s.replace('Italian Cars Trivia &amp; Fun Facts', TITLE)
s = s.replace('Italian Cars Trivia & Fun Facts', TITLE_PLAIN)
s = s.replace('Italian Cars Trivia', SHORT)
old_pitch_full = ("Ferrari sold road cars to pay for racing and said so out loud. Lamborghini existed because "
                  "a tractor manufacturer had money and a grievance. Ninety verified questions across ten "
                  "themed parts — Ferrari, Lamborghini, Alfa Romeo, Lancia, the Turin design houses and the "
                  "road races that were banned.")
old_pitch_cut = old_pitch_full[:236]
assert old_pitch_full in s and old_pitch_cut in s
# сначала полный питч, потом обрезок: обратный порядок разрубил бы полный питч пополам
s = s.replace(old_pitch_full, PITCH).replace(old_pitch_cut, DESC_META)

# --- 8. «Also on this shelf» — СТРОГО после блока 7 ---
# Иначе глобальная замена «Italian Cars Trivia» → «German Cars Trivia» переименует
# подпись карточки-соседа: обложка итальянской книги с немецким названием.
old_also = re.search(r'<div class="also">.*?</div></a></div>', s, re.S).group(0)
cards = '\n'.join(
    f'<a href="/books/{sl}/"><img src="{nb}" alt="{nm} cover"><div class="t">{nm}</div></a>'
    for (sl, nm, _), nb in zip(ALSO, new_blobs[1:]))
s = s.replace(old_also, f'<div class="also">{cards}</div>')

# следов итальянской книги не должно остаться нигде, КРОМЕ карточки соседа
probe = re.sub(r'<div class="also">.*?</div>\n  </div>', '', s, flags=re.S)
probe = re.sub(r'data:image/\w+;base64,[A-Za-z0-9+/=]+', '', probe)
leftovers = re.findall(r'(?i)italian|ferrari|lamborghini|lancia|B0HHQRHR8X|B0HHNVXJ2X', probe)
assert not leftovers, f'остались следы italian: {leftovers}'
OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'index.html').write_text(s)

# публичная обложка для og:image
cov = Image.open(KDP / 'german' / 'german-ebook-cover.jpg').convert('RGB')
cov = cov.resize((1000, round(cov.height * 1000 / cov.width)), Image.LANCZOS)
cov.save(DEPLOY / 'covers' / f'{SLUG}.jpg', 'JPEG', quality=85, optimize=True)

print(f'books/{SLUG}/index.html  {len(s)/1e3:.0f} KB')
print('video', vname, pname)
print('aplus', sorted(p.name for p in apd.iterdir()))
