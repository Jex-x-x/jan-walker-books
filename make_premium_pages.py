#!/usr/bin/env python3
"""Отдельная серия сайта «Premium Editions»: /premium/ (витрина) + /premium/<slug>/ (карточка каждой книги).
Картинки только из премиум-изданий: твёрдая обложка, заставки частей, настоящий разворот блока.
Новая премиум-книга = одна запись в BOOKS (+ запуск скрипта). Идемпотентно, правит только /premium/.

  python3 make_premium_pages.py
"""
import html, re, shutil, subprocess
from pathlib import Path
import fitz
from PIL import Image
from fontTools.ttLib import TTFont

K = Path('/Users/jexxx/autopapyrus-kdp')
KC = Path('/Users/jexxx/kdp/books/corvette/premium')
DEPLOY = K / 'site' / '_deploy'
OUT = DEPLOY / 'premium'
FONTS = K / 'covers' / 'fonts' / 'ofl' / 'static'

# slug (адрес /premium/<slug>/), папка издания, название, подзаголовок, ASIN твёрдой, страница стандартной книги, крючок
BOOKS = [
 dict(slug='911', d=K/'p911/premium', pre='p911', title='911', asin='B0HSVN115H', std=None, q=120, new=True,
      sub="What You Probably Didn't Know About the Rear-Engined Sports Car",
      hook='It was meant to be the 901, until a French carmaker objected.'),
 dict(slug='corvette', d=KC, pre='corvette', title='Corvette', asin='B0HSSSMJ4F', std=None, q=120, new=True,
      sub="What You Probably Didn't Know About America's Sports Car",
      hook='It began as a secret project in 1951, with a fibreglass body meant to be a stopgap.'),
 dict(slug='rx8', d=K/'rx8/hardcover/premium', pre='rx8', title='RX-8', asin='B0HR2SFK5B', std='rx8',
      sub="What You Probably Didn't Know About the Four-Door Sports Car With a Rotary Engine", hook='An engine with no pistons.'),
 dict(slug='miata2', d=K/'miata2/hardcover/premium', pre='miata2', title='MX-5 Miata, Volume 2', asin='B0HR2ZZ351', std='miata2',
      sub="Ninety More Things You Probably Didn't Know About the Best-Selling Roadster Ever Built", hook='The longest-running one-make race series in the world.'),
 dict(slug='tacoma', d=K/'tacoma/hardcover/premium', pre='tacoma', title='Toyota Tacoma', asin='B0HQ4XMNY1', std='tacoma',
      sub="What You Probably Didn't Know About the Truck in Your Driveway", hook='One generation, eleven years, and still outsold everyone at the end.'),
 dict(slug='300zx', d=K/'z32/hardcover/premium', pre='z32', title='300ZX', asin='B0HQ5DSC9X', std='300zx',
      sub="What You Probably Didn't Know About the Twin-Turbo Sports Car Designed on a Supercomputer", hook='Designed on a supercomputer, raced to Daytona.'),
 dict(slug='s2000', d=K/'s2000/hardcover/premium', pre='s2000', title='Honda S2000', asin='B0HPL31ZQ3', std='s2000',
      sub="What You Probably Didn't Know About the 9,000 RPM Roadster Honda Built for Its 50th Birthday", hook='A fiftieth-birthday present that revved to 9,000. No turbo, no successor.'),
 dict(slug='4runner', d=K/'4runner/hardcover/premium', pre='4runner', title='Toyota 4Runner', asin='B0HPKVS16Q', std='4runner',
      sub="What You Probably Didn't Know About the Body-on-Frame SUV That Refused to Die", hook='Fifteen years on one chassis. A cult formed around the receipt.'),
 dict(slug='skyline', d=K/'skyline/hardcover/premium', pre='skyline', title='Skyline GT-R', asin='B0HNNTLVWQ', std='skyline',
      sub="What You Probably Didn't Know About the JDM Legend They Called Godzilla", hook='They called it Godzilla. It earned it. Five generations deep.'),
 dict(slug='supra', d=K/'supra/hardcover/premium', pre='supra', title='Toyota Supra', asin='B0HN5DKVJP', std='supra',
      sub="What You Probably Didn't Know About the JDM Icon That Made the 2JZ a Legend", hook='The 2JZ legend, told properly, from Aristo sedan to 1,000 hp.'),
 dict(slug='miata', d=K/'miata/hardcover/premium', pre='miata', title='Mazda MX-5 Miata', asin='B0HN5TTNRS', std='miata',
      sub="What You Probably Didn't Know About the Best-Selling Roadster Ever Built", hook='The best-selling two-seat roadster ever built. Guinness says so.'),
 dict(slug='wrx', d=K/'wrx/hardcover/premium', pre='wrx', title='Subaru WRX', asin='B0HNN72HXM', std='wrx',
      sub="What You Probably Didn't Know About the Rally Car Subaru Sold to the Public", hook='The rally car a rulebook forced Subaru to sell you.'),
 dict(slug='gwagon', d=K/'gwagon/premium', pre='gwagon', title='G-Wagon', asin='B0HK4G1F5Z', std='gwagon',
      sub="What You Probably Didn't Know About the Boxy Fortress from Graz", hook="Born from a Shah's order that died 16 days before production."),
 dict(slug='pajerosport', d=K/'pajerosport/premium', pre='pajerosport', title='Pajero Sport', asin='B0HK3BG73Y', std='pajerosport',
      sub="What You Probably Didn't Know About the SUV Whose Name Changed at the Border", hook='Its family name was rude in Spanish, so the badge changed at the border.'),
]
import json


