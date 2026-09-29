#!/usr/bin/env python3
"""Вставка счётчика посещаемости во все страницы сайта.

    python3 add_analytics.py                  # сухой прогон, GoatCounter
    python3 add_analytics.py --go             # записать
    python3 add_analytics.py G-N9W5S95JNL --go   # Google Аналитика

Тег ставится последним перед </head>, чтобы не тормозить отрисовку.
Повторный запуск ничего не портит: страницы с уже вставленным тегом пропускаются.
"""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent
args = [a for a in sys.argv[1:] if not a.startswith('--')]
SITE = args[0] if args else 'janwalker-books'
GO = '--go' in sys.argv

if SITE.startswith('G-'):                      # Google Аналитика 4
    MARK = 'googletagmanager.com/gtag/js'
    TAG = (
        '<script async src="https://www.googletagmanager.com/gtag/js?id={s}"></script>\n'
        '<script>window.dataLayer=window.dataLayer||[];'
        'function gtag(){{dataLayer.push(arguments);}}'
        "gtag('js',new Date());gtag('config','{s}');</script>\n"
    ).format(s=SITE)
else:                                          # GoatCounter: без куки и баннеров о согласии
    MARK = 'goatcounter.com/count'
    TAG = (
        '<script data-goatcounter="https://{s}.goatcounter.com/count" '
        'async src="//gc.zgo.at/count.js"></script>\n'
    ).format(s=SITE)

changed, skipped = [], []
for f in sorted(ROOT.rglob('*.html')):
    s = f.read_text(encoding='utf-8')
    if MARK in s:
        skipped.append(str(f.relative_to(ROOT))); continue
    # у страниц сайта нет тегов <head>/</head> — браузер достраивает их сам,
    # поэтому цепляемся к концу блока стилей, а если его нет — к <title>
    if '</head>' in s:
        s = s.replace('</head>', TAG + '</head>', 1)
    elif '</style>' in s:
        s = s.replace('</style>', '</style>\n' + TAG, 1)
    elif '</title>' in s:
        s = s.replace('</title>', '</title>\n' + TAG, 1)
    else:
        skipped.append(str(f.relative_to(ROOT))); continue
    changed.append(str(f.relative_to(ROOT)))
    if GO:
        f.write_text(s, encoding='utf-8')

print(('ЗАПИСАНО' if GO else 'СУХОЙ ПРОГОН') + f': страниц со счётчиком {len(changed)}, пропущено {len(skipped)}')
for c in changed[:5]:
    print('  +', c)
if skipped:
    print('  пропущено, напр.:', skipped[:3])
