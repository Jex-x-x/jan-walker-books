#!/usr/bin/env python3
"""Собирает сайт: index.html + books/<slug>/index.html + covers/*.jpg + og.jpg.
Всё self-contained (шрифты/обложки base64), covers/ и og.jpg — публичные файлы для og:image.
"""
import base64, importlib.util, io, json, shutil, sys
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
    'christmas': ROOT / 'christmas/christmas-ebook-cover.jpg',
    'wordsearch': ROOT / 'wordsearch/nostalgic-ebook-cover.jpg',
    'halloween_ws': ROOT / 'halloween-ws/halloween-ebook-cover.jpg',
    'christmas_ws': ROOT / 'christmas-ws/christmas-ebook-cover.jpg',
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
    'miata':     ('Mazda MX-5 Miata Trivia', 'Mazda MX-5 Miata Trivia & Fun Facts', CARS_SERIES, 'B0HGM6J8CF', 'B0H659WDTG',
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
    'christmas': ('Christmas Trivia', 'Christmas Trivia: 900 Questions and Checked Answers About the Traditions Everyone Repeats', FAM_SERIES.replace('Family Table Books', 'Seasonal Shelf'), 'B0HFCTMH6V', 'B0HFD2PWK1',
                  'The tree came from Germany but not from Prince Albert; Santa wears red but not because of Coca-Cola; "Jingle Bells" was written for Thanksgiving. Nine hundred fact-checked questions across ten parts — origins, carols, films, Santa, food, the world, traditions, TV, gifts and the oddities that fit nowhere else. The holiday is built from borrowed parts, and the real story beats the dinner-table version every time.'),
}

PUZZLE_SERIES = 'Memory Lane Puzzles'
# slug -> (short, полный тайтл, PB ASIN, pitch, dir с feature-картинками (A+ модули))
# Серия word-search книг. Добавить книгу 2 = ещё одна строка тут (+ обложка в COVERS + карточка в JS PUZZLES).
PUZZLES = {
    'wordsearch': ('Nostalgic Word Search',
                   'Nostalgic Word Search: A True Story on Every Page',
                   'B0HDX65PXG',
                   'Large-print word search for adults and seniors — with a checked fact printed under every puzzle. Ten chapters across five decades, the 1950s through the 1990s. Words run across, down and diagonally, and never backwards.',
                   ROOT / 'aplus-batch' / 'out' / 'nostalgic'),
    'halloween_ws': ('Halloween Word Search',
                     'Halloween Word Search: A True Story on Every Page',
                     'B0HFG58BG6',
                     'Large-print word search for adults and seniors — with a checked fact under every grid. Ten chapters of Halloween, from Samhain and turnip lanterns to the broadcast that frightened New Jersey. Words run across, down and diagonally, and never backwards.',
                     ROOT / 'aplus-batch' / 'out' / 'halloween_ws'),
    'christmas_ws': ('Christmas Word Search',
                     'Christmas Word Search: A True Story on Every Page',
                     'B0HFP85ZY1',
                     'Large-print word search for adults and seniors — with a checked fact under every grid. Ten chapters of Christmas, from the German tree and the bishop who became Santa to why “Jingle Bells” was written for Thanksgiving. Words run across, down and diagonally, and never backwards.',
                     ROOT / 'aplus-batch' / 'out' / 'christmas_ws'),
}

# slug -> промо-ролик (social-версия, с сайтом в CTA); постер генерится из финального кадра
VIDEOS = {s: ROOT / f'video/out/{s}-promo.mp4' for s in
          ['wrx', 'miata', 'supra', 'skyline', 'mustang', 'silverado', 'gwagon',
           'tacoma', 'f150', '4runner', 'tundra', 'explorer',
           'grandpa', 'grandma', 'dad', 'mom', 'daughter', 'son', 'halloween']}

ALSO = {  # 4 соседа для «Also on this shelf»
    **{s: [x for x in ['miata', 'supra', 'skyline', 'wrx', 'mustang'] if x != s][:4]
       for s in ['miata', 'supra', 'skyline', 'wrx', 'mustang', 'silverado', 'gwagon', 'tacoma', 'f150', '4runner', 'tundra', 'explorer']},
    **{s: [x for x in ['grandpa', 'grandma', 'dad', 'mom', 'daughter'] if x != s][:4]
       for s in ['grandpa', 'grandma', 'dad', 'mom', 'daughter', 'son', 'halloween', 'christmas']},
}


# ---------------------------------------------------------------------------
# Локализация. Английский слой — дословно то, что раньше было вшито в шаблон
# (страницы /books/<slug>/ должны собираться байт-в-байт как до рефакторинга).
# Немецкий и испанский — для страниц переводов /de/books/… и /es/books/….
# ---------------------------------------------------------------------------
UI = {}