def esc(s): return html.escape(s, quote=True)


def read_pdf(b):
    pdf = fitz.open(str(b['d'] / f"{b['pre']}-hc-interior-KDP.pdf"))
    b['pages'] = len(pdf)
    # «About this book»: первые абзацы страницы 2
    tx = ' '.join(l.strip() for l in pdf[1].get_text().split('\n')[1:])      # без заголовка «About this book»
    tx = re.sub(r'(?<=[a-z])- (?=[a-z])', '', tx)      # перенос слова из PDF: «be- hind»
    sents = re.split(r'(?<=[.!?])\s+', tx)
    out = ''
    for sn in sents:
        out += (' ' if out else '') + sn
        if len(out) > 380: break
    b['about'] = [out]
    # содержание
    parts = []
    for i in range(2, 8):
        tx = pdf[i].get_text()
        if re.sub(r'\s', '', tx[:30]).lower().startswith('contents'):
            lines = [l.strip() for l in tx.split('\n')][1:]
            nxt = pdf[i + 1].get_text().split('\n')                  # оглавление может уходить на следующую страницу
            if nxt and re.fullmatch(r'\d\d', nxt[0].strip()): lines += [l.strip() for l in nxt]
            cur = None
            for l in lines:
                if cur is None and l == f'{len(parts) + 1:02d}':
                    cur = [l, None, []]; parts.append(cur)
                elif cur and cur[1] is None: cur[1] = l
                elif cur and re.fullmatch(r'\d+', l): cur = None
                elif cur: cur[2].append(l)
            break
    b['parts'] = [(p[0], p[1], ' '.join(p[2])) for p in parts if p[1]]
    return pdf


def assets(b, pdf):
    side = json.load(open(b['d'] / 'openers_side.json'))
    n = len(side)
    if len(b['parts']) != n:
        b['parts'] = [(f'{i:02d}', f'Part {i}', '') for i in range(1, n + 1)]
    b['n'] = n
    img = OUT / 'img' / b['slug']; img.mkdir(parents=True, exist_ok=True)
    fr = Image.open(b['d'] / f"{b['pre']}-hc-front.jpg").convert('RGB')
    fr.resize((760, round(fr.height * 760 / fr.width)), Image.LANCZOS).save(img / 'front.jpg', quality=84, optimize=True, progressive=True)
    fr.resize((420, round(fr.height * 420 / fr.width)), Image.LANCZOS).save(img / 'front-s.jpg', quality=82, optimize=True, progressive=True)
    for i in range(1, n + 1):
        op = Image.open(b['d'] / 'openers' / f"opener_part{i}_{side[str(i)]}.jpg").convert('RGB')
        op.resize((300, round(op.height * 300 / op.width)), Image.LANCZOS).save(img / f'op{i}.jpg', quality=80, optimize=True, progressive=True)
    # разворот: открывающая страница части 2 рядом со страницей текста
    toc = json.load(open(b['d'] / 'toc_pages_hc.json'))
    p2 = int(toc['2']); pages = (p2, p2 + 1) if side['2'] == 'L' else (p2 - 1, p2)
    ims = []
    for pn in pages:
        pg = pdf[pn - 1]; z = 900 / pg.rect.height
        pm = pg.get_pixmap(matrix=fitz.Matrix(z, z)); ims.append(Image.frombytes('RGB', (pm.width, pm.height), pm.samples))
    sp = Image.new('RGB', (ims[0].width + ims[1].width, ims[0].height), (255, 255, 255))
    sp.paste(ims[0], (0, 0)); sp.paste(ims[1], (ims[0].width, 0))
    sp.save(img / 'spread.jpg', quality=82, optimize=True, progressive=True)


