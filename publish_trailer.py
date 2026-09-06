#!/usr/bin/env python3
"""Положить на сайт КВАДРАТНЫЙ трейлер книги и переключить на него страницу.

Зачем отдельный скрипт: build.py на сайте больше не гоняется целиком (страницы
правятся точечно), а видео на восьми страницах уехало на вертикальные шортсы для
YouTube. Здесь та же логика, что в build.py: версионное имя по размеру файла,
постер с 17.6 с, плюс правка готового index.html.

  python3 publish_trailer.py <slug> [<slug> ...]
"""
import re, shutil, subprocess, sys
from pathlib import Path

ROOT = Path('/Users/jexxx/autopapyrus-kdp')
DEPLOY = ROOT / 'site/_deploy'
VDIR = DEPLOY / 'video'

def dur(p):
    out = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
                          '-show_entries', 'stream=width,height,duration',
                          '-of', 'csv=p=0', str(p)], capture_output=True, text=True).stdout.strip()
    w, h, d = out.split(',')[:3]
    return int(w), int(h), float(d)

for slug in sys.argv[1:]:
    src = ROOT / f'video/out/{slug}-promo.mp4'
    page = DEPLOY / f'books/{slug}/index.html'
    if not src.exists(): print(f'❌ {slug}: нет {src}'); continue
    if not page.exists(): print(f'❌ {slug}: нет страницы'); continue
    w, h, d = dur(src)
    if w != h: print(f'❌ {slug}: мастер не квадратный ({w}x{h})'); continue

    ver = src.stat().st_size
    vname, pname = f'{slug}-promo-{ver}.mp4', f'{slug}-promo-{ver}-poster.jpg'
    shutil.copy(src, VDIR / vname)
    shutil.copy(src, VDIR / f'{slug}-promo.mp4')
    subprocess.run(['ffmpeg', '-y', '-ss', '17.6', '-i', str(src), '-frames:v', '1',
                    '-q:v', '4', str(VDIR / pname), '-loglevel', 'error'], check=True)

    s = page.read_text()
    before = re.search(r'<video[^>]*>\s*<source src="([^"]+)"', s)
    s2 = re.sub(r'<video class="(?:vertical|wide)"', '<video class="wide"', s)
    s2 = re.sub(r'(<video class="wide"[^>]*poster=")[^"]+(")', rf'\g<1>/video/{pname}\g<2>', s2)
    s2 = re.sub(r'(<source src=")[^"]+(" type="video/mp4">)', rf'\g<1>/video/{vname}\g<2>', s2)
    s2 = re.sub(r'<h2>The \d+-second tour\.</h2>', f'<h2>The {round(d/5)*5:.0f}-second tour.</h2>', s2)
    if s2 == s:
        print(f'…  {slug}: страница уже такая')
    else:
        page.write_text(s2)
        print(f'✅ {slug}: {before.group(1) if before else "?"} → /video/{vname}  ({w}x{h}, {d:.1f} с)')