UI['en'] = {
    'T_NAV_EXAM': 'The Exam',
    'T_NAV_CARS': 'Cars &amp; Trucks',
    'T_NAV_FAMILY': 'Family Table',
    'T_CTA_GET': 'Get the book',
    'T_ALT_COVER': 'book cover',
    'T_STAT_Q': 'Questions',
    'T_STAT_PARTS': 'Themed parts',
    'T_STAT_SRC': 'Sources per fact',
    'T_BUY_PB': 'Paperback on Amazon',
    'T_BUY_K': 'Kindle edition',
    'T_BUY_NOTE': 'Ships worldwide from Amazon · Great as a gift',
    'T_TRY_KICKER': 'Straight from page {{Q_PAGE_HINT}}',
    'T_TRY_H': 'Try one on the house.',
    'T_TRY_MORE': 'There are 89 more where that came from.',
    'T_TRY_GET_A': 'Get ',
    'T_TRY_GET_B': ' on Amazon &rarr;',
    'T_TRY_TAIL': ' or <a href="/#quiz">take the full entrance exam &rarr;</a>',
    'T_RULES_KICKER': 'Why this one is different',
    'T_RULES_H': 'House rules. Every book.',
    'T_RULES_SUB': 'The Jan Walker standard',
    'T_RULE1': '{{QCOUNT}} questions. 10 themed parts. No padding.',
    'T_RULE2': 'Every fact verified against two independent sources.',
    'T_RULE3': 'Answers explained — the story behind the number.',
    'T_RULE4': 'Disputed facts flagged as disputed. Honestly.',
    'T_RULE5': 'Built to be read out loud and argued over.',
    'T_ALSO_KICKER': 'Keep the argument going',
    'T_ALSO_H': 'Also on this shelf.',
    'T_RD_ALT': 'Book Tracker 2026 — a Google Sheets reading tracker shown on a laptop',
    'T_RD_KICKER': 'For readers',
    'T_RD_H': 'Keep a shelf of everything you&rsquo;ve read.',
    'T_RD_P': 'A clean Google&nbsp;Sheets reading tracker &mdash; type the ISBN and the row fills itself: cover, title, author and page count. Ten tabs: Library, TBR, wishlist and a reading challenge that counts as you go.',
    'T_RD_CTA': 'Get the reading tracker on Etsy &rarr;',
    'T_RD_NOTE': 'Digital download &middot; TheGoodKeeper on Etsy',
    'T_FOOT_TAG': 'Trivia &amp; fun facts, verified twice.',
    'T_FOOT_SUB': 'Paperback &amp; Kindle on Amazon.',
    'T_FOOT_EXPLORE': 'Explore',
    'T_FOOT_ALL': 'All books',
    'T_FOOT_EXAM': 'The Entrance Exam',
    'T_FOOT_ABOUT': 'About Jan Walker',
    'T_FOOT_ELSEWHERE': 'Elsewhere',
    'T_FOOT_AMZ': 'Amazon author page',
    'T_FOOT_READERS': 'For readers',
    'T_FOOT_RD_P': 'Keep every book you finish in one clean Google&nbsp;Sheets tracker — type the ISBN and the row fills itself: cover, title, author and page count.',
    'T_FOOT_RD_CTA': 'Reading tracker on Etsy&nbsp;&rarr;',
    'T_FINE': '© 2026 Jan Walker · Book links lead to Amazon; the reading tracker is a separate download on Etsy. Amazon and Kindle are trademarks of Amazon.com, Inc. or its affiliates.',
    'T_OK': 'Correct',
    'T_BAD': 'Wrong',
    'T_BY': ' by Jan Walker',
    # секции, которые собирает сам build.py
    'T_SEC_VIDEO_K': 'Watch',
    'T_SEC_VIDEO_H': 'The 20-second tour.',
    'T_SEC_APLUS_K': 'A closer look',
    'T_SEC_APLUS_H': 'The whole book, before you buy.',
    'T_SEC_INSIDE_K': "What's inside",
    'T_SEC_INSIDE_H': 'Ten parts. Ninety questions.',
    'T_AP1': 'cover and overview',
    'T_AP4': 'part of the series',
    'T_AP5': 'a great gift',
    'T_AP6': 'about the author',
    'T_ALSO_ALT': 'cover',
    'T_Q_FALLBACK': 'From the book',
    'T_PAGE_HINT': 'the book',
    'T_LANG_NAME': 'English',
    'T_LANG_ABBR': 'EN',
    'T_VAR_LANG': 'Language',
}

