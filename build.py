#!/usr/bin/env python3
"""Собирает self-contained index.html: шрифты и обложки инлайнятся base64."""
import base64, io, sys
from pathlib import Path
from PIL import Image

ROOT = Path('/Users/jexxx/autopapyrus-kdp')
SITE = ROOT / 'site'

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


def cover_datauri(path, width=420, quality=80):
    im = Image.open(path).convert('RGB')
    h = round(im.height * width / im.width)
    im = im.resize((width, h), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, 'JPEG', quality=quality, optimize=True, progressive=True)
    return 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()


def main():
    html = (SITE / 'index.template.html').read_text()

    for token, path in FONTS.items():
        html = html.replace('{{%s}}' % token, base64.b64encode(path.read_bytes()).decode())

    uris = {}
    for slug, path in COVERS.items():
        uris[slug] = cover_datauri(path)
        html = html.replace('{{COVER_%s}}' % slug, uris[slug])

    cover_map = ', '.join("'%s': '%s'" % (slug, uri) for slug, uri in uris.items())
    html = html.replace('{{COVER_MAP}}', cover_map)

    leftovers = [l for l in ('{{',) if l in html]
    out = SITE / 'index.html'
    out.write_text(html)
    print('written', out, f'{out.stat().st_size / 1e6:.2f} MB', 'leftover tokens:', bool(leftovers))
    if leftovers:
        import re
        print(set(re.findall(r'{{[A-Z_a-z0-9]+}}', html)))


if __name__ == '__main__':
    main()