def fonts():
    d = OUT / 'fonts'; d.mkdir(parents=True, exist_ok=True)
    for name in ['NunitoSans-700', 'NunitoSans-800', 'EBGaramond-400', 'EBGaramond-Italic-400']:
        dst = d / f'{name}.woff2'
        if dst.exists(): continue
        f = TTFont(FONTS / f'{name}.ttf'); f.flavor = 'woff2'; f.save(dst)


CSS = '''
@font-face{font-family:'NS';src:url(/premium/fonts/NunitoSans-700.woff2) format('woff2');font-weight:700;font-display:swap}
@font-face{font-family:'NS';src:url(/premium/fonts/NunitoSans-800.woff2) format('woff2');font-weight:800;font-display:swap}
@font-face{font-family:'EBG';src:url(/premium/fonts/EBGaramond-400.woff2) format('woff2');font-weight:400;font-display:swap}
@font-face{font-family:'EBG';src:url(/premium/fonts/EBGaramond-Italic-400.woff2) format('woff2');font-weight:400;font-style:italic;font-display:swap}
:root{--bg:#16171a;--bg2:#1d1f23;--ivory:#f2ece2;--champ:#cdba96;--muted:#a8a196;--line:#34353a}
*{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth}
html{background:#16171a}body{background:radial-gradient(1200px 700px at 50% -10%,#2a2c31 0,#16171a 60%) no-repeat;color:var(--ivory);font-family:'EBG',Georgia,serif;font-size:19px;line-height:1.6;overflow-x:hidden}
a{color:inherit}
.wrap{max-width:1120px;margin:0 auto;padding:0 20px}
nav{border-bottom:1px solid var(--line);padding:16px 0}
nav .wrap{display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap}
.lg{font-family:'NS',sans-serif;font-weight:800;letter-spacing:.14em;text-transform:uppercase;font-size:14px;text-decoration:none;color:var(--ivory)}
.lg span{color:var(--champ)}
nav .l a{font-family:'NS',sans-serif;font-weight:700;font-size:12px;letter-spacing:.22em;text-transform:uppercase;text-decoration:none;color:var(--muted);margin-left:22px}
nav .l a:hover,nav .l a.on{color:var(--champ)}
.kick{font-family:'NS',sans-serif;font-weight:700;font-size:12px;letter-spacing:.3em;text-transform:uppercase;color:var(--champ)}
h1,h2{font-family:'NS',sans-serif;font-weight:800;letter-spacing:.07em;text-transform:uppercase;line-height:1.12}
h1{font-size:clamp(34px,6vw,58px);margin:10px 0 14px}
h2{font-size:clamp(22px,3.4vw,30px);margin:6px 0 10px}
.rule{width:60px;height:2px;background:var(--champ);margin:18px 0}
.sub{font-style:italic;font-size:clamp(20px,2.6vw,25px);color:var(--ivory);max-width:34em}
.lede{color:var(--muted);max-width:40em}
.btn{display:inline-block;font-family:'NS',sans-serif;font-weight:800;font-size:13px;letter-spacing:.2em;text-transform:uppercase;text-decoration:none;padding:15px 26px;border:1px solid var(--champ);color:var(--bg);background:var(--champ);border-radius:2px}
.btn:hover{background:var(--ivory);border-color:var(--ivory)}
.btn.g{background:transparent;color:var(--champ)}
.btn.g:hover{background:var(--champ);color:var(--bg)}
.hero{padding:54px 0 40px;display:grid;grid-template-columns:minmax(0,5fr) minmax(0,6fr);gap:54px;align-items:center}
.hero .cv img{width:100%;height:auto;display:block;border-radius:3px;box-shadow:0 40px 70px -28px #000,0 0 0 1px #0006}
.facts{list-style:none;margin:6px 0 26px}
.facts li{padding:6px 0 6px 30px;position:relative}
.facts li::before{content:'';position:absolute;left:0;top:19px;width:16px;height:1px;background:var(--champ)}
.cta{display:flex;gap:14px;flex-wrap:wrap;align-items:center}
section.s{padding:44px 0;border-top:1px solid var(--line)}
.parts{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:22px;margin-top:26px}
.parts figure img{width:100%;height:auto;display:block;border-radius:2px;box-shadow:0 18px 30px -18px #000}
.parts .n{font-family:'NS',sans-serif;font-weight:800;font-size:13px;letter-spacing:.14em;color:var(--champ);margin-top:10px}
.parts .t{font-size:17px;line-height:1.3}
.parts .d{font-size:14.5px;color:var(--muted);line-height:1.35;margin-top:3px}
.spread img{width:100%;height:auto;display:block;box-shadow:0 36px 60px -26px #000;border-radius:2px;margin-top:22px}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:30px;margin-top:34px}
.card{text-decoration:none;display:block;position:relative}.card .badge{position:absolute;top:12px;left:12px;margin:0;background:#16171acc}
.card img{width:100%;height:auto;display:block;border-radius:3px;box-shadow:0 26px 40px -22px #000;transition:transform .25s}
.card:hover img{transform:translateY(-4px)}
.card .t{font-family:'NS',sans-serif;font-weight:800;letter-spacing:.1em;text-transform:uppercase;font-size:15px;margin-top:16px}
.card .h{color:var(--muted);font-size:16.5px;line-height:1.4;margin-top:4px}
.card .go{font-family:'NS',sans-serif;font-weight:700;font-size:11.5px;letter-spacing:.22em;text-transform:uppercase;color:var(--champ);margin-top:10px}
.badge{display:inline-block;font-family:'NS',sans-serif;font-weight:800;font-size:10.5px;letter-spacing:.24em;text-transform:uppercase;border:1px solid var(--champ);color:var(--champ);padding:3px 8px;margin-bottom:10px}
.std{color:var(--muted);margin-top:22px;font-size:17px}
.std a{color:var(--champ)}
footer{border-top:1px solid var(--line);padding:30px 0 50px;color:var(--muted);font-size:15px;margin-top:20px}
footer a{color:var(--muted);margin-right:18px}
@media(max-width:760px){.hero{grid-template-columns:1fr;gap:30px;padding-top:34px}.hero .cv{max-width:340px}nav .l a{margin-left:14px}}
'''