UI['de'] = {
    'T_NAV_EXAM': 'Quiz',
    'T_NAV_CARS': 'Autos &amp; Trucks',
    'T_NAV_FAMILY': 'Family Table',
    'T_CTA_GET': 'Zum Buch',
    'T_ALT_COVER': 'Buchcover',
    'T_STAT_Q': 'Fragen',
    'T_STAT_PARTS': 'Thementeile',
    'T_STAT_SRC': 'Quellen pro Fakt',
    'T_BUY_PB': 'Taschenbuch bei Amazon',
    'T_BUY_K': 'Kindle-Ausgabe',
    'T_BUY_NOTE': 'Weltweiter Versand über Amazon · Ein gutes Geschenk',
    'T_TRY_KICKER': 'Direkt aus dem Buch',
    'T_TRY_H': 'Eine Frage geht aufs Haus.',
    'T_TRY_MORE': 'Neunundachtzig weitere warten im Buch.',
    'T_TRY_GET_A': '',
    'T_TRY_GET_B': ' bei Amazon holen &rarr;',
    'T_TRY_TAIL': '',
    'T_RULES_KICKER': 'Warum dieses Buch anders ist',
    'T_RULES_H': 'Hausregeln. In jedem Buch.',
    'T_RULES_SUB': 'Der Jan-Walker-Standard',
    'T_RULE1': '{{QCOUNT}} Fragen. 10 Thementeile. Kein Füllmaterial.',
    'T_RULE2': 'Jeder Fakt gegen zwei unabhängige Quellen geprüft.',
    'T_RULE3': 'Antworten erklärt — die Geschichte hinter der Zahl.',
    'T_RULE4': 'Umstrittene Angaben sind als umstritten gekennzeichnet. Ehrlich.',
    'T_RULE5': 'Gemacht zum Vorlesen und Weiterstreiten.',
    'T_ALSO_KICKER': 'Weiterstreiten',
    'T_ALSO_H': 'Auch auf Deutsch.',
    'T_RD_ALT': 'Book Tracker 2026 — ein Lesetagebuch in Google Sheets auf einem Laptop',
    'T_RD_KICKER': 'Für Leser',
    'T_RD_H': 'Ein Regal für alles, was Sie gelesen haben.',
    'T_RD_P': 'Ein aufgeräumtes Lesetagebuch in Google&nbsp;Sheets &mdash; ISBN eintippen, und die Zeile füllt sich von selbst: Cover, Titel, Autor und Seitenzahl. Zehn Reiter: Bibliothek, Leseliste, Wunschliste und eine Lese-Challenge, die mitzählt. Vorlage auf Englisch.',
    'T_RD_CTA': 'Lesetagebuch auf Etsy ansehen &rarr;',
    'T_RD_NOTE': 'Digitaler Download &middot; TheGoodKeeper auf Etsy',
    'T_FOOT_TAG': 'Trivia &amp; Fakten, zweifach geprüft.',
    'T_FOOT_SUB': 'Taschenbuch &amp; Kindle bei Amazon.',
    'T_FOOT_EXPLORE': 'Entdecken',
    'T_FOOT_ALL': 'Alle Bücher (englisch)',
    'T_FOOT_EXAM': 'Das Quiz (englisch)',
    'T_FOOT_ABOUT': 'Über Jan Walker (englisch)',
    'T_FOOT_ELSEWHERE': 'Anderswo',
    'T_FOOT_AMZ': 'Autorenseite bei Amazon',
    'T_FOOT_READERS': 'Für Leser',
    'T_FOOT_RD_P': 'Jedes gelesene Buch in einem aufgeräumten Google&nbsp;Sheets-Tracker — ISBN eintippen, und die Zeile füllt sich von selbst: Cover, Titel, Autor und Seitenzahl.',
    'T_FOOT_RD_CTA': 'Lesetagebuch auf Etsy&nbsp;&rarr;',
    'T_FINE': '© 2026 Jan Walker · Buchlinks führen zu Amazon; das Lesetagebuch ist ein separater Download auf Etsy. Amazon und Kindle sind Marken von Amazon.com, Inc. oder seinen verbundenen Unternehmen.',
    'T_OK': 'Richtig',
    'T_BAD': 'Falsch',
    'T_BY': ' von Jan Walker',
    'T_SEC_VIDEO_K': 'Ansehen',
    'T_SEC_VIDEO_H': 'Der Rundgang in 20 Sekunden.',
    'T_SEC_APLUS_K': 'Genauer hingesehen',
    'T_SEC_APLUS_H': 'Das ganze Buch, bevor Sie es kaufen.',
    'T_SEC_INSIDE_K': 'Im Buch',
    'T_SEC_INSIDE_H': 'Zehn Teile. Neunzig Fragen.',
    'T_AP1': 'Cover und Überblick',
    'T_AP4': 'Teil der Reihe',
    'T_AP5': 'ein Buch zum Verschenken',
    'T_AP6': 'vom Autor',
    'T_ALSO_ALT': 'Cover',
    'T_Q_FALLBACK': 'Aus dem Buch',
    'T_PAGE_HINT': 'dem Buch',
    'T_LANG_NAME': 'Deutsch',
    'T_LANG_ABBR': 'DE',
    'T_VAR_LANG': 'Sprache',
}

UI['es'] = {
    'T_NAV_EXAM': 'Quiz',
    'T_NAV_CARS': 'Coches',
    'T_NAV_FAMILY': 'Family Table',
    'T_CTA_GET': 'Ver el libro',
    'T_ALT_COVER': 'portada del libro',
    'T_STAT_Q': 'Preguntas',
    'T_STAT_PARTS': 'Partes temáticas',
    'T_STAT_SRC': 'Fuentes por dato',
    'T_BUY_PB': 'Tapa blanda en Amazon',
    'T_BUY_K': 'Edición Kindle',
    'T_BUY_NOTE': 'Envío internacional desde Amazon · Ideal para regalar',
    'T_TRY_KICKER': 'Directamente del libro',
    'T_TRY_H': 'Una pregunta, invita la casa.',
    'T_TRY_MORE': 'Quedan otras ochenta y nueve en el libro.',
    'T_TRY_GET_A': 'Consigue ',
    'T_TRY_GET_B': ' en Amazon &rarr;',
    'T_TRY_TAIL': '',
    'T_RULES_KICKER': 'Por qué este libro es distinto',
    'T_RULES_H': 'Normas de la casa. En todos los libros.',
    'T_RULES_SUB': 'El estándar Jan Walker',
    'T_RULE1': '{{QCOUNT}} preguntas. 10 partes temáticas. Sin relleno.',
    'T_RULE2': 'Cada dato contrastado con dos fuentes independientes.',
    'T_RULE3': 'Respuestas explicadas: la historia detrás del dato.',
    'T_RULE4': 'Los datos discutidos se marcan como discutidos. Con honestidad.',
    'T_RULE5': 'Pensado para leerlo en voz alta y discutirlo.',
    'T_ALSO_KICKER': 'Que siga la discusión',
    'T_ALSO_H': 'También en español.',
    'T_RD_ALT': 'Book Tracker 2026 — un registro de lecturas en Google Sheets en un portátil',
    'T_RD_KICKER': 'Para lectores',
    'T_RD_H': 'Guarda una estantería con todo lo que has leído.',
    'T_RD_P': 'Un registro de lecturas limpio en Google&nbsp;Sheets &mdash; escribe el ISBN y la fila se rellena sola: portada, título, autor y número de páginas. Diez pestañas: biblioteca, pendientes, lista de deseos y un reto de lectura que va contando. Plantilla en inglés.',
    'T_RD_CTA': 'Ver el registro de lecturas en Etsy &rarr;',
    'T_RD_NOTE': 'Descarga digital &middot; TheGoodKeeper en Etsy',
    'T_FOOT_TAG': 'Trivia y curiosidades, verificadas dos veces.',
    'T_FOOT_SUB': 'Tapa blanda y Kindle en Amazon.',
    'T_FOOT_EXPLORE': 'Explorar',
    'T_FOOT_ALL': 'Todos los libros (en inglés)',
    'T_FOOT_EXAM': 'El examen de acceso (en inglés)',
    'T_FOOT_ABOUT': 'Sobre Jan Walker (en inglés)',
    'T_FOOT_ELSEWHERE': 'En otros sitios',
    'T_FOOT_AMZ': 'Página de autor en Amazon',
    'T_FOOT_READERS': 'Para lectores',
    'T_FOOT_RD_P': 'Guarda cada libro que terminas en un registro limpio de Google&nbsp;Sheets — escribe el ISBN y la fila se rellena sola: portada, título, autor y número de páginas.',
    'T_FOOT_RD_CTA': 'Registro de lecturas en Etsy&nbsp;&rarr;',
    'T_FINE': '© 2026 Jan Walker · Los enlaces de los libros llevan a Amazon; el registro de lecturas es una descarga aparte en Etsy. Amazon y Kindle son marcas de Amazon.com, Inc. o de sus filiales.',
    'T_OK': 'Correcto',
    'T_BAD': 'Incorrecto',
    'T_BY': ' de Jan Walker',
    'T_SEC_VIDEO_K': 'Ver',
    'T_SEC_VIDEO_H': 'El recorrido en 20 segundos.',
    'T_SEC_APLUS_K': 'Más de cerca',
    'T_SEC_APLUS_H': 'El libro entero, antes de comprarlo.',
    'T_SEC_INSIDE_K': 'Dentro del libro',
    'T_SEC_INSIDE_H': 'Diez partes. Noventa preguntas.',
    'T_AP1': 'portada y resumen',
    'T_AP4': 'parte de la edición',
    'T_AP5': 'un libro para regalar',
    'T_AP6': 'del autor',
    'T_ALSO_ALT': 'portada',
    'T_Q_FALLBACK': 'Del libro',
    'T_PAGE_HINT': 'el libro',
    'T_LANG_NAME': 'Español',
    'T_LANG_ABBR': 'ES',
    'T_VAR_LANG': 'Idioma',
}

