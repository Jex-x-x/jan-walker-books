#!/usr/bin/env python3
"""Собирает страницу источников книги про Pajero Sport: по одному блоку на вопрос,
с самим вопросом, проверенным утверждением и живыми ссылками.

Шрифты берутся из уже собранной страницы соседней книги (там они вшиты base64),
чтобы не тянуть TTF и не расходиться с оформлением сайта.
"""
import io, json, re, html
from pathlib import Path

DEPLOY = Path(__file__).resolve().parent
BOOK   = Path('/Users/jexxx/autopapyrus-kdp/pajerosport-classic')
OUT    = DEPLOY / 'books' / 'pajerosport' / 'sources' / 'index.html'

src    = json.load(io.open(BOOK / 'sources.json', encoding='utf-8'))
report = json.load(io.open(BOOK / 'pajerosport-classic-trivia-v1-en.factcheck.json', encoding='utf-8'))

# Шрифты подключаем ссылкой, а не base64. Вшитые TTF давали 353 КБ из 449 —
# 78% страницы, — и веб-читалки на такой странице спотыкались. Начертания те же,
# что на остальном сайте (Anton, Lora), плюс честный запасной стек.
FONTS = ''
FONT_LINK = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
             '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
             '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
             'family=Anton&family=Lora:wght@400;600&display=swap">')

# Заметки в sources.json — рабочие; где в них кухня правок (даты, «в черновике было»),
# на страницу идёт чистый текст. Сами правки перечислены открыто в блоке исправлений.
PUBLIC_NOTE = {
    '1.1': 'Mitsubishi company history: named after Leopardus pajeros, the pampas cat of the Patagonian plateau, to suggest a harmony between "taste of the wild" and "beauty".',
    '4.6': 'Frame welding site set up in 2013 for the previous generation; one trade report, with the vehicle maker\'s own background.',
    '4.9': 'Chittagong plant of Pragoti Industries Limited; the state-owned company has assembled and sold Mitsubishi models in Bangladesh since 1977 (Automotive World).',
    '5.3': 'Australian reviewers called the lamps polarising; the lamps were shortened at the 2019 facelift.',
    '7.9': '2025 Australian brochure: the range is GLS and Exceed only, both with a rear differential lock; no front differential lock is listed.',
}

PART_TITLES = {}
for r in report['results']:
    if r.get('part') and r.get('q'):
        PART_TITLES.setdefault(r['part'], None)

def host(u):
    m = re.match(r'https?://([^/]+)', u)
    return (m.group(1) if m else u).replace('www.', '')

def esc(t):
    return html.escape(t or '')

answers = [r for r in report['results'] if r['type'] == 'answer']
extras  = [r for r in report['results'] if r['type'] != 'answer']

rows = []
for r in answers:
    s = src[r['q']]
    links = ' '.join(
        f'<a href="{esc(u)}" rel="nofollow noopener" target="_blank">{esc(host(u))}</a>'
        for u in r['sources'])
    note_txt = PUBLIC_NOTE.get(r['q'], s.get('note', ''))
    note = f'<p class="note">{esc(note_txt)}</p>' if note_txt else ''
    flag = ''
    if 'CORRECT' in s.get('status','').upper():
        flag = '<span class="flag">corrected after review</span>'
    if len(r['sources']) < 2:
        flag += '<span class="flag solo">one source</span>'
    rows.append(f'''<article class="q" id="q{esc(r['q'])}">
<h3><span class="num">{esc(r['q'])}</span> {esc(r['question'])}{flag}</h3>
<p class="claim">{esc(s['claim'])}</p>{note}
<p class="links">{links}</p></article>''')

