#!/usr/bin/env python3
"""Убирает из галереи A+ на страницах книг модуль 4 «THE SERIES».

Он показывает ТУ ЖЕ 3D-обложку, что и баннер-модуль 1 — так собирает генератор
A+, и это одинаково у всех книг. На Amazon незаметно (баннер широкий, квадраты
мелкие), а у нас на телефоне модули идут в столбик во всю ширину, и получаются
два одинаковых мокапа подряд (Ян, 05.09.2026).

Плюс сам смысл модуля («другие книги серии») у нас уже закрыт родной секцией
«Also on this shelf» — там четыре РАЗНЫЕ обложки.

Скрипт идемпотентный. Запуск: python3 fix_aplus_dup.py
"""
import re
from pathlib import Path

D = Path(__file__).parent
done, skip = [], []
for root in (D / 'books', D / 'de' / 'books', D / 'es' / 'books'):
    if not root.exists():
        continue
    for d in sorted(root.iterdir()):
        f = d / 'index.html'
        if not f.exists():
            continue
        s = f.read_text()
        n = len(re.findall(r'<img src="/aplus/[^"]+/4\.jpg"[^>]*>\s*\n?', s))
        if not n:
            skip.append(d.name); continue
        s = re.sub(r'\s*<img src="/aplus/[^"]+/4\.jpg"[^>]*>', '', s)
        # три колонки на два квадрата оставили бы дыру справа
        s = s.replace('.aplus-squares { max-width: 900px; margin: 22px auto 0; display: grid; grid-template-columns: repeat(3, 1fr); gap: 22px; }',
                      '.aplus-squares { max-width: 900px; margin: 22px auto 0; display: grid; grid-template-columns: repeat(2, 1fr); gap: 22px; }')
        f.write_text(s)
        done.append(f'{root.parent.name if root.parent != D else "en"}/{d.name}')
print(f'модуль-дубль убран со страниц: {len(done)}')
if skip:
    print('без модуля 4 (пропущены):', skip)