# Домен Amazon по языку издания + авторская страница (en — ровно как было в шаблоне)
AMZ_HOST = {'en': 'www.amazon.com', 'de': 'www.amazon.de', 'es': 'www.amazon.es'}
AMZ_AUTHOR = {
    'en': 'https://www.amazon.com/Jan-Walker/e/B0H3W7P7KR',
    'de': 'https://www.amazon.de/-/e/B0H3W7P7KR',
    'es': 'https://www.amazon.es/-/e/B0H3W7P7KR',
}

# Переводы уже вышедших книг. Отдельно от BOOKS: главная и её счётчики считают
# ПРОИЗВЕДЕНИЯ, а не издания — Miata остаётся одной книгой в трёх языках.
# slug перевода = слаг конфига в aplus-batch/configs и каталога A+ модулей.
TCOVERS = {
    'miata_de': ROOT / 'miata-de/miata-de-ebook-cover.jpg',
    'supra_de': ROOT / 'supra-de/supra-de-ebook-cover.jpg',
    'miata_es': ROOT / 'miata-es/miata-es-ebook-cover.jpg',
    'supra_es': ROOT / 'supra-es/supra-es-ebook-cover.jpg',
    'wrx_es': ROOT / 'wrx-es/wrx-es-ebook-cover.jpg',
    'wrx_de': ROOT / 'wrx-de/wrx-de-ebook-cover.jpg',
}

TRANSLATIONS = {
    'miata_de': dict(
        lang='de', base='miata',
        short='Mazda MX-5 Trivia',
        title='Mazda MX-5 Trivia & Fakten',
        series='Trivia & Fakten · Autos & Trucks',
        pb='B0HG58PZ13', kindle='B0HG569TYG',
        pitch='Über eine Million Autos und ein Guinness-Rekord: der meistverkaufte zweisitzige Roadster aller Zeiten. Neunzig geprüfte Fragen durch vier Generationen des Wagens, der den bezahlbaren Sportwagen gerettet hat — Klappscheinwerfer inklusive.'),
    'supra_de': dict(
        lang='de', base='supra',
        short='Toyota Supra Trivia',
        title='Toyota Supra Trivia & Fakten',
        series='Trivia & Fakten · Autos & Trucks',
        pb='B0HG5M7MJZ', kindle='B0GYZ4BCYH',
        pitch='Die 2JZ-Legende, richtig erzählt — vom stillen Debüt in einer Limousine bis zu Straßenautos mit 1.000 PS auf Serieninnereien. Neunzig geprüfte Fragen durch fünf Generationen der Toyota-Ikone.'),
    'miata_es': dict(
        lang='es', base='miata',
        short='Mazda MX-5 Trivia',
        title='Mazda MX-5 Trivia y Curiosidades',
        series='Trivia y Curiosidades · Coches y Pickups',
        pb='B0HG6517XP', kindle='B0HC4TZLT5',
        pitch='Más de un millón de coches y un récord Guinness: el descapotable biplaza más vendido de la historia. Noventa preguntas verificadas que recorren cuatro generaciones del coche que resucitó al deportivo asequible, faros escamoteables incluidos.'),
    'supra_es': dict(
        lang='es', base='supra',
        short='Toyota Supra Trivia',
        title='Toyota Supra Trivia y Curiosidades',
        series='Trivia y Curiosidades · Coches y Pickups',
        pb='B0HG7P8W7Y', kindle='B0HG7PKVGY',
        pitch='La leyenda del 2JZ contada como toca: del debut discreto bajo la carrocería de una berlina a los coches de calle con mil caballos sobre entrañas de serie. Noventa preguntas verificadas que recorren cinco generaciones del icono de Toyota.'),
    'wrx_es': dict(
        lang='es', base='wrx',
        short='Subaru WRX Trivia',
        title='Subaru WRX Trivia y Curiosidades',
        series='Trivia y Curiosidades · Coches y Pickups',
        pb='B0HG85J4N5', kindle='B0HG7ZXTFQ',
        pitch='Subaru construyó un coche de rally y le vendió al público exactamente lo que el reglamento exigía homologar. McRae, los años del 555, los 424 ejemplares del 22B: noventa preguntas verificadas a lo largo de tres décadas de leyenda bóxer.'),
    'wrx_de': dict(
        lang='de', base='wrx',
        short='Subaru WRX Trivia',
        title='Subaru WRX Trivia & Fakten',
        series='Trivia & Fakten · Autos & Trucks',
        pb='B0HGB7R8PR', kindle='B0HG9HC55T',
        pitch='Subaru baute ein Rallyeauto und verkaufte dem Publikum genau das, was das Reglement zur Homologation verlangte. McRae, die 555-Jahre, alle 424 Exemplare des 22B — neunzig geprüfte Fragen durch drei Jahrzehnte Boxer-Legende.'),
}

