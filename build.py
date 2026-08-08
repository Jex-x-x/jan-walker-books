#!/usr/bin/env python3
"""Собирает сайт: index.html + books/<slug>/index.html + covers/*.jpg + og.jpg.
Всё self-contained (шрифты/обложки base64), covers/ и og.jpg — публичные файлы для og:image.
"""
import base64, importlib.util, io, shutil, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path('/Users/jexxx/autopapyrus-kdp')
SITE = ROOT / 'site'
DEPLOY = SITE / '_deploy'
CFG_DIR = ROOT / 'aplus-batch' / 'configs'

COVERS = {
    'miata':     ROOT / 'miata/miata-ebook-cover.jpg',
    'supra':     ROOT / 'supra/supra-ebook-cover.jpg',
    'skyline':   ROOT / 'skyline/skyline-ebook-cover.jpg',
    'wrx':       ROOT / 'wrx/wrx-ebook-cover.jpg',
    'mustang':   ROOT / 'mustang/mustang-ebook-cover.jpg',
    'silverado': ROOT / 'silverado/silverado-ebook-cover.jpg',
    'gwagon':    ROOT / 'gwagon/gwagon-ebook-cover.jpg',
    'tacoma':    ROOT / 'tacoma/tacoma-ebook-cover.jpg',
    'f150':      ROOT / 'f150/f150-ebook-cover.jpg',
    '4runner':   ROOT / '4runner/4runner-ebook-cover.jpg',
    'tundra':    ROOT / 'tundra/tundra-ebook-cover.jpg',
    'explorer':  ROOT / 'explorer/explorer-ebook-cover.jpg',
    'grandpa':   ROOT / 'grandpa/grandpa-ebook-cover.jpg',
    'grandma':   ROOT / 'grandma/grandma-ebook-cover.jpg',
    'dad':       ROOT / 'dad/dad-ebook-cover.jpg',
    'mom':       ROOT / 'mom/mom-ebook-cover.jpg',
    'daughter':  ROOT / 'daughter/daughter-ebook-cover.jpg',
    'son':       ROOT / 'son/son-ebook-cover.jpg',
    'halloween': ROOT / 'halloween/halloween-ebook-cover.jpg',
}

FONTS = {
    'FONT_ANTON':  Path('/tmp/Anton-Regular.ttf'),
    'FONT_LORA':   Path('/tmp/Lora-Regular.ttf'),
    'FONT_LORA_B': Path('/tmp/Lora-Bold.ttf'),
}

CARS_SERIES = 'Trivia & Fun Facts · Cars & Trucks'
FAM_SERIES = 'Family Table Books'