erows = []
for r in extras:
    kind = 'spec table' if r['type'] == 'spec_table' else f"box, part {r['part']}"
    links = ' '.join(
        f'<a href="{esc(u)}" rel="nofollow noopener" target="_blank">{esc(host(u))}</a>'
        for u in r['sources'])
    claim = re.sub(r'\s+', ' ', r['claim'])
    if len(claim) > 180:
        cut = claim[:180].rsplit(' ', 1)[0].rstrip(' ,.;:—-')
        claim = cut + ' …'
    note = f'<p class="note">{esc(r["notes"])}</p>' if r.get('notes') else ''
    erows.append(f'''<article class="q">
<h3><span class="num">{esc(kind)}</span> {esc(claim)}</h3>{note}
<p class="links">{links}</p></article>''')

revs = '\n'.join(
    f'<li><b>{esc(r["what_en"])}.</b> Was: {esc(r["was_en"])} → now: {esc(r["now_en"])}. {esc(r["why_en"])}</li>'
    for r in report['revisions'])

DOC = f'''<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sources — Pajero Sport Trivia &amp; Fun Facts — Jan Walker</title>
<link rel="icon" href="/favicon.ico?v=2" sizes="any">
<link rel="apple-touch-icon" href="/apple-touch-icon.png?v=2">
<meta name="description" content="Every one of the ninety questions in Pajero Sport Trivia &amp; Fun Facts, with the source that settles it. Manufacturer announcements, crash-test agencies and the trade press of each market — with the corrections made while checking listed openly.">
<link rel="canonical" href="https://janwalkerbooks.com/books/pajerosport/sources/">
<meta name="robots" content="noindex,nofollow">
<meta name="googlebot" content="noindex,nofollow">
<meta property="og:type" content="article">
<meta property="og:site_name" content="Jan Walker Books">
<meta property="og:title" content="Sources — Pajero Sport Trivia &amp; Fun Facts">
<meta property="og:description" content="All ninety questions, each with the source that settles it.">
<meta property="og:url" content="https://janwalkerbooks.com/books/pajerosport/sources/">
{FONT_LINK}
<style>
{FONTS}
:root {{ --paper:#f6f1e5; --paper-deep:#efe8d6; --card:#fcf9f0; --ink:#1d2130;
  --ink-soft:#454a59; --ink-faint:#948e7d; --line:#ddd3bd; --line-soft:#e8e0cc;
  --accent:#d95314; --ok:#2e6b3f; }}
* {{ box-sizing:border-box; }}
body {{ background:var(--paper); color:var(--ink); font-family:'Lora',Georgia,serif;
  font-size:17px; line-height:1.65; margin:0; }}
.wrap {{ max-width:820px; margin:0 auto; padding:0 22px 90px; }}
header {{ border-bottom:1px solid var(--line); padding:46px 0 26px; margin-bottom:34px; }}
.kicker {{ font-family:'Anton',Impact,sans-serif; letter-spacing:.14em; text-transform:uppercase;
  font-size:13px; color:var(--accent); margin:0 0 10px; }}
h1 {{ font-family:'Anton',Impact,sans-serif; font-weight:400; font-size:clamp(30px,6vw,46px);
  line-height:1.06; letter-spacing:.01em; margin:0 0 14px; text-transform:uppercase; }}
h2 {{ font-family:'Anton',Impact,sans-serif; font-weight:400; text-transform:uppercase;
  letter-spacing:.05em; font-size:22px; margin:52px 0 6px; }}
h2 + .sub {{ color:var(--ink-faint); margin:0 0 22px; font-size:15px; }}
.lede {{ color:var(--ink-soft); margin:0 0 6px; }}
.rule {{ width:64px; height:3px; background:var(--accent); border:0; margin:0 0 20px; }}
.q {{ border-top:1px solid var(--line-soft); padding:18px 0 16px; }}
.q h3 {{ font-family:'Lora',Georgia,serif; font-weight:600; font-size:17px; margin:0 0 6px;
  line-height:1.5; }}
.num {{ display:inline-block; font-family:'Anton',Impact,sans-serif; font-weight:400;
  font-size:12px; letter-spacing:.08em; text-transform:uppercase; color:var(--ink-faint);
  border:1px solid var(--line); border-radius:100px; padding:1px 9px; margin-right:8px;
  vertical-align:2px; white-space:nowrap; }}
.claim {{ margin:0 0 4px; color:var(--ink); }}
.claim::before {{ content:"Verified: "; color:var(--ink-faint); font-size:14px; }}
.note {{ margin:0 0 6px; color:var(--ink-soft); font-size:15px; }}
.links a {{ display:inline-block; font-size:13px; color:var(--accent); text-decoration:none;
  border:1px solid var(--line); border-radius:100px; padding:2px 11px; margin:3px 5px 0 0;
  background:var(--card); word-break:break-word; }}
.links a:hover {{ border-color:var(--accent); }}
.links {{ margin:6px 0 0; }}
.flag.solo {{ background:transparent; color:var(--ink-faint); border:1px solid var(--line); }}
.flag {{ font-family:'Anton',Impact,sans-serif; font-size:11px; letter-spacing:.08em;
  text-transform:uppercase; color:#fff; background:var(--accent); border-radius:100px;
  padding:2px 9px; margin-left:8px; white-space:nowrap; }}
.card {{ background:var(--card); border:1px solid var(--line); border-radius:14px;
  padding:20px 22px; margin:26px 0 0; }}
.card ul {{ margin:10px 0 0; padding-left:20px; }}
.card li {{ margin-bottom:9px; color:var(--ink-soft); font-size:16px; }}
footer {{ border-top:1px solid var(--line); margin-top:56px; padding-top:22px;
  color:var(--ink-faint); font-size:14px; }}
footer a {{ color:var(--accent); }}
@media (prefers-color-scheme: dark) {{ }}
</style>
<div class="wrap">
<header>
<p class="kicker">Jan Walker Books · sources</p>
<h1>Pajero Sport Trivia &amp; Fun Facts</h1>
<hr class="rule">
<p class="lede">Ninety questions, and for each of them the source that settles it. Mitsubishi's
own announcements supply the launch dates, plant openings, engine and transmission firsts and the
plans for the new Pajero. Crash-test results come from ANCAP and Latin NCAP directly. Capability
figures — towing, fording, angles — come from Mitsubishi Australia's published specifications and
are marked as Australian. Sales and discontinuation decisions come from the trade press of the
market concerned.</p>
<p class="lede">Wikipedia was used to find primary sources and is never the only source for an
answer; owner forums tell you which question to ask, never the answer. Every one of the ninety
answers rests on at least two sources. Five of the boxes rest on one — mostly the maker describing
its own factory or its own equipment — and each is marked <span class="flag solo">one source</span>.
Where two respectable sources disagree, the book says so in the answer rather than choosing the
more impressive number.</p>
</header>

<h2>Corrections made while checking</h2>
<p class="sub">Found by checking every claim one at a time and in an independent review before
publication; the last three were found after publication, on the reference pages at the back of
the book, and corrected in the files submitted to Amazon on 14 September 2026. Listed here rather than quietly applied.</p>
<div class="card"><ul>
{revs}
</ul></div>

<h2>The ninety questions</h2>
<p class="sub">Numbered part.question, in the order they appear in the book.</p>
{chr(10).join(rows)}

<h2>Boxes and the specification table</h2>
<p class="sub">The boxes inside the parts, and the summary table at the front —
{len(extras)} further claims, checked the same way.</p>
{chr(10).join(erows)}

<footer>
<p>Last checked {esc(report['generated'])}. {esc(str(report['total_claims']))} claims, every one
with a source. If you find something wrong here, that is worth knowing —
<a href="https://janwalkerbooks.com/">janwalkerbooks.com</a>.</p>
</footer>
</div>
'''

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(DOC, encoding='utf-8')
print(f'{OUT} — {len(DOC):,} байт, вопросов {len(answers)}, доп. утверждений {len(extras)}')
