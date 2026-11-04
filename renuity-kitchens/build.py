#!/usr/bin/env python3
"""Build every Renuity kitchen brand page.

    python3 renuity-kitchens/build.py            # all brands
    python3 renuity-kitchens/build.py fhia       # one brand

Reads config/*.json + config/brands/<id>.json and writes a self-contained static page to
../<brand.route>/ (index.html, thank-you.html, assets/). Requires Pillow (with AVIF support).
"""
import json
import shutil
import sys
from datetime import date
from pathlib import Path

from PIL import Image

import components as K

ROOT = Path(__file__).resolve().parent
OUT_ROOT = ROOT.parent
CFG = ROOT / 'config'
SHARED = ROOT / 'assets' / 'shared'

# key: (source, crop aspect w/h or None, focus x, focus y, widths, quality)
IMAGES = {
    'hero-mobile':     ('hero-white-shaker-blue-tile.jpg', 16 / 10, .42, .55, [640, 960, 1280], 74),
    'hero-desktop':    ('hero-white-shaker-blue-tile.jpg', 1 / 1, .30, .5, [900, 1300], 74),
    'transform':       ('white-cabinets-butcher-block.jpg', 5 / 4, .5, .5, [640, 960, 1280], 74),
    'finish-white':    ('finish-white-shaker.avif', 4 / 3, .62, .5, [400, 600], 80),
    'finish-gray':     ('finish-soft-gray.avif', 4 / 3, .5, .62, [400, 640], 80),
    'finish-cherry':   ('finish-warm-cherry.jpg', 4 / 3, .5, .62, [400, 640], 76),
    'finish-espresso': ('finish-espresso.jpg', 4 / 3, .6, .5, [400, 640], 76),
    'gallery-main':    ('gallery-white-dark-island.jpg', 1 / 1, .5, .55, [720, 1100, 1440], 74),
    'gallery-side-1':  ('gallery-white-island-pendants.jpg', 4 / 3, .5, .62, [480, 880], 76),
    'gallery-side-2':  ('gallery-white-l-shape.jpg', 4 / 3, .45, .6, [480, 880], 76),
    'cta':             ('cta-gray-brass.avif', 4 / 3, .55, .5, [640], 80),
}


def load(p):
    return json.loads(Path(p).read_text())


def crop(im, aspect, fx, fy):
    if not aspect:
        return im
    w, h = im.size
    if w / h > aspect:
        nw = round(h * aspect)
        x = min(max(round(w * fx - nw / 2), 0), w - nw)
        return im.crop((x, 0, x + nw, h))
    nh = round(w / aspect)
    y = min(max(round(h * fy - nh / 2), 0), h - nh)
    return im.crop((0, y, w, y + nh))


def build_images(out):
    """Crop + resize every shared image to WebP. Widths above the source size are skipped."""
    dest = out / 'assets'
    info = {}
    for key, (src, aspect, fx, fy, widths, q) in IMAGES.items():
        im = crop(Image.open(SHARED / src).convert('RGB'), aspect, fx, fy)
        files = []
        for wd in widths:
            wd = min(wd, im.width)
            if files and files[-1][0] == wd:
                continue
            r = im.resize((wd, round(wd * im.height / im.width)), Image.LANCZOS)
            name = f'{key}-{wd}.webp'
            r.save(dest / name, 'WEBP', quality=q, method=6)
            files.append((wd, f'assets/{name}'))
        last = files[-1][0]
        info[key] = {'files': files, 'default': files[min(1, len(files) - 1)][1],
                     'w': last, 'h': round(last * im.height / im.width)}
    return info


