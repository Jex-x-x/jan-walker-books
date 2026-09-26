#!/usr/bin/env python3
"""Страница книги, которой ЕЩЁ НЕТ в продаже: /books/rx7/ и /books/ae86/.

Отличие от make_<slug>_page.py: у книги нет ASIN, поэтому кнопки «Paperback on
Amazon» и «Kindle edition» заменяются блоком «Coming soon», а ссылки на Amazon
внутри пробного вопроса и в JSON-LD ведут на саму страницу. Когда книга выйдет,
достаточно прогнать обычный make_<slug>_page.py с настоящими ASIN.

Почему не build.py: он брошен с 01.09.2026 и откатывает недели правок.

    python3 make_soon_page.py rx7
    python3 make_soon_page.py ae86
"""
import base64, io, json, re, shutil, subprocess, sys
from pathlib import Path
from PIL import Image

KDP = Path('/Users/jexxx/autopapyrus-kdp')
DEPLOY = KDP / 'site' / '_deploy'
SRC = DEPLOY / 'books' / 'gti' / 'index.html'      # донор: та же комплектация, вертикальный ролик

DONOR = dict(
    slug='gti', title_raw='Golf GTI Trivia & Fun Facts', short='Golf GTI Trivia',
    pb='B0HKVWQPBF', kin='B0GX2WLP2B',
    pitch=("Nobody at Volkswagen asked for it. A handful of employees built a fast Golf in the margins "
           "of their real jobs, without a project number, and showed it to management once it already "
           "existed. Ninety verified questions across eight generations — the injection system with "
           "no computer in it, the supercharged four-wheel-drive homologation special, the twelve years "
           "when the badge stopped meaning the fast one, and a N&uuml;rburgring record taken from far "
           "more expensive machinery."),
    leftovers=r'(?i)\b(?:golf|gti|volkswagen|wolfsburg)\b|\bMk[1-8]\b|B0HKVWQPBF|B0GX2WLP2B',
)

