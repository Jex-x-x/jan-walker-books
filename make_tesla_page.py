#!/usr/bin/env python3
"""Страница /books/tesla/ — собирается из соседней german-страницы.

Почему не build.py: его словарь BOOKS отстал на шесть книг, а запуск перезаписал
бы index.html главной. Точечная пересборка одной страницы из проверенного соседа —
тот же приём, что в make_german_page.py.

Отличие от german-версии: трейлер сразу квадратный (постер с 17.6 с), потому что
вертикальные шортсы со страниц книг убраны — коммит c933eef.
"""
import base64, io, re, shutil, subprocess
from pathlib import Path
from PIL import Image

KDP = Path('/Users/jexxx/autopapyrus-kdp')
DEPLOY = KDP / 'site' / '_deploy'
SRC = DEPLOY / 'books' / 'german' / 'index.html'
OUT = DEPLOY / 'books' / 'tesla'
SLUG = 'tesla'

PB, KIN = 'B0HJ3VFQWB', 'B0HHZRJR59'
TITLE = TITLE_PLAIN = SHORT = 'Ultimate Tesla Challenge'
PITCH = ("The first car this company sold was a British sports car with the engine taken out, and "
         "the company nearly died before it built anything of its own. It borrowed $465 million "
         "from the American taxpayer and repaid the loan nine years early, with interest. Ninety "
         "verified questions across ten themed parts — the roadster, the saloon, the battery, the "
         "charging network built in secret, the tent in a car park and the car past the orbit of Mars.")
DESC_META = ("The first car this company sold was a British sports car with the engine taken out, and "
             "the company nearly died before it built anything of its own. Ninety verified questions, "
             "ten themed parts.")

PARTS = [
    ('The First Car.', 'A British body with no engine in it'),
    ('The Saloon.', 'Aluminium, and a screen the size of a laptop'),
    ('Inside the Battery.', 'Laptop cells, by the thousand'),
    ('Range and Charging.', 'Towns nobody would drive to on purpose'),
    ('Assisted Driving.', 'What the names have meant, legally'),
    ('Production Hell.', 'The tent that kept a model alive'),
    ('The Strange Ones.', 'Falcon doors and stainless panels'),
    ('Four Factories.', 'Shanghai in 168 working days'),
    ('Numbers and Money.', 'Why one car has three honest 0&ndash;60 times'),
    ('Living With One.', 'And the one that left the planet'),
]

ALSO = [  # (href, короткое имя, путь к ebook-обложке)
    ('german',       'German Cars Trivia',     'german/german-ebook-cover.jpg'),
    ('italian',      'Italian Cars Trivia',    'italian/italian-ebook-cover.jpg'),
    ('japanese-car', 'Japanese Cars Trivia',   'jdm/jdm-ebook-cover.jpg'),
    ('gwagon',       'Mercedes G-Wagon Trivia', 'gwagon/gwagon-ebook-cover.jpg'),
]

QUIZ = dict(
    top='Q47  &middot;  PART 6  &middot;  PRODUCTION HELL',
    q='The car was meant to be called the Model E. It is not. Why?',
    opts=['The letter tested badly', 'A printing constraint',
          'It was never planned', 'A rival firm blocked it'],
    correct=3,
    reveal=("The company applied for Model E in 2013. A rival opposed the filing, citing an earlier "
            "agreement, and the application was abandoned. The range was meant to spell S-E-X-Y; "
            "it reads S, 3, X, Y."),
)

# что заменяем в исходной странице
GER_PITCH = ("In 1948 the whole Wolfsburg factory was offered to Ford for nothing, and Ford's chief "
             "adviser said it wasn't worth a damn. Every marque in this book was once a week from the "
             "receiver. Ninety verified questions across ten themed parts — Volkswagen, Porsche, "
             "Mercedes-Benz, BMW, Audi, the tuning divisions and the races that made the reputations.")
GER_DESC = ("In 1948 the whole Wolfsburg factory was offered to Ford for nothing, and Ford's chief "
            "adviser said it wasn't worth a damn. Every marque in this book was once a week from the "
            "receiver. Ninety verified questions, ten themed parts.")


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
s = s.replace('/video/german-promo-3787226-poster.jpg', f'/video/{pname}')
s = s.replace('/video/german-promo-3787226.mp4', f'/video/{vname}')

# --- 3. A+ модули 1,5,6 (модуль 4 «THE SERIES» со страниц снят — коммит 76d7156) ---
apd = DEPLOY / 'aplus' / SLUG
apd.mkdir(parents=True, exist_ok=True)
for n, key, wmax in [(1, 'hero', 970), (5, 'gift', 700), (6, 'author', 700)]:
    im = Image.open(KDP / 'aplus-batch' / 'out' / SLUG / f'module{n}_{key}.png').convert('RGB')
    if im.width > wmax:
        im = im.resize((wmax, round(im.height * wmax / im.width)), Image.LANCZOS)
    im.save(apd / f'{n}.jpg', 'JPEG', quality=82, optimize=True, progressive=True)
s = s.replace('/aplus/german/', f'/aplus/{SLUG}/')

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
s = s.replace('const CORRECT = 1;   // B — Major Ivan Hirst',
              f"const CORRECT = {QUIZ['correct']};   // D — заявку на Model E заблокировал конкурент")

# --- 6. тексты, ссылки, ASIN ---
# ASIN встречается не только в ссылках: блок отзывов держит его в переменной JS
s = s.replace('B0HHSV7NYP', PB).replace('B0HHX1DJWY', KIN)
s = s.replace('/books/german/', f'/books/{SLUG}/')
s = s.replace('/covers/german.jpg', f'/covers/{SLUG}.jpg')
s = s.replace('German Cars Trivia &amp; Fun Facts', TITLE)
s = s.replace('German Cars Trivia & Fun Facts', TITLE_PLAIN)
s = s.replace('German Cars Trivia', SHORT)
assert GER_PITCH in s and GER_DESC in s
s = s.replace(GER_PITCH, PITCH).replace(GER_DESC, DESC_META)

# --- 7. «Also on this shelf» — СТРОГО после блока 6 ---
old_also = re.search(r'<div class="also">.*?</div></a></div>', s, re.S).group(0)
cards = '\n'.join(
    f'<a href="/books/{sl}/"><img src="{nb}" alt="{nm} cover"><div class="t">{nm}</div></a>'
    for (sl, nm, _), nb in zip(ALSO, new_blobs[1:]))
s = s.replace(old_also, f'<div class="also">{cards}</div>')

# следов немецкой книги не должно остаться нигде, КРОМЕ карточки соседа
probe = re.sub(r'<div class="also">.*?</div>\n  </div>', '', s, flags=re.S)
probe = re.sub(r'data:image/\w+;base64,[A-Za-z0-9+/=]+', '', probe)
leftovers = re.findall(r'(?i)german|wolfsburg|volkswagen|porsche|autobahn|B0HHSV7NYP|B0HHX1DJWY', probe)
assert not leftovers, f'остались следы german: {leftovers}'
OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'index.html').write_text(s)

cov = Image.open(KDP / SLUG / f'{SLUG}-ebook-cover.jpg').convert('RGB')
cov = cov.resize((1000, round(cov.height * 1000 / cov.width)), Image.LANCZOS)
cov.save(DEPLOY / 'covers' / f'{SLUG}.jpg', 'JPEG', quality=85, optimize=True)

print(f'books/{SLUG}/index.html  {len(s)/1e3:.0f} KB')
print('video', vname, pname)
print('aplus', sorted(p.name for p in apd.iterdir()))