# base slug -> {lang: url-path}. Нужен для hreflang и переключателя языков.
LANG_PATHS = {}
for _s in BOOKS:
    LANG_PATHS.setdefault(_s, {})['en'] = f'books/{_s}'
for _s, _t in TRANSLATIONS.items():
    LANG_PATHS.setdefault(_t['base'], {})[_t['lang']] = f"{_t['lang']}/books/{_s}"

# соседи по языку для «Also on this shelf» на страницах переводов
TALSO = {s: [x for x in TRANSLATIONS if x != s and TRANSLATIONS[x]['lang'] == t['lang']][:4]
         for s, t in TRANSLATIONS.items()}


def editions():
    """Все страницы книг: сначала английские (BOOKS), затем переводы."""
    for slug, (short, title, series, pb, kindle, pitch) in BOOKS.items():
        yield dict(slug=slug, cfg=slug, base=slug, lang='en', short=short, title=title,
                   series=series, pb=pb, kindle=kindle, pitch=pitch,
                   cover=COVERS[slug], path=f'books/{slug}', also=ALSO[slug])
    for slug, t in TRANSLATIONS.items():
        yield dict(slug=slug, cfg=slug, base=t['base'], lang=t['lang'], short=t['short'],
                   title=t['title'], series=t['series'], pb=t.get('pb'), kindle=t['kindle'],
                   pitch=t['pitch'],
                   cover=TCOVERS[slug], path=f"{t['lang']}/books/{slug}", also=TALSO[slug])


def short_of(slug):
    return BOOKS[slug][0] if slug in BOOKS else TRANSLATIONS[slug]['short']


def cover_of(slug):
    return COVERS[slug] if slug in COVERS else TCOVERS[slug]


def path_of(slug):
    return f'books/{slug}' if slug in BOOKS else f"{TRANSLATIONS[slug]['lang']}/books/{slug}"


def hreflang_block(base, lang):
    """Взаимные rel=alternate для всех языковых версий книги (+ x-default = английская)."""
    paths = LANG_PATHS.get(base) or {}
    if len(paths) < 2:
        return ''
    order = [l for l in ('en', 'de', 'es') if l in paths]
    out = ['']
    for l in order:
        out.append(f'<link rel="alternate" hreflang="{l}" href="{SITE_URL}/{paths[l]}/">')
    out.append(f'<link rel="alternate" hreflang="x-default" href="{SITE_URL}/{paths["en"]}/">')
    return '\n'.join(out)


def variations_block(base, lang):
    """Выбор языка как вариация товара — рядом с кнопками покупки, а не в навигации."""
    paths = LANG_PATHS.get(base) or {}
    if len(paths) < 2:
        return ''
    opts = []
    for l in (x for x in ('en', 'de', 'es') if x in paths):
        name = UI[l]['T_LANG_NAME']
        if l == lang:
            opts.append(f'          <span class="vopt on" aria-current="true">{name}</span>')
        else:
            opts.append(f'          <a class="vopt" href="/{paths[l]}/" hreflang="{l}" lang="{l}">{name}</a>')
    return ('      <div class="vary">\n'
            f'        <div class="vlbl">{UI[lang]["T_VAR_LANG"]}</div>\n'
            '        <div class="vopts">\n' + '\n'.join(opts) + '\n'
            '        </div>\n      </div>\n')


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


def aplus_dir(slug):
    """Каталог с A+ модулями книги. halloween лежит отдельно, остальное — в batch/out."""
    return ROOT / 'halloween' / 'aplus' if slug == 'halloween' else ROOT / 'aplus-batch' / 'out' / slug


# (номер, ключ файла, подпись для alt, ширина web-JPEG). 1 — баннер-герой 970×600, 4-6 — квадраты 900×900.
# Модули 2 (10 частей) и 3 (пример-вопрос) НЕ выводим: их дублируют родные секции сайта
# #inside (PARTS_SECTION) и #try (интерактивный вопрос). См. «дубли не нужны» 15.08.
APLUS_SPECS = [
    (1, 'hero', 'T_AP1', 970),
    (4, 'series', 'T_AP4', 700),
    (5, 'gift', 'T_AP5', 700),
    (6, 'author', 'T_AP6', 700),
]


def aplus_images(slug):
    """Ресайзит module1..6 в _deploy/aplus/<slug>/N.jpg. Возвращает [(url, подпись, kind)]."""
    d = aplus_dir(slug)
    out = DEPLOY / 'aplus' / slug
    items = []
    for n, key, tkey, w in APLUS_SPECS:
        src = d / f'module{n}_{key}.png'
        if not src.exists():
            continue
        out.mkdir(exist_ok=True, parents=True)
        im = Image.open(src).convert('RGB')
        if im.width > w:
            im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
        im.save(out / f'{n}.jpg', 'JPEG', quality=82, optimize=True, progressive=True)
        items.append((f'/aplus/{slug}/{n}.jpg', tkey, 'banner' if n <= 3 else 'square'))
    return items