HEAD = '''<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="icon" href="/favicon.ico?v=2" sizes="any">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png?v=2">
<link rel="apple-touch-icon" href="/apple-touch-icon.png?v=2">
<meta name="description" content="{desc}">
<link rel="canonical" href="https://janwalkerbooks.com{path}">
<meta property="og:type" content="{ogt}">
<meta property="og:site_name" content="Jan Walker Books">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="https://janwalkerbooks.com{path}">
<meta property="og:image" content="https://janwalkerbooks.com{img}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@JanWalkerBooks">
{extra}<style>{css}</style>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-N9W5S95JNL"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-N9W5S95JNL');</script>
<script data-goatcounter="https://janwalkerbooks.goatcounter.com/count" async src="https://gc.zgo.at/count.js"></script>
'''
NAV = '''<nav><div class="wrap"><a class="lg" href="/">Jan<span>&nbsp;Walker</span></a>
<div class="l"><a href="/#garage">Cars &amp; Trucks</a><a class="on" href="/premium/">Premium Editions</a><a href="/#family">Family Table</a></div></div></nav>
'''
FOOT = '''<footer><div class="wrap"><a href="/">Jan Walker Books</a><a href="/premium/">Premium Editions</a><a href="https://www.amazon.com/Jan-Walker/e/B0H3W7P7KR" target="_blank" rel="noopener">Amazon author page</a><a href="https://www.youtube.com/@JanWalkerBooks" target="_blank" rel="noopener">YouTube</a>
<p style="margin-top:14px">Independent, unofficial publications. All images in these books are AI-generated illustrations.</p></div></footer>
'''


