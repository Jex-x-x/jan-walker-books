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
 'nsx': dict(
   title_raw='NSX Trivia & Fun Facts', short='NSX Trivia', book='nsx', aplus='nsx/v2',
   pitch=("Most supercars are built to be admired. This one was built to be used. In 1984 Honda "
          "commissioned a mid-engine concept car from Pininfarina, and the project that grew out of it "
          "set itself an unusual target: a car that could be measured against Ferrari, but that an "
          "ordinary person could drive every day. Ninety verified questions &mdash; the all-aluminium "
          "body, what Senna really did at the N&uuml;rburgring, the first Type R, and the racing car "
          "that won its class at Le Mans."),
   parts=[('From HP-X to NS-X.', 'A concept with no doors, and a name'),
          ('Aluminium and Hands.', 'The body and the factory built for it'),
          ('Senna and the Ring.', 'How the chassis was made stiff'),
          ('The V6.', 'Three litres, four valves, titanium'),
          ('The Everyday Supercar.', 'Visibility, hardware, daily use'),
          ('The First Type R.', '1992 and 2002: when Honda took things out'),
          ('Fifteen Years of Updates.', 'Targa, 3.2 litres, fixed headlights'),
          ('Le Mans and Beyond.', 'The NSX as a racing car'),
          ('The Second NSX.', 'Hybrid, built in Ohio'),
          ('Honda&rsquo;s Racing Roots.', 'The company behind the car')],
   quiz=dict(top='Q21  &middot;  PART 3  &middot;  SENNA AND THE RING',
             q='What word did Senna use about the NSX prototype&rsquo;s body after driving it?',
             opts=['Fragile', 'Perfect', 'Heavy', 'Loud'], correct=0,
             reveal=("Fragile. According to Honda&rsquo;s own account, Senna said he was not sure he could "
                     "give advice about a mass-production car, but that he felt it was a little fragile. "
                     "The team took it seriously and set a tougher stiffness target for the body.")),
   also=[('civic', 'Civic Type R Trivia', 'civic-type-r/civic-type-r-ebook-cover.jpg'),
         ('rx7', 'RX-7 Trivia', 'rx7/rx7-ebook-cover.jpg'),
         ('ae86', 'AE86 Trivia', 'ae86/ae86-ebook-cover.jpg'),
         ('miata', 'Mazda MX-5 Miata Trivia', 'miata/miata-ebook-cover.jpg')],
   when='Coming soon',
   soon_line=('Printed and proofread, in the last checks before release \u00b7 paperback and Kindle, worldwide from Amazon')),
 '300zx': dict(
   title_raw='300ZX Trivia & Fun Facts', short='300ZX Trivia', book='z32', aplus='z32/v2',
   pitch=("A sports car was drawn in 1984 that Nissan did not sell until 1989. Toshio Yamashita began the "
          "Z32, a Cray-2 supercomputer helped shape its body, and it carried a 3.0-litre V6 with two "
          "turbochargers. Ninety verified questions &mdash; who drew it, the four-wheel steering, the "
          "Super Bowl commercial Nissan pulled after one showing, and the racing 300ZX that won "
          "Daytona outright."),
   parts=[('Mr. K and the Z.', 'From the 240Z to the V6 300ZX'),
          ('Drawn in 1984.', 'The design, the MID4 and a supercomputer'),
          ('Three Litres, Two Turbos.', 'The VG30 engines and the 280 PS limit'),
          ('Steering with Four Wheels.', 'Super HICAS, suspension and brakes'),
          ('Many Shapes, Many Markets.', 'Bodies, trims and where they were built'),
          ('Launch, Awards and Sales.', '1990 to 1996, and the price that rose'),
          ('The Ad Nissan Pulled.', 'A Super Bowl spot, toys and a Lamborghini'),
          ('From Lime Rock to Daytona.', 'Racing 300ZXs, 1985 to 1995'),
          ('Tuners and Special Editions.', 'SR-71, SMZ and the Bonneville record'),
          ('The Last Z32.', 'What came after, and what did not')],
   quiz=dict(top='Q56  &middot;  PART 7  &middot;  THE AD NISSAN PULLED',
             q='How many times did Nissan&rsquo;s Ridley Scott Super Bowl commercial run?',
             opts=['Once', 'Twice', 'Ten times', 'Throughout the whole 1990 season'], correct=0,
             reveal=("Once. Nissan aired the commercial during the Super Bowl and did not repeat it; "
                     "safety groups objected, and the company defended the spot as clearly fanciful.")),
   also=[('civic', 'Civic Type R Trivia', 'civic-type-r/civic-type-r-ebook-cover.jpg'),
         ('nsx', 'NSX Trivia', 'nsx/nsx-ebook-cover.jpg'),
         ('rx7', 'RX-7 Trivia', 'rx7/rx7-ebook-cover.jpg'),
         ('ae86', 'AE86 Trivia', 'ae86/ae86-ebook-cover.jpg')],
   when='Coming soon',
   soon_line=('Printed and proofread, in the last checks before release \u00b7 paperback and Kindle, worldwide from Amazon')),
 'etype': dict(
   allow=['Jaguar'],
   title_raw='E-Type Trivia & Fun Facts', short='E-Type Trivia', book='etype', aplus='etype',
   pitch=("The E-Type began as a racing car with the racing taken out. Jaguar won Le Mans five times with the "
          "C-Type and the D-Type, and in March 1961 it unveiled the road car in Geneva, claiming 150 mph at about "
          "half the price of its exotic rivals. About 72,500 were built before production ended in 1974. Ninety "
          "verified questions &mdash; the man who drew it with slide rules, the XK engine, the Series 1, 2 and 3, the "
          "V12, the Lightweight and the electric E-type Zero."),
   parts=[('From Le Mans to the Road.', 'The C-Type, the D-Type and the XKSS'),
          ('The Man Who Drew It.', 'Malcolm Sayer and William Lyons'),
          ('Geneva, March 1961.', 'The launch and the claims'),
          ('The XK Engine and the Gearbox.', '3.8 litres, then 4.2'),
          ('Series 1 Cars.', 'Glass headlights, 1961 to 1967'),
          ('Series 1&frac12; and Series 2.', 'American safety rules, 1967 to 1971'),
          ('Series 3 and the V12.', 'The last E-Types, 1971 to 1974'),
          ('Racing Specials and Rarities.', 'The Lightweight and the XJ13'),
          ('Prices and Numbers.', 'What it cost, what it fetches, how many'),
          ('The Legend and the Ultimate Fan Challenge.', '1996 to today')],
   quiz=dict(top='Q47  &middot;  PART 6  &middot;  GLASS HEADLIGHTS',
             q='What was removed from the Series 2 headlights?',
             opts=['The bulbs', 'The chrome surround', 'The glass covers', 'The indicators'], correct=2,
             reveal=("The glass covers. They were removed from cars everywhere, largely because of American "
                     "safety rules, and the Series 1½ of 1967 and 1968 is what owners call the cars in between.")),
   also=[('vwbus', 'Microbus Trivia', 'vwbus/vwbus-ebook-cover.jpg'),
         ('e30', 'E30 Trivia', 'e30/e30-ebook-cover.jpg'),
         ('z3', 'Z3 Trivia', 'z3/z3-ebook-cover.jpg'),
         ('miata', 'Mazda MX-5 Miata Trivia', 'miata/miata-ebook-cover.jpg')],
   when='Coming soon',
   soon_line=('Printed and proofread, in the last checks before release \u00b7 paperback and Kindle, worldwide from Amazon')),
 'vwbus': dict(
   allow=['Volkswagen'],
   title_raw='Microbus Trivia & Fun Facts', short='Microbus Trivia', book='vwbus', aplus='vwbus',
   pitch=("In April 1947 a Dutch importer drew a van with the driver at the very front and a payload of "
          "690 kilograms, and the sketch became the most recognisable vehicle in the world. Volkswagen says "
          "13 million Transporters have been sold since 1950, in five countries. Ninety verified questions "
          "&mdash; the Splittie and the 23-window Samba, the camper conversions, a Vanagon with a Porsche "
          "engine, the Chicken Tax, and the electric successor."),
   parts=[('The Sketch.', 'An importer, a doodle, 1947 to 1950'),
          ('The Splittie.', 'The first generation, 1950 to 1967'),
          ('The Samba.', 'Twenty-three windows and a sunroof'),
          ('The Bay Window.', 'The second generation, 1967 to 1979'),
          ('The Camper.', 'Westfalia and the pop-up roof'),
          ('The Vanagon.', 'Square, water-cooled, four-wheel drive'),
          ('The Front-Engined Bus.', 'The T4, 1990 to 2003'),
          ('Around the World.', 'Brazil, Mexico and the last Kombi'),
          ('The Counterculture and the Chicken Tax.', 'A tariff and a symbol'),
          ('The Ultimate Fan Challenge.', 'From the T5 to the electric ID. Buzz')],
   quiz=dict(top='Q73  &middot;  PART 9  &middot;  THE CHICKEN TAX',
             q='What rate did the Chicken Tax put on imported light trucks?',
             opts=['4%', '10%', '25%', '50%'], correct=2,
             reveal=("25 per cent &mdash; introduced in January 1964 as retaliation for European tariffs on "
                     "American chicken. The van counted as a light truck, so it was hit too.")),
   also=[('e30', 'E30 Trivia', 'e30/e30-ebook-cover.jpg'),
         ('z3', 'Z3 Trivia', 'z3/z3-ebook-cover.jpg'),
         ('miata', 'Mazda MX-5 Miata Trivia', 'miata/miata-ebook-cover.jpg'),
         ('supra', 'Toyota Supra Trivia', 'supra/supra-ebook-cover.jpg')],
   when='Coming soon',
   soon_line=('Printed and proofread, in the last checks before release \u00b7 paperback and Kindle, worldwide from Amazon')),
 'e30': dict(
   title_raw='E30 Trivia & Fun Facts', short='E30 Trivia', book='e30', aplus='e30/v2',
   pitch=("The most famous car in this book has four cylinders, not six. BMW built about 2.3 million E30s "
          "between 1982 and 1994, and from one of them, made under a racing rule, it produced a road car "
          "that won the championships it was designed for. Ninety verified questions &mdash; the M3 and "
          "its homologation rule, Camshaft Paul and the S14 engine, the touring-car titles, and the "
          "tuner that became a manufacturer."),
   parts=[('The Compact BMW.', 'From the 1975 3 Series to the E30'),
          ('Bodies and Engines.', 'The E30 range, 1982 to 1994'),
          ('Made for Other Markets.', 'America, South Africa and the tax specials'),
          ('A Racing Car with a Number Plate.', 'The M3, 1985 to 1991'),
          ('Four Cylinders, Six-Cylinder Genes.', 'The S14 engine'),
          ('Touring Cars.', 'DTM, Europe and the world, 1987 to 1992'),
          ('Endurance and Bragging Rights.', 'N&uuml;rburgring, Spa and Macau'),
          ('Alpina.', 'The tuner that became a manufacturer'),
          ('The M Division.', 'The people who built the engines'),
          ('What Came After.', 'The E36 and the E30&rsquo;s design DNA')],
   quiz=dict(top='Q39  &middot;  PART 5  &middot;  FOUR CYLINDERS, SIX-CYLINDER GENES',
             q='What was Paul Rosche&rsquo;s nickname, because of his early specialisation in camshaft calculation?',
             opts=['Piston Paul', 'Turbo Paul', 'Crank Paul', 'Camshaft Paul'], correct=3,
             reveal=("Camshaft Paul &mdash; in German, Nocken-Paul. Rosche ran BMW&rsquo;s racing-engine "
                     "development, led the S14, and retired in 1999 at the age of 65.")),
   also=[('civic', 'Civic Type R Trivia', 'civic-type-r/civic-type-r-ebook-cover.jpg'),
         ('nsx', 'NSX Trivia', 'nsx/nsx-ebook-cover.jpg'),
         ('300zx', '300ZX Trivia', 'z32/z32-ebook-cover.jpg'),
         ('ae86', 'AE86 Trivia', 'ae86/ae86-ebook-cover.jpg')],
   when='Coming soon',
   soon_line=('Printed and proofread, in the last checks before release \u00b7 paperback and Kindle, worldwide from Amazon')),
 'z3': dict(
   title_raw='Z3 Trivia & Fun Facts', short='Z3 Trivia', book='z3', aplus='z3/v2',
   pitch=("BMW paid nothing for the Z3&rsquo;s part in a Bond film, and the placement turned into one of the "
          "most successful of 1995. The little roadster was built in South Carolina, not Germany, and "
          "a hundred replicas of the film car went through a Christmas catalogue. Ninety verified questions "
          "&mdash; the Z1 that came before it, the Spartanburg plant, the engine range from fours to the "
          "M Roadster, and the Coupe nicknamed the clown shoe."),
   parts=[('The Roadster Before It.', 'The Z1 and the Fun Car, 1985 to 1992'),
          ('Drawn in Munich.', 'The Fun Car, the board and the E36 underneath'),
          ('Built in Carolina.', 'Spartanburg, South Carolina, 1992 to 2002'),
          ('The Spy&rsquo;s Car.', 'GoldenEye, 1995'),
          ('A Hundred Cars for the Catalogue.', 'The launch and the 007 Edition'),
          ('Fours and Sixes.', 'The engine range, 1995 to 2002'),
          ('The M Roadster.', 'The Z3 M, 1997 to 2002'),
          ('The Clown Shoe.', 'The Z3 Coup&eacute;, 1997 to 2002'),
          ('Prototypes, Specials and Totals.', 'V12, MotoGP and the final count'),
          ('Owners and the Last Car.', 'The club, the Homecoming and the Z4')],
   quiz=dict(top='Q31  &middot;  PART 4  &middot;  THE SPY&rsquo;S CAR',
             q='How much did BMW pay for the placement of the Z3 in the film?',
             opts=['About $1 million', 'About $10 million', 'About $50 million', 'Nothing'], correct=3,
             reveal=("Nothing. No money changed hands: BMW tied the film to the car&rsquo;s launch "
                     "campaign instead, and it had script approval.")),
   also=[('civic', 'Civic Type R Trivia', 'civic-type-r/civic-type-r-ebook-cover.jpg'),
         ('e30', 'E30 Trivia', 'e30/e30-ebook-cover.jpg'),
         ('miata', 'Mazda MX-5 Miata Trivia', 'miata/miata-ebook-cover.jpg'),
         ('rx7', 'RX-7 Trivia', 'rx7/rx7-ebook-cover.jpg')],
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
    if not mp4.exists():
        # Ролика ещё нет (будет после выхода книги): секцию трейлера убираем, чтобы не показывать видео донора.
        tr = re.search(r'<section id="trailer">.*?</section>\n\n', s, re.S)
        assert tr, 'секция трейлера донора не найдена'
        s = s[:tr.start()] + s[tr.end():]
        vname = '(нет ролика)'
    else:
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

    # 6б. «2 sources per fact» — у BMW-книг часть фактов с одним источником (factcheck.json), число не подтверждено
    s = s.replace('<div class="num">2</div><div class="lbl">Sources per fact</div>',
                  '<div class="num">4</div><div class="lbl">Choices per question</div>')

    s = s.replace('Every fact verified against two independent sources.',
                  'Facts checked against reference works and period coverage.')

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
    for t in cfg.get('allow', []):
        probe = probe.replace(t, '')
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