def build_logo(brand, out):
    """Trim transparent padding, then export header/footer sizes. Never stretched: width follows height."""
    im = Image.open(ROOT / brand['logo']['src']).convert('RGBA')
    im = im.crop(im.getchannel('A').getbbox())

    def save(h, name):
        r = im.resize((round(h * im.width / im.height), h), Image.LANCZOS)
        r.save(out / 'assets' / name, 'WEBP', quality=92, method=6)
        return r.size

    hh = brand['logo']['headerHeight'] * 2
    w, h = save(hh, 'logo.webp')
    fw, fh = save(112, 'logo-footer.webp')
    ico = im.copy()
    ico.thumbnail((64, 64))
    canvas = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    canvas.paste(ico, ((64 - ico.width) // 2, (64 - ico.height) // 2))
    canvas.save(out / 'assets' / 'icon.png')
    return {'header': 'assets/logo.webp', 'footer': 'assets/logo-footer.webp', 'icon': 'assets/icon.png',
            'w': round(w / 2), 'h': round(h / 2), 'fw': round(fw / 2), 'fh': round(fh / 2)}


def theme_vars(brand):
    t = brand['theme']
    dark = t['mode'] == 'dark'
    v = {
        'head': t['headFont'], 'body': t['bodyFont'], 'head-w': t['headWeight'],
        'navy': t['navy'], 'navy-deep': t['navyDeep'], 'accent': t['accent'], 'accent-text': t['accentText'],
        'accent-soft': t['accentSoft'], 'surface': t['surface'], 'tint': t['tint'],
        'cta-bg': t['ctaBg'], 'cta-hover': t['ctaHover'], 'cta-ink': t['ctaInk'],
        'offer-bg': t['offerBg'], 'offer-ink': t['offerInk'], 'offer-accent': t['offerAccent'],
        'radius': t['radius'], 'radius-sm': t['radiusSm'],
        'step-radius': '50%' if t['radius'] != t['radiusSm'] or int(t['radius'].rstrip('px')) > 6 else t['radiusSm'],
        'hero-ink': '#FFFFFF' if dark else t['navy'],
        'hero-muted': '#C9D7E5' if dark else '#4E5B69',
        'logo-h': f"{brand['logo']['headerHeight']}px", 'logo-h-m': f"{brand['logo']['mobileHeaderHeight']}px",
    }
    return ':root{' + ';'.join(f'--{k}:{val}' for k, val in v.items()) + ';}'


def context(brand, offer, legal, content, tracking, images, logo):
    exp = date.fromisoformat(offer['expires'])
    exp_s = f'{exp.month}/{exp.day}/{exp.year}'
    btn = legal['buttonLabel']
    consent = (legal['consentHtml'].replace('{button}', btn)
               .replace('{callingTermsUrl}', legal['callingTermsUrl'])
               .replace('{consentPrivacyUrl}', legal['consentPrivacyUrl']))
    return {
        'brand': brand, 'offer': offer, 'legal': legal, 'content': content, 'images': images, 'logo': logo,
        'offer_expires_short': exp_s,
        'offer_disclosures': [d.replace('{expires}', exp_s) for d in offer['disclosures']],
        'consent_html': consent,
        'dark_cls': ' hero-dark' if brand['theme']['mode'] == 'dark' else '',
        'year': date.today().year,
        'theme_css': theme_vars(brand),
        'css': (ROOT / 'styles' / 'kitchen.css').read_text(),
        'runtime': {
            'brandId': brand['tracking']['brandId'], 'brandName': brand['name'],
            'landingPageId': brand['tracking']['landingPageId'],
            'offer': {'enabled': offer['enabled'], 'expires': offer['expires'],
                      'summary': f"{offer['primary']} + {offer['secondary']}"},
            'tracking': {k: v for k, v in tracking.items() if not k.startswith('_')},
        },
    }


def script(c):
    cfg = json.dumps(c['runtime'], separators=(',', ':'))
    return f'<script>window.KITCHEN_CONFIG={cfg};</script>\n<script>\n{(ROOT / "scripts" / "lead-form.js").read_text()}</script>'


def page(c):
    b = c['brand']
    shape = 'shape-gable' if b['id'] == 'mad-city' else 'shape-round'
    body = '\n  '.join(f(c) for f in (K.hero, K.trust, K.transformation, K.styles, K.why, K.process, K.gallery, K.final_cta))
    return f'''<!DOCTYPE html>
<html lang="en">
{K.head(c, b['meta']['title'], b['meta']['description'])}
<body class="brand-{b['id']} {b['theme'].get('shape', shape)}">
{K.header(c)}
<main id="top">
  {body}
</main>
{K.footer(c)}
{K.sticky(c)}
{script(c)}
</body>
</html>
'''


def thank_you(c):
    b, t = c['brand'], c['content']['thankYou']
    c = dict(c, css=c['css'])
    return f'''<!DOCTYPE html>
<html lang="en">
{K.head(c, f"Thank You | {b['name']}", f"Your {b['name']} quote request was received.", preload=False)}
<body class="brand-{b['id']}">
<header class="site-header"><div class="wrap"><a class="logo" href="./" aria-label="{K.e(b['name'])} home"><img src="{c['logo']['header']}" alt="{K.e(b['logo']['alt'])}" width="{c['logo']['w']}" height="{c['logo']['h']}"></a></div></header>
<main class="ty">
  <div class="ty-card">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="m7.5 12.3 3 3 6-6.3"/></svg>
    <h1>{K.e(t['h1'])}</h1>
    <p>{K.e(t['p'].replace('{brand}', b['name']))}</p>
  </div>
</main>
</body>
</html>
'''


def build(brand_id):
    brand = load(CFG / 'brands' / f'{brand_id}.json')
    out = OUT_ROOT / brand['route']
    if (out / 'assets').exists():
        shutil.rmtree(out / 'assets')
    (out / 'assets').mkdir(parents=True)
    images = build_images(out)
    logo = build_logo(brand, out)
    c = context(brand, load(CFG / 'offer.json'), load(CFG / 'legal.json'), load(CFG / 'content.json'),
                load(CFG / 'tracking.json'), images, logo)
    (out / 'index.html').write_text(page(c))
    (out / 'thank-you.html').write_text(thank_you(c))
    size = sum(p.stat().st_size for p in out.rglob('*') if p.is_file())
    print(f'{brand["name"]}: /{brand["route"]}/  ({size / 1024:.0f} KB total)')


if __name__ == '__main__':
    ids = sys.argv[1:] or sorted(p.stem for p in (CFG / 'brands').glob('*.json'))
    for i in ids:
        build(i)