def card(b):
    return (f'<a class="card" href="/premium/{b["slug"]}/"><img src="/premium/img/{b["slug"]}/front-s.jpg" alt="{esc(b["title"])} Trivia &amp; Fun Facts, premium hardcover edition" loading="lazy" width="420" height="{round(420*Image.open(b["d"]/(b["pre"]+"-hc-front.jpg")).height/Image.open(b["d"]/(b["pre"]+"-hc-front.jpg")).width)}">'
            f'{"<span class=badge>New</span>" if b.get("new") else ""}'
            f'<div class="t">{esc(b["title"])}</div><div class="h">{esc(b["hook"])}</div><div class="go">View edition &rarr;</div></a>')


def hub():
    cards = '\n'.join(card(b) for b in BOOKS)
    head = HEAD.format(title='Premium Editions — Trivia & Fun Facts hardcovers by Jan Walker', css=CSS, path='/premium/', ogt='website',
                       desc='Trivia & Fun Facts: Premium Editions. Full-colour matte hardcovers, a full-page image opening every part, the same verified questions.',
                       img=f'/premium/img/{BOOKS[0]["slug"]}/front.jpg', extra='')
    body = f'''<body>{NAV}
<header class="wrap" style="padding:60px 20px 10px">
<div class="kick">Trivia &amp; Fun Facts</div>
<h1>Premium Editions</h1>
<div class="rule"></div>
<p class="sub">Full-colour hardcovers. A full-page image opens every part.</p>
<p class="lede" style="margin-top:14px">A series of its own: matte-finish hardcovers with colour illustration throughout, made to be given and kept. Every question is checked against at least two sources, and the answer tells the story behind it.</p>
</header>
<main class="wrap"><div class="cards">
{cards}
</div></main>
{FOOT}</body></html>'''
    (OUT / 'index.html').write_text(head + body)


