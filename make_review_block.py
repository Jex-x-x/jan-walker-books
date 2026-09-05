#!/usr/bin/env python3
"""Блок «уже прочитали? оставьте отзыв» на страницах книг.

Отдельных страниц под это НЕ заводим (было 29 штук — Ян: «запутаемся со
страницами», и он прав: генератор их уже один раз собрал только по английским
книгам и молча пропустил немецкие и испанские). Блок живёт на странице книги,
которая и так есть, и берёт номер издания из той же строки, что и кнопка
покупки, — разъехаться нечему.

Витрину не выбираем за читателя: страница смотрит на язык браузера и показывает
его магазин, остальные прячет под строчкой «покупали в другом месте». Так
покрыты все витрины Amazon, а не три.

Скрипт идемпотентный: повторный запуск заменяет уже вставленный блок.
Запуск: python3 make_review_block.py
"""
import re
from pathlib import Path

DEPLOY = Path(__file__).parent

# Витрины Amazon. Порядок = порядок в списке «покупали в другом месте».
STORES = [('com', 'United States'), ('co.uk', 'United Kingdom'), ('de', 'Deutschland'),
          ('fr', 'France'), ('es', 'España'), ('it', 'Italia'), ('nl', 'Nederland'),
          ('pl', 'Polska'), ('se', 'Sverige'), ('com.au', 'Australia'), ('ca', 'Canada'),
          ('co.jp', '日本'), ('com.br', 'Brasil'), ('com.mx', 'México'), ('in', 'India')]

T = {
    'en': dict(kicker='Already read it?', h2='Tell the next reader.',
               body="One honest sentence about the part you enjoyed helps this book more than any "
                    "amount of advertising. Found an error? That matters even more — corrections "
                    "reach the next edition.",
               btn='Leave a review on', more='Bought it in another store?'),
    'de': dict(kicker='Schon gelesen?', h2='Sagen Sie es dem nächsten Leser.',
               body="Ein ehrlicher Satz darüber, was Ihnen gefallen hat, hilft diesem Buch mehr als "
                    "jede Werbung. Einen Fehler gefunden? Das zählt noch mehr — Korrekturen kommen "
                    "in die nächste Auflage.",
               btn='Rezension schreiben auf', more='Woanders gekauft?'),
    'es': dict(kicker='¿Ya lo has leído?', h2='Cuéntaselo al siguiente lector.',
               body="Una frase honesta sobre la parte que más te gustó ayuda a este libro más que "
                    "cualquier anuncio. ¿Has encontrado un error? Eso importa aún más: las "
                    "correcciones llegan a la siguiente edición.",
               btn='Escribe una reseña en', more='¿Lo compraste en otra tienda?'),
}

CSS = """<style>
  #review .rv-lead { max-width: 52ch; margin: 0 auto 26px; text-align: center; }
  #review .rv-btns { display: flex; flex-direction: column; align-items: center; gap: 10px; }
  #review .rv-more { background: none; border: 0; padding: 6px 2px; cursor: pointer;
                     font: inherit; font-size: 14px; text-decoration: underline;
                     text-underline-offset: 3px; opacity: .7; }
  #review .rv-all { display: flex; flex-wrap: wrap; justify-content: center;
                    gap: 8px 16px; max-width: 640px; margin: 6px auto 0; }
  #review .rv-all a { font-size: 14px; color: inherit; text-decoration: none;
                      border-bottom: 1px solid currentColor; opacity: .62;
                      padding-bottom: 1px; white-space: nowrap; }
  #review .rv-all a:hover { opacity: 1; }
</style>"""