# slug -> (short, полный тайтл, серия, PB ASIN, Kindle ASIN, pitch)
BOOKS = {
    'miata':     ('Mazda MX-5 Miata Trivia', 'Mazda MX-5 Miata Trivia & Fun Facts', CARS_SERIES, 'B0H3NK9YGJ', 'B0H659WDTG',
                  'Over a million cars and a Guinness record: the best-selling two-seat roadster ever built. Ninety verified questions across four generations of the car that saved the affordable sports car — pop-up headlights included.'),
    'supra':     ('Toyota Supra Trivia', 'Toyota Supra Trivia & Fun Facts', CARS_SERIES, 'B0H3T3LZYD', 'B0H6BRCWB3',
                  'The 2JZ legend told properly — from its quiet debut in a luxury sedan to 1,000-horsepower street builds on stock internals. Ninety verified questions across five generations of Toyota’s icon.'),
    'skyline':   ('Skyline GT-R Trivia', 'Skyline GT-R Trivia & Fun Facts', CARS_SERIES, 'B0HCZWQSG9', 'B0HD143CD4',
                  'They called it Godzilla, and it earned the name. From the Prince years to the last BNR34, ninety verified questions about the GT-R — including the rulebook math that made the RB26 exactly 2,568 cc.'),
    'wrx':       ('Subaru WRX Trivia', 'Subaru WRX Trivia & Fun Facts', CARS_SERIES, 'B0HD8FX51M', 'B0HD9GGXV2',
                  'Subaru built a rally car and sold the public whatever the rulebook demanded. McRae, the 555 years, all 424 examples of the 22B — ninety verified questions across three decades of boxer-engine legend.'),
    'mustang':   ('Ford Mustang Trivia', 'Ford Mustang Trivia & Fun Facts', CARS_SERIES, 'B0HBXPPWCJ', 'B0HBX98HDG',
                  'America’s original pony car: 418,000 sold in year one, a record that stood for decades. Ninety verified questions across seven generations, from the World’s Fair debut to the present day.'),
    'silverado': ('Chevy Silverado Trivia', 'Silverado Trivia & Fun Facts', CARS_SERIES, 'B0HCK8655N', 'B0HCJM5VBG',
                  'For 24 years Silverado wasn’t a truck — it was a trim level named after a California silver-mining town. Ninety verified questions across four generations of Chevy’s full-size workhorse.'),
    'gwagon':    ('Mercedes G-Wagon Trivia', 'G-Wagon Trivia & Fun Facts', CARS_SERIES, 'B0HBT4F5H3', 'B0HCHW5B98',
                  'Born from a royal order that died with a regime, sixteen days before production began. Ninety verified questions about the military box that conquered Beverly Hills without ever changing shape.'),
    'tacoma':    ('Toyota Tacoma Trivia', 'Toyota Tacoma Trivia & Fun Facts', CARS_SERIES, 'B0H3LRD3YF', 'B0H3VY2HDH',
                  'One generation, eleven years — and it still outsold every rival in its final season. Ninety verified questions about the midsize truck that refused to lose, from Hilux roots to TRD Pro.'),
    'f150':      ('Ford F-150 Trivia', 'F-150 Truck Trivia & Fun Facts', CARS_SERIES, 'B0H3NYC85Q', 'B0H6C7D469',
                  'The truck that made twin turbos respectable in half-ton country: the 2011 EcoBoost outsold the V8 within a year. Ninety verified questions about America’s long-reigning best-seller.'),
    '4runner':   ('Toyota 4Runner Trivia', 'Toyota 4Runner Trivia & Fun Facts', CARS_SERIES, 'B0H41QVRGC', 'B0H3TFKQBL',
                  'Fifteen model years on one chassis — the longest single-generation run of any modern midsize SUV, and a cult formed around the receipt. Ninety verified questions from truck-topper origins to TRD Pro.'),
    'tundra':    ('Toyota Tundra Trivia', 'Toyota Tundra Trivia & Fun Facts', CARS_SERIES, 'B0H49SCLH2', 'B0H47VPLRH',
                  'The 5.7 V8 that launched at 381 hp in 2007 and ran nearly unchanged for thirteen years while rivals kept blinking. Ninety verified questions about Toyota’s full-size gamble that paid off.'),
    'explorer':  ('Ford Explorer Trivia', 'Ford Explorer Trivia & Fun Facts', CARS_SERIES, 'B0HC3X71SD', 'B0HC3R48L9',
                  'The SUV that chauffeured Jurassic Park and half of the 1990s. Ninety verified questions about the truck that taught America to buy SUVs — school runs, silver screens and all.'),
    'grandpa':   ('Grandpa Trivia', 'Grandpa Trivia: 90 Things Your Grandpa Probably Knew', FAM_SERIES, 'B0H7N6B5KR', 'B0H6LXSJR4',
                  'The 9-volt tongue test, points and condensers, why he saved every jar of screws. Ninety verified questions about the things grandpa probably knew — few of which help you today, all of which explain him.'),
    'grandma':   ('Grandma Trivia', 'Grandma Trivia: 90 Things Your Grandmother Quietly Knew', FAM_SERIES, 'B0H7N21RMX', 'B0H6M78MKH',
                  'Pyrex that never wore out, the phone-tree, the hospitality code. Ninety verified questions about the things your grandmother quietly knew — and that you’d honestly love to know too.'),
    'dad':       ('Dad Trivia', 'Dad Trivia: 90 Things Your Dad Absolutely Insists On', FAM_SERIES, 'B0H7NN36T6', 'B0H7NT6S47',
                  'The steak comes off at 128°F, the thermostat is not a toy, and the gas station on the left is always cheaper. Ninety verified questions about the things dad absolutely insists on. Some are even true.'),
    'mom':       ('Mom Trivia', 'Mom Trivia: 90 Things Your Mom Has Already Told You Twice', FAM_SERIES, 'B0H7SCBZZG', 'B0H7RVGVP3',
                  'She remembers every birthday, reads the group chat like a wire service, and told you all of this twice already. Ninety verified questions celebrating the household’s memory backup layer.'),
    'daughter':  ('Daughter Trivia', 'Daughter Trivia: 90 Things Your Daughter Does, Says, and Believes', FAM_SERIES, 'B0H7SS3HSH', 'B0H4X54W5P',
                  'The best friend rotates every 2–3 weeks, and that’s developmentally correct. Ninety verified questions about what daughters do, say and believe — with the actual science behind the chaos.'),
    'son':       ('Son Trivia', 'Son Trivia: 90 Things Your Son Does, Says, and Believes', FAM_SERIES, 'B0H7SWYJCR', 'B0H7SQJPYM',
                  'The pillow faces the door because the label has to be on the right. Ninety verified questions about what sons do, say and believe — including the just-right rituals every parent recognizes.'),
    'halloween': ('Halloween Trivia', 'Halloween Trivia: 90 Things You Think You Know About Halloween', FAM_SERIES.replace('Family Table Books', 'Seasonal Shelf'), 'B0H87S7S1P', 'B0H88FWX5H',
                  'Candy corn, Samhain, and the great razor-blade panic that never actually happened. Ninety verified questions for the household know-it-all — the October book that settles the porch arguments.'),
}

