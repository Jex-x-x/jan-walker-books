#!/usr/bin/env python3
"""Собирает страницу источников книги про Tesla: по одному блоку на вопрос,
с самим вопросом, проверенным утверждением и живыми ссылками.

Шрифты берутся из уже собранной страницы соседней книги (там они вшиты base64),
чтобы не тянуть TTF и не расходиться с оформлением сайта.
"""
import io, json, re, html
from pathlib import Path

DEPLOY = Path(__file__).resolve().parent
TESLA  = Path('/Users/jexxx/autopapyrus-kdp/tesla')
OUT    = DEPLOY / 'books' / 'tesla' / 'sources' / 'index.html'

src    = json.load(io.open(TESLA / 'sources.json', encoding='utf-8'))
report = json.load(io.open(TESLA / 'tesla-trivia-v1-en.factcheck.json', encoding='utf-8'))

# шрифты сайта — вырезаем @font-face из готовой страницы
neighbour = (DEPLOY / 'books' / 'german' / 'index.html').read_text(encoding='utf-8')
faces = re.findall(r"@font-face\s*\{[^}]*\}", neighbour)
faces = [f for f in faces if 'Anton' in f or 'Lora' in f]
assert faces, 'не нашёл @font-face у соседней страницы'
FONTS = '\n'.join(faces)

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
    note = f'<p class="note">{esc(s.get("note",""))}</p>' if s.get('note') else ''
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
<title>Sources — Ultimate Tesla Challenge — Jan Walker</title>
<link rel="icon" href="/favicon.ico?v=2" sizes="any">
<link rel="apple-touch-icon" href="/apple-touch-icon.png?v=2">
<meta name="description" content="Every one of the ninety questions in Ultimate Tesla Challenge, with the source that settles it. Company filings, regulators and independent tests — with the corrections made in review listed openly.">
<link rel="canonical" href="https://janwalkerbooks.com/books/tesla/sources/">
<meta name="robots" content="index,follow">
<meta property="og:type" content="article">
<meta property="og:site_name" content="Jan Walker Books">
<meta property="og:title" content="Sources — Ultimate Tesla Challenge">
<meta property="og:description" content="All ninety questions, each with the source that settles it.">
<meta property="og:url" content="https://janwalkerbooks.com/books/tesla/sources/">
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
<h1>Ultimate Tesla Challenge</h1>
<hr class="rule">
<p class="lede">Ninety questions, and for each of them the source that settles it. Figures and
dates come from the company's own filings and from regulators wherever those exist; anything
a manufacturer had reason to phrase generously is checked against an independent test. Owner
forums are used to find out which question is worth asking, never to answer it.</p>
<p class="lede">Two retellings of one press release are one source, not two. Eight of these
entries rest on a single source; each is marked <span class="flag solo">one source</span> and
says in its note why a second was not found. Where the
record is genuinely disputed, the book says so in the answer instead of choosing the more
impressive number.</p>
</header>

<h2>Corrections made in review</h2>
<p class="sub">Found by re-checking every question one at a time, after a reviewer rejected a
part-by-part check. Listed here rather than quietly fixed.</p>
<div class="card"><ul>
{revs}
</ul></div>

<h2>The ninety questions</h2>
<p class="sub">Numbered part.question, in the order they appear in the book.</p>
{chr(10).join(rows)}

<h2>Boxes and the specification table</h2>
<p class="sub">The “did you know” box in each part, and the summary table at the front —
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