JS = """<script>
(function () {
  var ASIN = %(asin)s, HOME = %(home)s, LBL = %(lbl)s;
  var STORES = %(stores)s;
  // Витрину определяем по языку браузера: 'de-AT' -> AT -> amazon.de. Если региона
  // нет ('de') — берём язык. Не угадали — читатель раскроет полный список.
  var REG = {US:'com',GB:'co.uk',DE:'de',AT:'de',CH:'de',FR:'fr',BE:'fr',ES:'es',IT:'it',
             NL:'nl',PL:'pl',SE:'se',AU:'com.au',NZ:'com.au',CA:'ca',JP:'co.jp',
             BR:'com.br',MX:'com.mx',IN:'in'};
  var LNG = {de:'de',fr:'fr',es:'es',it:'it',nl:'nl',pl:'pl',sv:'se',ja:'co.jp',pt:'com.br'};
  function pick() {
    try {
      var l = (navigator.languages && navigator.languages[0]) || navigator.language || '';
      var p = l.split('-');
      if (p[1] && REG[p[1].toUpperCase()]) return REG[p[1].toUpperCase()];
      if (LNG[p[0]]) return LNG[p[0]];
    } catch (e) {}
    return HOME;
  }
  // Ведём на КАРТОЧКУ книги к блоку отзывов, а не на форму создания отзыва.
  // Форма /review/create-review отдаёт редирект на /review/create-review/error
  // всем, кто не имеет права писать отзыв (Amazon требует покупок в аккаунте).
  // Проверено 05.09.2026: на /error падает и родная кнопка Amazon, и ссылка на
  // постороннюю книгу — то есть тупик зависит от читателя, а не от адреса.
  // На карточке Amazon сам решает, что показать, и кнопка «Write a customer
  // review» там своя. Тупика не бывает никогда.
  function url(d) { return 'https://www.amazon.' + d + '/dp/' + ASIN + '#customerReviews'; }
  var mine = pick();
  var name = (STORES.filter(function (s) { return s[0] === mine; })[0] || ['com','United States'])[1];
  document.getElementById('rv-main').innerHTML =
    '<a class="btn primary" href="' + url(mine) + '" rel="noopener">' + LBL + ' amazon.' + mine + '</a>';
  document.getElementById('rv-all').innerHTML = STORES.filter(function (s) { return s[0] !== mine; })
    .map(function (s) { return '<a href="' + url(s[0]) + '" rel="noopener">amazon.' + s[0] + ' &middot; ' + s[1] + '</a>'; })
    .join('');
  var b = document.getElementById('rv-more'), box = document.getElementById('rv-all');
  b.addEventListener('click', function () { box.hidden = !box.hidden; });
  // Пришли по QR из книги (?r=1) — засчитываем отдельным событием. GoatCounter
  // пишет путь без якоря, поэтому без метки скан кода не отличить от обычного
  // захода, и мерить эффект приёма было бы нечем.
  try {
    if (location.search.indexOf('r=1') !== -1) {
      var send = function () {
        if (window.goatcounter && window.goatcounter.count)
          window.goatcounter.count({ path: 'qr' + location.pathname.replace(/\/$/, ''), title: 'QR из книги', event: true });
        else setTimeout(send, 1200);
      };
      send();
    }
  } catch (e) {}
})();
</script>"""


def block(lang, asin, home):
    t = T[lang]
    js = JS % dict(asin=repr(asin).replace("'", '"'), home=repr(home).replace("'", '"'),
                   lbl=repr(t['btn']).replace("'", '"'),
                   stores='[' + ','.join('["%s","%s"]' % s for s in STORES) + ']')
    return f'''<section id="review">
  <div class="wrap">
    <div class="sec-head" style="text-align:center">
      <div class="kicker">{t['kicker']}</div>
      <h2>{t['h2']}</h2>
      <div class="rule" style="margin-left:auto;margin-right:auto"></div>
    </div>
    <p class="rv-lead">{t['body']}</p>
    <div class="rv-btns">
      <div id="rv-main"></div>
      <button type="button" class="rv-more" id="rv-more">{t['more']}</button>
      <div class="rv-all" id="rv-all" hidden></div>
    </div>
  </div>
</section>
{CSS}
{js}

'''


def main():
    done, skipped = [], []
    for lang, root in (('en', DEPLOY / 'books'), ('de', DEPLOY / 'de' / 'books'), ('es', DEPLOY / 'es' / 'books')):
        if not root.exists():
            continue
        for d in sorted(root.iterdir()):
            f = d / 'index.html'
            if not f.exists():
                continue
            s = f.read_text()
            m = re.search(r'class="btn primary" href="https://www\.amazon\.([a-z.]+)/dp/(\w+)"', s)
            if not m:
                skipped.append(d.name); continue
            home, asin = m.group(1), m.group(2)
            # идемпотентность: срезаем ранее вставленный блок целиком
            s = re.sub(r'<section id="review">.*?</script>\n\n', '', s, flags=re.S)
            anchor = '<section id="reader">'
            if anchor not in s:
                skipped.append(d.name + ' (нет якоря)'); continue
            s = s.replace(anchor, block(lang, asin, home) + anchor, 1)
            f.write_text(s)
            done.append(f'{lang}/{d.name} → amazon.{home} {asin}')
    print(f'блок вставлен на {len(done)} страниц')
    for x in done:
        print('  ', x)
    if skipped:
        print('пропущено:', skipped)


if __name__ == '__main__':
    main()