BOOKS = {
 'rx7': dict(
   title_raw='RX-7 Trivia & Fun Facts', short='RX-7 Trivia', book='rx7', aplus='rx7',
   pitch=("Mazda licensed an engine in 1961 that scored deep marks into its own housings within hours "
          "of running. NSU gave up on it. Citro&euml;n gave up on it. Mazda spent seventeen years making "
          "it durable, then built a low two-seat coup&eacute; around it and sold that car for twenty-four "
          "years. Ninety verified questions across three generations — the seals that nearly ended it, "
          "the pair of turbochargers brought in one after the other, and the four-rotor prototype that "
          "won Le Mans outright."),
   parts=[('The Engine Mazda Kept.', 'Licensed in 1961, still broken in 1967'),
          ('SA22C.', 'March 1978, about a thousand kilograms'),
          ('FC3S.', 'Turbochargers, and an intercooler in the bonnet'),
          ('FD3S.', 'The shape, and two turbos in sequence'),
          ('How a Rotary Works.', 'Three seals per rotor, one moving part each'),
          ('Le Mans 1991.', 'The 787B, and the rule written before it'),
          ('Racing Everywhere.', 'A hundred IMSA wins, spread over years'),
          ('What Owners Argue About.', 'Oil, compression, and rebuild intervals'),
          ('On Screen.', 'How the shape outlived the production run'),
          ('What They Cost Now.', 'Why the last ones went past the first')],
   quiz=dict(top='Q46  &middot;  PART 6  &middot;  LE MANS 1991',
             q='Which Mazda won Le Mans outright in 1991?',
             opts=['RX-7 GTO', '767B', 'RX-792P', '787B'], correct=3,
             reveal=("The 787B — a closed Group C prototype, not a version of the road car. The 767B came "
                     "before it and the RX-792P after; neither won. Saying that the RX-7 won Le Mans turns "
                     "a real win into a false sentence.")),
   also=[('civic', 'Civic Type R Trivia', 'civic-type-r/civic-type-r-ebook-cover.jpg'),
         ('gti', 'Golf GTI Trivia', 'gti/gti-ebook-cover.jpg'),
         ('miata', 'Mazda MX-5 Miata Trivia', 'miata/miata-ebook-cover.jpg'),
         ('supra', 'Toyota Supra Trivia', 'supra/supra-ebook-cover.jpg')],
   when='Coming soon',
   soon_line=('Printed and proofread, in the last checks before release \u00b7 paperback and Kindle, worldwide from Amazon')),
 'ae86': dict(
   title_raw='AE86 Trivia & Fun Facts', short='AE86 Trivia', book='ae86', aplus='ae86',
   pitch=("Toyota did not set out to build a legend. Retooling a plant for front-wheel drive ran to more "
          "than a hundred and twenty billion yen, so the conversion went in stages and one coup&eacute; "
          "was left on the old rear-drive platform. Ninety verified questions — one car sold under two "
          "names with two different faces, the engine Yamaha helped design, and the comic that arrived "
          "eight years after the last one was built."),
   parts=[('The Last Rear-Drive Coupe.', 'Kept because retooling cost too much'),
          ('Reading the Code.', 'A for engine, E for Corolla, 8 for the series'),
          ('4A-GE.', 'Sixteen valves, two cams, a Yamaha head'),
          ('What America Got.', 'GT-S and SR5: same shell, different engine'),
          ('Tsuchiya and Drifting.', 'A 1987 video, and the licence it nearly cost'),
          ('Racing.', 'Two British touring car titles, on 1.6 litres'),
          ('Initial D.', 'A comic that began eight years too late'),
          ('What Owners Argue About.', 'Codes, axles and forty-year-old shells'),
          ('The Second Coming.', 'One car, four badges, twenty-five years later'),
          ('What They Cost Now.', 'From scrap value to auction catalogue')],
   quiz=dict(top='Q15  &middot;  PART 2  &middot;  READING THE CODE',
             q='What is the difference between an AE85 and an AE86?',
             opts=['The body shape', 'The engine fitted', 'The country of assembly', 'The number of doors'],
             correct=1,
             reveal=("The engine fitted. The shells are shared, but the AE85 has the smaller unit, drum "
                     "rear brakes, a different gearbox and no limited-slip differential. Buyer&rsquo;s "
                     "guides have warned for years that the badges can be swapped.")),
   also=[('civic', 'Civic Type R Trivia', 'civic-type-r/civic-type-r-ebook-cover.jpg'),
         ('supra', 'Toyota Supra Trivia', 'supra/supra-ebook-cover.jpg'),
         ('miata', 'Mazda MX-5 Miata Trivia', 'miata/miata-ebook-cover.jpg'),
         ('wrx', 'Subaru WRX Trivia', 'wrx/wrx-ebook-cover.jpg')],
   when='Coming soon',
   soon_line=('Printed and proofread, in the last checks before release \u00b7 paperback and Kindle, worldwide from Amazon')),
}


def datauri(path, width, quality):
    im = Image.open(path).convert('RGB')
    im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, 'JPEG', quality=quality, optimize=True, progressive=True)
    return 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()