def aplus_section(slug, short, T):
    """HTML-секция «A closer look» с A+ модулями (3 баннера + ряд из 3 квадратов)."""
    items = aplus_images(slug)
    if not items:
        return ''
    banners = '\n      '.join(
        f'<img src="{u}" alt="{esc(short)} — {T[d]}" loading="lazy">' for u, d, k in items if k == 'banner')
    squares = '\n      '.join(
        f'<img src="{u}" alt="{esc(short)} — {T[d]}" loading="lazy">' for u, d, k in items if k == 'square')
    return f'''<section id="aplus">
  <div class="wrap">
    <div class="sec-head" style="text-align:center">
      <div class="kicker">{T['T_SEC_APLUS_K']}</div>
      <h2>{T['T_SEC_APLUS_H']}</h2>
      <div class="rule" style="margin-left:auto;margin-right:auto"></div>
    </div>
    <div class="aplus-banners">
      {banners}
    </div>
    <div class="aplus-squares">
      {squares}
    </div>
  </div>
</section>'''


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


SITE_URL = 'https://janwalkerbooks.com'

# Аналитика без куки-баннера (PLAN.md, этап 1). Все варианты не ставят куки и
# не требуют баннера согласия. Пока PROVIDER пуст — в HTML не попадает ничего.
#   goatcounter  → CODE = код сайта, выданный на goatcounter.com (<code>.goatcounter.com)
#   cloudflare   → CODE = beacon-токен из Cloudflare Web Analytics
ANALYTICS_PROVIDER = 'goatcounter'
ANALYTICS_CODE = 'janwalkerbooks'


def analytics_tag():
    """<script> счётчика или пустая строка, если счётчик не подключён."""
    if not ANALYTICS_PROVIDER or not ANALYTICS_CODE:
        return ''
    if ANALYTICS_PROVIDER == 'goatcounter':
        return ('<script data-goatcounter="https://%s.goatcounter.com/count"'
                ' async src="https://gc.zgo.at/count.js"></script>\n' % ANALYTICS_CODE)
    if ANALYTICS_PROVIDER == 'cloudflare':
        return ('<script defer src="https://static.cloudflareinsights.com/beacon.min.js"'
                ' data-cf-beacon=\'{"token": "%s"}\'></script>\n' % ANALYTICS_CODE)
    raise SystemExit('неизвестный ANALYTICS_PROVIDER: ' + ANALYTICS_PROVIDER)


def book_ld(slug, title, desc, lang='en', path=None):
    """JSON-LD schema.org/Book для страницы книги (json.dumps сам экранирует)."""
    return json.dumps({
        '@context': 'https://schema.org',
        '@type': 'Book',
        'name': title,
        'author': {'@type': 'Person', 'name': 'Jan Walker',
                   'url': SITE_URL + '/'},
        'publisher': {'@type': 'Organization', 'name': 'Jan Walker Books'},
        'bookFormat': 'https://schema.org/Paperback',
        'inLanguage': lang,
        'url': f'{SITE_URL}/{path or ("books/" + slug)}/',
        'image': f'{SITE_URL}/covers/{slug}.jpg',
        'description': desc,
    }, ensure_ascii=False)


HOME_LD = json.dumps({
    '@context': 'https://schema.org',
    '@graph': [
        {'@type': 'WebSite', 'name': 'Jan Walker Books', 'url': SITE_URL + '/'},
        {'@type': 'Person', 'name': 'Jan Walker', 'url': SITE_URL + '/',
         'jobTitle': 'Author',
         'sameAs': ['https://x.com/JanWalkerBooks',
                    'https://www.pinterest.com/janwalkerbooks/']},
    ],
}, ensure_ascii=False)


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