ALSO = {  # 4 соседа для «Also on this shelf»
    **{s: [x for x in ['miata', 'supra', 'skyline', 'wrx', 'mustang'] if x != s][:4]
       for s in ['miata', 'supra', 'skyline', 'wrx', 'mustang', 'silverado', 'gwagon', 'tacoma', 'f150', '4runner', 'tundra', 'explorer']},
    **{s: [x for x in ['grandpa', 'grandma', 'dad', 'mom', 'daughter'] if x != s][:4]
       for s in ['grandpa', 'grandma', 'dad', 'mom', 'daughter', 'son', 'halloween']},
}


def load_cfg(slug):
    p = CFG_DIR / (slug + '.py')
    if not p.exists():
        return None
    sys.path.insert(0, str(CFG_DIR.parent))
    spec = importlib.util.spec_from_file_location('cfg_' + slug, p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.BOOK


def cover_datauri(path, width=420, quality=80):
    im = Image.open(path).convert('RGB')
    h = round(im.height * width / im.width)
    im = im.resize((width, h), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, 'JPEG', quality=quality, optimize=True, progressive=True)
    return 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def build_og():
    """og.jpg 1200×630 для главной."""
    W, H = 1200, 630
    im = Image.new('RGB', (W, H), (246, 241, 229))
    d = ImageDraw.Draw(im)
    anton = ImageFont.truetype(str(FONTS['FONT_ANTON']), 96)
    anton_s = ImageFont.truetype(str(FONTS['FONT_ANTON']), 30)
    lora = ImageFont.truetype(str(FONTS['FONT_LORA']), 26)
    x = 64
    d.text((x, 96), 'BOOKS THAT', font=anton, fill=(29, 33, 48))
    d.text((x, 196), 'START', font=anton, fill=(217, 83, 20))
    d.text((x, 296), 'ARGUMENTS.', font=anton, fill=(29, 33, 48))
    d.rectangle([x, 420, x + 130, 425], fill=(198, 15, 46))
    d.text((x, 448), '19 trivia books · every fact verified twice', font=lora, fill=(69, 74, 89))
    d.text((x, 496), 'TAKE THE ENTRANCE EXAM · JANWALKERBOOKS.COM', font=anton_s, fill=(148, 142, 125))
    covers = ['supra', 'grandpa', 'wrx']
    cx = 760
    for i, slug in enumerate(covers):
        cov = Image.open(COVERS[slug]).convert('RGB')
        cw = 240
        ch = round(cov.height * cw / cov.width)
        cov = cov.resize((cw, ch), Image.LANCZOS)
        rot = cov.rotate([-7, 4, -3][i], expand=True, fillcolor=(246, 241, 229))
        im.paste(rot, (cx + i * 120 - 60, 90 + [40, 10, 80][i]))
    im.save(DEPLOY / 'og.jpg', 'JPEG', quality=88)
    print('og.jpg written')


def main():
    (DEPLOY / 'covers').mkdir(exist_ok=True, parents=True)
    fonts64 = {k: base64.b64encode(p.read_bytes()).decode() for k, p in FONTS.items()}

    # публичные обложки для og:image детальных страниц
    for slug, path in COVERS.items():
        im = Image.open(path).convert('RGB')
        w = 1000
        im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
        im.save(DEPLOY / 'covers' / (slug + '.jpg'), 'JPEG', quality=85, optimize=True)

    # -------- главная --------
    html = (SITE / 'index.template.html').read_text()
    for tok, val in fonts64.items():
        html = html.replace('{{%s}}' % tok, val)
    uris = {slug: cover_datauri(path) for slug, path in COVERS.items()}
    for slug, uri in uris.items():
        html = html.replace('{{COVER_%s}}' % slug, uri)
    html = html.replace('{{COVER_MAP}}', ', '.join("'%s': '%s'" % (s, u) for s, u in uris.items()))
    (SITE / 'index.html').write_text(html)
    shutil.copy(SITE / 'index.html', DEPLOY / 'index.html')
    print('index.html', f"{(SITE / 'index.html').stat().st_size / 1e6:.2f} MB")

    # -------- детальные страницы --------
    tpl = (SITE / 'book.template.html').read_text()
    for tok, val in fonts64.items():
        tpl = tpl.replace('{{%s}}' % tok, val)

    for slug, (short, title, series, pb, kindle, pitch) in BOOKS.items():
        cfg = load_cfg(slug)
        page = tpl
        page = page.replace('{{SLUG}}', slug)
        page = page.replace('{{SHORT}}', esc(short))
        page = page.replace('{{TITLE}}', esc(title))
        page = page.replace('{{SERIES}}', esc(series))
        page = page.replace('{{PITCH}}', esc(pitch))
        page = page.replace('{{META_DESC}}', esc(pitch[:250]))
        page = page.replace('{{AMZ_PB}}', f'https://www.amazon.com/dp/{pb}')
        page = page.replace('{{AMZ_K}}', f'https://www.amazon.com/dp/{kindle}')
        page = page.replace('{{COVER_MAIN}}', cover_datauri(COVERS[slug], width=640, quality=82))

        # Parts
        if cfg and cfg.get('chapters'):
            parts = '\n'.join(
                f'<div class="part"><span class="num">{esc(n)}</span><span><span class="pt">{esc(t)}.</span> <span class="ps">{esc(s)}</span></span></div>'
                for n, t, s in cfg['chapters'])
            parts_section = f'''<section id="inside">
  <div class="wrap">
    <div class="sec-head">
      <div class="kicker">What's inside</div>
      <h2>Ten parts. Ninety questions.</h2>
      <div class="rule"></div>
    </div>
    <div class="parts">{parts}</div>
  </div>
</section>'''
        else:
            parts_section = ''
        page = page.replace('{{PARTS_SECTION}}', parts_section)

        # Sample question
        q = cfg.get('sample_q') if cfg else None
        if q:
            page = page.replace('{{Q_LOCATION}}', esc(q.get('location', 'From the book')))
            page = page.replace('{{Q_PROMPT}}', esc(' '.join(q['prompt'])))
            page = page.replace('{{Q_OPTIONS}}', '\n'.join(
                f'<button class="opt"><span class="tag">{L}</span><span>{esc(o)}</span></button>'
                for L, o in q['options']))
            page = page.replace('{{Q_CORRECT}}', str([L for L, _ in q['options']].index(q['correct'])))
            page = page.replace('{{Q_STORY}}', esc(' '.join(q['story'])))
        else:
            # без конфига (halloween): вырезаем секцию try целиком
            start = page.index('<section id="try">')
            end = page.index('</section>', start) + len('</section>')
            page = page[:start] + page[end:]
            page = page.replace('{{Q_CORRECT}}', '0')
        page = page.replace('{{Q_PAGE_HINT}}', 'the book')

        # Also on this shelf
        also = '\n'.join(
            f'<a href="/books/{s}/"><img src="{cover_datauri(COVERS[s], width=300, quality=78)}" alt="{esc(BOOKS[s][0])} cover"><div class="t">{esc(BOOKS[s][0])}</div></a>'
            for s in ALSO[slug])
        page = page.replace('{{ALSO_CARDS}}', also)

        out = DEPLOY / 'books' / slug
        out.mkdir(exist_ok=True, parents=True)
        (out / 'index.html').write_text(page)

    print('book pages:', len(BOOKS))
    build_og()

    leftover = '{{' in (DEPLOY / 'books' / 'miata' / 'index.html').read_text()
    print('leftover tokens in book pages:', leftover)


if __name__ == '__main__':
    main()