def detail(b, i):
    others = [x for x in BOOKS if x['slug'] != b['slug']]
    nxt = [BOOKS[(i + k) % len(BOOKS)] for k in (1, 2, 3, 4)]
    url = f'https://www.amazon.com/dp/{b["asin"]}'
    q = b.get('q', 90)
    parts = ''.join(
        f'<figure><img src="/premium/img/{b["slug"]}/op{n}.jpg" alt="Part {int(num)}: {esc(t)}, full-page image" loading="lazy">'
        f'<div class="n">{num}</div><div class="t">{esc(t)}</div>{f"<div class=d>{esc(dd)}</div>" if dd else ""}</figure>'
        for n, (num, t, dd) in enumerate(b['parts'], 1))
    about = ''.join(f'<p class="lede" style="margin-top:12px">{esc(p)}</p>' for p in b['about'])
    ld = json.dumps({"@context": "https://schema.org", "@type": "Book", "name": f'{b["title"]} Trivia & Fun Facts (Premium Edition)',
                     "author": {"@type": "Person", "name": "Jan Walker"}, "bookFormat": "https://schema.org/Hardcover",
                     "numberOfPages": b['pages'], "inLanguage": "en", "image": f'https://janwalkerbooks.com/premium/img/{b["slug"]}/front.jpg',
                     "url": f'https://janwalkerbooks.com/premium/{b["slug"]}/', "isPartOf": {"@type": "BookSeries", "name": "Trivia & Fun Facts: Premium Editions"},
                     "workExample": {"@type": "Book", "bookFormat": "https://schema.org/Hardcover", "url": url}}, ensure_ascii=False)
    desc = f'{b["title"]} Trivia & Fun Facts, Premium Edition: {b["sub"]}. Full-colour matte hardcover, {q} verified questions in {b["n"]} parts, a full-page image opening every part.'
    head = HEAD.format(title=f'{b["title"]} Trivia & Fun Facts, Premium Edition — Jan Walker', css=CSS, path=f'/premium/{b["slug"]}/', ogt='book',
                       desc=esc(desc[:300]), img=f'/premium/img/{b["slug"]}/front.jpg', extra=f'<script type="application/ld+json">{ld}</script>\n')
    std = (f'<p class="std">Also in paperback and Kindle: <a href="/books/{b["std"]}/">the standard edition of {esc(b["title"])} Trivia</a>.</p>' if b['std'] else '')
    body = f'''<body>{NAV}
<main class="wrap">
<div class="hero">
  <div class="cv"><img src="/premium/img/{b["slug"]}/front.jpg" alt="{esc(b["title"])} Trivia &amp; Fun Facts, premium hardcover cover" width="760" height="{round(760*Image.open(b["d"]/(b["pre"]+"-hc-front.jpg")).height/Image.open(b["d"]/(b["pre"]+"-hc-front.jpg")).width)}"></div>
  <div>
    <div class="kick">Trivia &amp; Fun Facts &middot; Premium Editions</div>
    <h1>{esc(b["title"])}</h1>
    <p class="sub">{esc(b["sub"])}</p>
    <div class="rule"></div>
    <ul class="facts">
      <li>{q} verified multiple-choice questions in {b["n"]} parts</li>
      <li>A full-page colour image opens every part</li>
      <li>Matte-finish hardcover, full colour, {b["pages"]} pages</li>
      <li>Every answer comes with the story behind it</li>
    </ul>
    <div class="cta"><a class="btn" href="{url}" target="_blank" rel="noopener">Hardcover on Amazon</a><a class="btn g" href="#inside">Inside the book</a></div>
    {std}
  </div>
</div>
<section class="s" id="inside">
  <div class="kick">Inside the book</div>
  <h2>{b["n"]} parts. {q} questions.</h2>
  {about}
  <div class="parts">{parts}</div>
</section>
<section class="s spread">
  <div class="kick">A page from the book</div>
  <h2>Every part opens like this.</h2>
  <p class="lede">The full-page image, then the introduction and the questions. Each answer begins directly beneath its question.</p>
  <img src="/premium/img/{b["slug"]}/spread.jpg" alt="Hardcover spread of {esc(b["title"])} Trivia: a full-page image opening Part Two beside a page of questions" loading="lazy">
</section>
<section class="s">
  <div class="kick">More in the series</div>
  <h2>Premium Editions</h2>
  <div class="cards">{''.join(card(x) for x in nxt)}</div>
  <p style="margin-top:34px"><a class="btn g" href="/premium/">All Premium Editions</a></p>
</section>
</main>
{FOOT}</body></html>'''
    d = OUT / b['slug']; d.mkdir(exist_ok=True)
    (d / 'index.html').write_text(head + body)


def sitemap():
    p = DEPLOY / 'sitemap.xml'; s = p.read_text()
    s = re.sub(r'\s*<url><loc>https://janwalkerbooks\.com/premium/[^<]*</loc>.*?</url>', '', s)
    urls = ['/premium/'] + [f'/premium/{b["slug"]}/' for b in BOOKS]
    add = ''.join(f'\n  <url><loc>https://janwalkerbooks.com{u}</loc><changefreq>weekly</changefreq><priority>{"0.9" if u=="/premium/" else "0.7"}</priority></url>' for u in urls)
    s = s.replace('</urlset>', add + '\n</urlset>'); p.write_text(s)


if __name__ == '__main__':
    OUT.mkdir(exist_ok=True)
    fonts()
    for b in BOOKS:
        pdf = read_pdf(b); assets(b, pdf)
        print(b['slug'], b['pages'], 'стр', b['n'], 'частей', len(b['about']), 'абзаца about |', b['parts'][0][1])
    hub()
    for i, b in enumerate(BOOKS): detail(b, i)
    sitemap()
    print('ok', sum(f.stat().st_size for f in OUT.rglob('*') if f.is_file()) // 1000, 'KB')