def build_brand():
    """Логотип «читающая лиса» + фавиконы из site/brand-fox.png (прозрачный вырез)."""
    src = Image.open(SITE / 'brand-fox.png').convert('RGBA')
    bb = src.split()[-1].getbbox()
    fox = src.crop(bb) if bb else src
    (DEPLOY / 'brand').mkdir(exist_ok=True, parents=True)
    logo = fox.copy(); logo.thumbnail((460, 460), Image.LANCZOS)
    logo.save(DEPLOY / 'brand' / 'logo.png')
    CREAM = (246, 241, 229, 255)

    def tile(img, size, pad=0.08):
        c = Image.new('RGBA', (size, size), CREAM)
        inner = size - 2 * int(size * pad)
        s = img.copy(); s.thumbnail((inner, inner), Image.LANCZOS)
        c.alpha_composite(s, ((size - s.width) // 2, (size - s.height) // 2))
        return c

    # фавикон = полный знак (лиса + книга), а не только морда: так это узнаётся
    # как наш логотип. На 32px+ читается чисто; на 16px мельчит, но силуэт держит.
    tile(fox, 16, pad=0.05).save(DEPLOY / 'favicon-16.png')
    tile(fox, 32, pad=0.06).save(DEPLOY / 'favicon-32.png')
    tile(fox, 180, pad=0.12).convert('RGB').save(DEPLOY / 'apple-touch-icon.png')
    tile(fox, 48, pad=0.08).save(DEPLOY / 'favicon.ico', sizes=[(16, 16), (32, 32), (48, 48)])
    print('brand: logo.png + favicons written')


def main():
    (DEPLOY / 'covers').mkdir(exist_ok=True, parents=True)
    fonts64 = {k: base64.b64encode(p.read_bytes()).decode() for k, p in FONTS.items()}

    # публичные обложки для og:image детальных страниц
    for slug, path in {**COVERS, **TCOVERS}.items():
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
    html = html.replace('{{JSONLD}}', HOME_LD)
    # счётчики героя считаем из данных, чтобы не протухали при добавлении книги.
    # вопросы — только у trivia (BOOKS): christmas = 900, остальные 90 (как {{QCOUNT}} на стр. книги);
    # word search (PUZZLES) — это головоломки, в «verified questions» не входят.
    html = html.replace('{{BOOK_COUNT}}', str(len(BOOKS) + len(PUZZLES)))
    html = html.replace('{{QUESTION_COUNT}}', f"{sum(900 if s == 'christmas' else 90 for s in BOOKS):,}")
    html = html.replace('{{ANALYTICS}}\n', analytics_tag())
    (SITE / 'index.html').write_text(html)
    shutil.copy(SITE / 'index.html', DEPLOY / 'index.html')
    print('index.html', f"{(SITE / 'index.html').stat().st_size / 1e6:.2f} MB")

    # -------- детальные страницы --------
    tpl = (SITE / 'book.template.html').read_text()
    for tok, val in fonts64.items():
        tpl = tpl.replace('{{%s}}' % tok, val)

    n_pages = 0
    for ed in editions():
        slug, lang, base = ed['slug'], ed['lang'], ed['base']
        T = UI[lang]
        short, title, series, pitch = ed['short'], ed['title'], ed['series'], ed['pitch']
        cfg = load_cfg(ed['cfg'])
        page = tpl
        # строки интерфейса — ПЕРЕД {{QCOUNT}} и {{Q_PAGE_HINT}}: они сидят внутри
        # значений T_RULE1 и T_TRY_KICKER и должны успеть раскрыться
        for k, v in T.items():
            page = page.replace('{{%s}}' % k, v)
        page = page.replace('{{SLUG}}', slug)
        page = page.replace('{{ANALYTICS}}\n', analytics_tag())
        page = page.replace('{{LANG}}', lang)
        page = page.replace('{{PATH}}', ed['path'])
        page = page.replace('{{HREFLANG}}', hreflang_block(base, lang))
        page = page.replace('{{VARIATIONS}}\n', variations_block(base, lang))
        page = page.replace('{{AMZ_AUTHOR}}', AMZ_AUTHOR[lang])
        page = page.replace('{{SHORT}}', esc(short))
        page = page.replace('{{TITLE}}', esc(title))
        page = page.replace('{{SERIES}}', esc(series))
        page = page.replace('{{PITCH}}', esc(pitch))
        page = page.replace('{{META_DESC}}', esc(pitch[:250]))
        page = page.replace('{{JSONLD}}', book_ld(slug, title, pitch, lang, ed['path']))
        # У издания может не быть бумаги (немецкий WRX: paperback заблокирован Amazon'ом).
        # Тогда все ссылки «купить» ведут на Kindle, а кнопка «бумага» из блока покупки уходит.
        k_url = f"https://{AMZ_HOST[lang]}/dp/{ed['kindle']}"
        pb_url = f"https://{AMZ_HOST[lang]}/dp/{ed['pb']}" if ed.get('pb') else k_url
        if not ed.get('pb'):
            # строки T_* уже раскрыты выше, поэтому ищем кнопку с готовым текстом
            btn_pb = ('<a class="btn primary" href="{{AMZ_PB}}" target="_blank" '
                      'rel="noopener">%s</a>\n        ' % T['T_BUY_PB'])
            assert page.count(btn_pb) == 1, 'кнопка «бумага» не найдена в шаблоне'
            page = page.replace(btn_pb, '')
            page = page.replace('class="btn ghost" href="{{AMZ_K}}"', 'class="btn primary" href="{{AMZ_K}}"')
        page = page.replace('{{AMZ_PB}}', pb_url)
        page = page.replace('{{AMZ_K}}', k_url)
        page = page.replace('{{QCOUNT}}', {'christmas': '900'}.get(slug, '90'))
        page = page.replace('{{COVER_MAIN}}', cover_datauri(ed['cover'], width=640, quality=82))

        # Trailer video: ВЕРСИОННЫЕ имена файлов (кэш HTML на GitHub Pages живёт 10 мин и
        # отдаёт старые ссылки — с версией в имени старый HTML тянет старый файл, новый — новый).
        # У переводов ролика нет: озвучка и текст в кадре английские.
        if lang == 'en' and slug in VIDEOS and VIDEOS[slug].exists():
            vdir = DEPLOY / 'video'
            vdir.mkdir(exist_ok=True, parents=True)
            ver = VIDEOS[slug].stat().st_size
            vname = f'{slug}-promo-{ver}.mp4'
            pname = f'{slug}-promo-{ver}-poster.jpg'
            shutil.copy(VIDEOS[slug], vdir / vname)
            shutil.copy(VIDEOS[slug], vdir / f'{slug}-promo.mp4')  # переходный незверсионный URL
            import subprocess
            subprocess.run(['ffmpeg', '-y', '-ss', '17.6', '-i', str(VIDEOS[slug]), '-frames:v', '1',
                            '-q:v', '4', str(vdir / pname), '-loglevel', 'error'])
            video_section = f'''<section id="trailer">
  <div class="wrap">
    <div class="sec-head">
      <div class="kicker">{T['T_SEC_VIDEO_K']}</div>
      <h2>{T['T_SEC_VIDEO_H']}</h2>
      <div class="rule"></div>
    </div>
    <video controls playsinline preload="metadata" poster="/video/{pname}">
      <source src="/video/{vname}" type="video/mp4">
    </video>
  </div>
</section>'''
        else:
            video_section = ''
        page = page.replace('{{VIDEO_SECTION}}', video_section)

        # A+ gallery (модули из Amazon-листинга — у переводов свои, локализованные)
        page = page.replace('{{APLUS_SECTION}}', aplus_section(ed['cfg'], short, T))

        # Parts
        if cfg and cfg.get('chapters'):
            parts = '\n'.join(
                f'<div class="part"><span class="num">{esc(n)}</span><span><span class="pt">{esc(t)}.</span> <span class="ps">{esc(sub)}</span></span></div>'
                for n, t, sub in cfg['chapters'])
            parts_section = f'''<section id="inside">
  <div class="wrap">
    <div class="sec-head">
      <div class="kicker">{T['T_SEC_INSIDE_K']}</div>
      <h2>{T['T_SEC_INSIDE_H']}</h2>
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
            page = page.replace('{{Q_LOCATION}}', esc(q.get('location', T['T_Q_FALLBACK'])))
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
        page = page.replace('{{Q_PAGE_HINT}}', T['T_PAGE_HINT'])

        # Also on this shelf — соседи того же языка
        if ed['also']:
            also = '\n'.join(
                f'<a href="/{path_of(x)}/"><img src="{cover_datauri(cover_of(x), width=300, quality=78)}" alt="{esc(short_of(x))} {T["T_ALSO_ALT"]}"><div class="t">{esc(short_of(x))}</div></a>'
                for x in ed['also'])
            page = page.replace('{{ALSO_CARDS}}', also)
        else:
            # соседей на этом языке ещё нет (miata_es) — секцию убираем целиком
            start = page.index('<section id="series-more">')
            end = page.index('</section>', start) + len('</section>')
            page = page[:start] + page[end:]

        out = DEPLOY / ed['path']
        out.mkdir(exist_ok=True, parents=True)
        (out / 'index.html').write_text(page)
        n_pages += 1

    print('book pages:', n_pages, f'(en {len(BOOKS)} + переводы {len(TRANSLATIONS)})')

    # -------- Memory Lane Puzzles (word-search series) --------
    ws_tpl = (SITE / 'wordsearch.template.html').read_text()
    for tok, val in fonts64.items():
        ws_tpl = ws_tpl.replace('{{%s}}' % tok, val)
    PUZZLE_SPECS = {
        'wordsearch': [('80', 'Puzzles'), ('10', 'Themed chapters'), ('5', 'Decades · 1950s–90s')],
        'halloween_ws': [('130', 'Puzzles'), ('10', 'Themed chapters'), ('2', 'Sources per fact')],
        'christmas_ws': [('130', 'Puzzles'), ('10', 'Themed chapters'), ('2', 'Sources per fact')],
    }
    for slug, (short, title, pb, pitch, adir) in PUZZLES.items():
        page = ws_tpl
        specs = PUZZLE_SPECS.get(slug, [('', ''), ('', ''), ('', '')])
        page = page.replace('{{SPECS}}', ''.join(
            f'<div class="spec"><div class="num">{esc(n)}</div><div class="lbl">{esc(l)}</div></div>'
            for n, l in specs))
        page = page.replace('{{SLUG}}', slug)
        page = page.replace('{{ANALYTICS}}\n', analytics_tag())
        page = page.replace('{{SHORT}}', esc(short))
        page = page.replace('{{TITLE}}', esc(title))
        page = page.replace('{{SERIES}}', esc(PUZZLE_SERIES))
        page = page.replace('{{PITCH}}', esc(pitch))
        page = page.replace('{{META_DESC}}', esc(pitch[:250]))
        page = page.replace('{{JSONLD}}', book_ld(slug, title, pitch))
        page = page.replace('{{AMZ_PB}}', f'https://www.amazon.com/dp/{pb}')
        page = page.replace('{{COVER_MAIN}}', cover_datauri(COVERS[slug], width=640, quality=82))
        # feature banners: word-search sample jpgs, else fall back to the A+ header
        # modules (hero / inside / sample) so books built through the A+ pipeline
        # (halloween_ws) still show a rich "inside" showcase.
        feats = sorted(adir.glob('0*.jpg'))
        if not feats:
            feats = [adir / f for f in ('module1_hero.png', 'module2_inside.png', 'module3_sample.png')
                     if (adir / f).exists()]
        feat_html = '\n'.join(
            f'<img src="{cover_datauri(p, width=900, quality=82)}" alt="{esc(short)} sample" loading="lazy">'
            for p in feats)
        page = page.replace('{{FEATURE_IMAGES}}', feat_html)
        out = DEPLOY / 'books' / slug
        out.mkdir(exist_ok=True, parents=True)
        (out / 'index.html').write_text(page)
    print('puzzle pages:', len(PUZZLES))

    # -------- robots.txt + sitemap.xml (индексация) --------
    base = 'https://janwalkerbooks.com'
    slugs = list(BOOKS.keys()) + list(PUZZLES.keys())
    urls = ([base + '/'] + [f'{base}/books/{s}/' for s in slugs]
            + [f"{base}/{t['lang']}/books/{s}/" for s, t in TRANSLATIONS.items()])
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        prio = '1.0' if u.endswith('.com/') else '0.8'
        sm.append(f'  <url><loc>{u}</loc><changefreq>weekly</changefreq><priority>{prio}</priority></url>')
    sm.append('</urlset>')
    (DEPLOY / 'sitemap.xml').write_text('\n'.join(sm) + '\n')
    (DEPLOY / 'robots.txt').write_text(
        f'User-agent: *\nAllow: /\n\nSitemap: {base}/sitemap.xml\n')
    print('sitemap urls:', len(urls))

    # -------- подтверждение владения (Google Search Console + Bing) --------
    # HTML-файл верификации GSC (свой путь — не ловит 10-мин HTML-кэш главной)
    (DEPLOY / 'google254517b6338c9420.html').write_text(
        'google-site-verification: google254517b6338c9420.html\n')
    # IndexNow ключ (Bing/Yandex/Seznam мгновенная подача). Ключ публичный.
    INDEXNOW_KEY = '5e3f345729040673408fd470780bc8b4'
    (DEPLOY / f'{INDEXNOW_KEY}.txt').write_text(INDEXNOW_KEY + '\n')
    (DEPLOY / 'urls.txt').write_text('\n'.join(urls) + '\n')  # для ручной/скриптовой подачи
    # Bing Webmaster Tools — верификация XML-файлом (свой путь, кэш главной не мешает)
    (DEPLOY / 'BingSiteAuth.xml').write_text(
        '<?xml version="1.0"?>\n<users>\n\t<user>88F0E9A10B7D3AEBF4A91E52CF453923</user>\n</users>\n')

    build_og()
    build_brand()

    leftover = [str(f.parent.relative_to(DEPLOY))
                for f in (DEPLOY / 'books' / 'miata' / 'index.html',
                          DEPLOY / 'de' / 'books' / 'miata_de' / 'index.html',
                          DEPLOY / 'es' / 'books' / 'miata_es' / 'index.html')
                if '{{' in f.read_text()]
    print('leftover tokens in book pages:', leftover)


if __name__ == '__main__':
    main()