def build(slug):
    cfg = BOOKS[slug]
    title = cfg['title_raw'].replace('&', '&amp;')
    s = SRC.read_text()
    donor_ver = re.search(rf"/video/{DONOR['slug']}-promo-(\d+)\.mp4", s).group(1)

    # 1. картинки: герой 640 + четыре соседа 300
    blobs = list(re.finditer(r'data:image/jpeg;base64,[A-Za-z0-9+/=]+', s))
    assert len(blobs) == 5, len(blobs)
    new_blobs = [datauri(KDP / cfg['book'] / f"{cfg['book']}-ebook-cover.jpg", 640, 82)]
    new_blobs += [datauri(KDP / p, 300, 80) for _, _, p in cfg['also']]
    for m, nb in zip(reversed(blobs), reversed(new_blobs)):
        s = s[:m.start()] + nb + s[m.end():]

    # 2. ролик: вертикальный мастер, версионное имя по размеру, постер с финальным кадром
    mp4 = KDP / 'video' / 'out' / f"{cfg['book']}-quiz-vertical.mp4"
    w, h = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                           'stream=width,height', '-of', 'csv=p=0', str(mp4)],
                          capture_output=True, text=True).stdout.strip().split(',')[:2]
    assert int(h) > int(w), f'мастер не вертикальный: {w}x{h}'
    vdir = DEPLOY / 'video'
    ver = mp4.stat().st_size
    vname, pname = f'{slug}-promo-{ver}.mp4', f'{slug}-promo-{ver}-poster.jpg'
    shutil.copy(mp4, vdir / vname)
    shutil.copy(mp4, vdir / f'{slug}-promo.mp4')
    subprocess.run(['ffmpeg', '-y', '-ss', '23.6', '-i', str(mp4), '-frames:v', '1', '-q:v', '4',
                    str(vdir / pname), '-loglevel', 'error'], check=True)
    for old, new in ((f"/video/{DONOR['slug']}-promo-{donor_ver}-poster.jpg", f'/video/{pname}'),
                     (f"/video/{DONOR['slug']}-promo-{donor_ver}.mp4", f'/video/{vname}')):
        assert old in s, old
        s = s.replace(old, new)

    # 3. A+ модули 1, 5, 6
    apd = DEPLOY / 'aplus' / slug
    apd.mkdir(parents=True, exist_ok=True)
    for n, key, wmax in [(1, 'hero', 970), (5, 'gift', 700), (6, 'author', 700)]:
        im = Image.open(KDP / 'aplus-batch' / 'out' / cfg['aplus'] / f'module{n}_{key}.png').convert('RGB')
        if im.width > wmax:
            im = im.resize((wmax, round(im.height * wmax / im.width)), Image.LANCZOS)
        im.save(apd / f'{n}.jpg', 'JPEG', quality=82, optimize=True, progressive=True)
    s = s.replace(f"/aplus/{DONOR['slug']}/", f'/aplus/{slug}/')

    # 4. «What's inside»
    old_parts = re.search(r'<div class="parts">.*?</div></div>\n  </div>\n</section>', s, re.S).group(0)
    rows = '\n'.join(
        f'<div class="part"><span class="num">{i:02d}</span><span><span class="pt">{t}</span> '
        f'<span class="ps">{sub}</span></span></div>'
        for i, (t, sub) in enumerate(cfg['parts'], 1))
    s = s.replace(old_parts, f'<div class="parts">{rows}</div>\n  </div>\n</section>')

    # 5. пробный вопрос: ссылка ведёт на саму страницу, потому что книги ещё нет в продаже
    q = cfg['quiz']
    old_try = re.search(r'<div class="qtop">.*?</div>\n      </div>\n    </div>', s, re.S).group(0)
    opts = '\n'.join(f'<button class="opt"><span class="tag">{"ABCD"[i]}</span><span>{o}</span></button>'
                     for i, o in enumerate(q['opts']))
    new_try = f'''<div class="qtop">{q['top']}</div>
      <div class="qbody">
        <div class="q">{q['q']}</div>
        <div class="opts" id="opts">{opts}</div>
        <div class="stamp" id="stamp"></div>
        <div class="reveal" id="reveal">{q['reveal']}<br><b>There are 89 more where that came from.</b> {cfg['when']} on Amazon — or <a href="/#quiz">take the full entrance exam &rarr;</a></div>
      </div>
    </div>'''
    s = s.replace(old_try, new_try)
    assert 'const CORRECT = ' in s
    s = re.sub(r'const CORRECT = \d+;[^\n]*', f"const CORRECT = {q['correct']};", s, count=1)

    # 6. тексты и ссылки
    s = s.replace(f"/books/{DONOR['slug']}/", f'/books/{slug}/')
    s = s.replace(f"/covers/{DONOR['slug']}.jpg", f'/covers/{slug}.jpg')
    assert DONOR['pitch'] in s
    s = s.replace(DONOR['pitch'], cfg['pitch'])
    cut = re.search(r'content="(Nobody at Volkswagen asked[^"]*)"', s)
    assert cut, 'обрезанный питч не найден'
    s = s.replace(cut.group(1), cfg['pitch'][:len(cut.group(1))].rsplit(' ', 1)[0])
    ld = re.search(r'<script type="application/ld\+json">(.*?)</script>', s, re.S)
    s = s[:ld.start(1)] + ld.group(1).replace(f'"{DONOR["title_raw"]}', f'"{cfg["title_raw"]}') + s[ld.end(1):]
    s = s.replace(DONOR['title_raw'].replace('&', '&amp;'), title)
    s = s.replace(DONOR['title_raw'], cfg['title_raw'])
    s = s.replace(DONOR['short'], cfg['short'])

    # 7. КНОПКИ ПОКУПКИ → блок «скоро». Ссылок на Amazon у книги без ASIN быть не должно.
    buy = re.search(r'<a class="btn primary" href="https://www\.amazon\.com/dp/[A-Z0-9]+"[^>]*>[^<]*</a>\s*'
                    r'<a class="btn ghost" href="https://www\.amazon\.com/dp/[A-Z0-9]+"[^>]*>[^<]*</a>', s)
    assert buy, 'кнопки покупки не найдены'
    s = s[:buy.start()] + (
        f'<span class="btn primary" style="cursor:default">{cfg["when"]} on Amazon</span>\n'
        f'        <span class="btn ghost" style="cursor:default">Paperback &amp; Kindle</span>'
    ) + s[buy.end():]
    # подпись под кнопками говорила так, будто книга уже в продаже
    ship = 'Ships worldwide from Amazon \u00b7 Great as a gift'
    assert ship in s, 'подпись под кнопками не найдена'
    s = s.replace(ship, cfg['soon_line'])
    s = re.sub(r'https://www\.amazon\.com/dp/[A-Z0-9]+', f'https://janwalkerbooks.com/books/{slug}/', s)
    s = s.replace(DONOR['pb'], '').replace(DONOR['kin'], '')

    # 7б. Секция отзывов: у книги без ASIN она строит битую ссылку
    # https://www.amazon.com/dp/#customerReviews, да и отзывов быть ещё не может.
    rv = re.search(r'<section[^>]*id="review".*?</section>', s, re.S)
    assert rv, 'секция отзывов не найдена'
    s = s[:rv.start()] + s[rv.end():]
    # и её скрипт, который обращается к пустому ASIN
    for anchor in ('rv-main', 'rv-all'):
        assert anchor not in s.split('<script')[0], anchor
    sc = re.search(r'<script>(?:(?!</script>).)*rv-main(?:(?!</script>).)*</script>', s, re.S)
    if sc:
        s = s[:sc.start()] + s[sc.end():]

    # следов донора не осталось нигде, кроме карточек соседей
    old_also = re.search(r'<div class="also">.*?</div></a></div>', s, re.S).group(0)
    cards = '\n'.join(f'<a href="/books/{sl}/"><img src="{nb}" alt="{nm} cover"><div class="t">{nm}</div></a>'
                      for (sl, nm, _), nb in zip(cfg['also'], new_blobs[1:]))
    s = s.replace(old_also, f'<div class="also">{cards}</div>')
    probe = re.sub(r'<div class="also">.*?</div>\n  </div>', '', s, flags=re.S)
    probe = re.sub(r'data:image/\w+;base64,[A-Za-z0-9+/=]+', '', probe)
    leftovers = re.findall(DONOR['leftovers'], probe)
    assert not leftovers, f'остались следы донора: {set(leftovers)}'
    assert 'amazon.com/dp/' not in s, 'осталась ссылка на несуществующий товар'
    json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', s, re.S).group(1))

    out = DEPLOY / 'books' / slug
    out.mkdir(parents=True, exist_ok=True)
    (out / 'index.html').write_text(s)
    cov = Image.open(KDP / cfg['book'] / f"{cfg['book']}-ebook-cover.jpg").convert('RGB')
    cov = cov.resize((1000, round(cov.height * 1000 / cov.width)), Image.LANCZOS)
    cov.save(DEPLOY / 'covers' / f'{slug}.jpg', 'JPEG', quality=85, optimize=True)
    print(f'books/{slug}/index.html  {len(s)/1e3:.0f} KB  ·  video {vname}  ·  aplus '
          + ', '.join(sorted(p.name for p in apd.iterdir())))


if __name__ == '__main__':
    for a in sys.argv[1:]:
        build(a)
