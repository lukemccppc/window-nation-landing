"""Page components shared by every Renuity kitchen brand.

Each component takes the merged context `c` (brand + offer + legal + content + images)
and returns an HTML string. Nothing here names a brand directly; it all comes from config.
"""
from html import escape as e

ARROW = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>'
CHECK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7"/></svg>'
DASH = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="8.5" stroke-width="1.6"/><path d="M8.5 12h7"/></svg>'

ICONS = {
    'users': '<circle cx="9" cy="8" r="3.2"/><path d="M3 19.5c0-3.3 2.7-5.5 6-5.5s6 2.2 6 5.5"/><path d="M15.5 4.9a3.2 3.2 0 0 1 0 6.2M17.5 14.3c2.1.6 3.5 2.6 3.5 5.2"/>',
    'droplet': '<path d="M12 3.2s-6 6.6-6 11a6 6 0 0 0 12 0c0-4.4-6-11-6-11z"/><path d="M9.2 14.8a2.9 2.9 0 0 0 2.6 2.7"/>',
    'clock': '<circle cx="12" cy="12" r="8.6"/><path d="M12 7.3V12l3.2 2"/>',
    'ruler': '<path d="M4 16.5 16.5 4 20 7.5 7.5 20z"/><path d="M8 12.5l1.8 1.8M10.6 9.9l1.2 1.2M13.2 7.3l1.8 1.8"/>',
    'home': '<path d="M3.5 11 12 4l8.5 7"/><path d="M5.8 9.4V20h12.4V9.4"/><path d="M10 20v-5.2h4V20"/>',
    'shield': '<path d="M12 3.3 19 6v5.6c0 4.4-3 7.7-7 9.1-4-1.4-7-4.7-7-9.1V6z"/><path d="m8.8 12 2.3 2.3 4.2-4.4"/>',
    'pin': '<path d="M12 21s-6.5-5.6-6.5-11a6.5 6.5 0 0 1 13 0c0 5.4-6.5 11-6.5 11z"/><circle cx="12" cy="10" r="2.4"/>',
}


def icon(name):
    return f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[name]}</svg>'


def img(c, key, alt, sizes, cls='', lazy=True, extra=''):
    """Responsive <img> for an image processed by build.py."""
    im = c['images'][key]
    srcset = ', '.join(f'{p} {w}w' for w, p in im['files'])
    load = 'loading="lazy" decoding="async"' if lazy else 'fetchpriority="high" decoding="async"'
    cls = f' class="{cls}"' if cls else ''
    return (f'<img{cls} src="{im["default"]}" srcset="{srcset}" sizes="{sizes}" '
            f'width="{im["w"]}" height="{im["h"]}" alt="{e(alt)}" {load}{extra}>')


def cta(c, where, text=None, cls='btn', icon_svg=ARROW):
    text = text or c['legal']['buttonLabel']
    return f'<a class="{cls}" href="#quote" data-cta="{where}">{e(text)} {icon_svg}</a>'


# ---------------------------------------------------------------------------

def header(c):
    b = c['brand']
    return f'''<header class="site-header">
  <div class="wrap">
    <a class="logo" href="#top" aria-label="{e(b['name'])} home">
      <img src="{c['logo']['header']}" alt="{e(b['logo']['alt'])}" width="{c['logo']['w']}" height="{c['logo']['h']}">
    </a>
    <div class="header-right">
      <p class="header-note">{e(b['copy']['headerNote'])}</p>
      <a class="btn btn-sm" href="#quote" data-cta="header"><span class="long">Get My Free Quote</span><span class="short">Free Quote</span></a>
    </div>
  </div>
</header>'''


def offer_plate(c):
    o = c['offer']
    return f'''<div class="offer" data-offer>
        <p class="offer-label">{e(o['label'])}</p>
        <p class="offer-main"><b>{e(o['primaryLead'])}</b><span>{e(o['primaryTail'])}</span></p>
        <p class="offer-sub"><em>+</em> {e(o['secondary'])}</p>
        <p class="offer-fine">{e(o['scope'])}. Ends {c['offer_expires_short']}. <a href="#offer-terms">See offer terms*</a></p>
      </div>'''


def lead_form(c):
    h, legal = c['content']['hero'], c['legal']
    fields = [
        ('first_name', 'First name', 'text', 'given-name', 'text', ''),
        ('last_name', 'Last name', 'text', 'family-name', 'text', ''),
        ('email', 'Email address', 'email', 'email', 'email', ''),
        ('phone', 'Phone number', 'tel', 'tel-national', 'tel', ' maxlength="14"'),
        ('zip', 'ZIP code', 'text', 'postal-code', 'numeric', ' maxlength="5"'),
    ]

    def field(name, label, typ, auto, mode, extra):
        return (f'<div class="field"><label for="{name}">{label}</label>'
                f'<input id="{name}" name="{name}" type="{typ}" inputmode="{mode}" autocomplete="{auto}" required '
                f'aria-describedby="{name}-err"{extra}><p class="err" id="{name}-err" aria-live="polite"></p></div>')

    f = [field(*x) for x in fields]
    return f'''<div class="form-card">
          <h2 id="form-title">{e(h['formTitle'])}</h2>
          <p class="form-sub">{e(h['formSub'])}</p>
          <form id="leadForm" class="lead-form" novalidate aria-labelledby="form-title">
            <div class="form-alert" role="alert" id="formAlert"></div>
            <div class="row">{f[0]}{f[1]}</div>
            {f[2]}
            {f[3]}
            {f[4]}
            <div class="hp" aria-hidden="true"><label for="company">Company</label><input id="company" name="company" type="text" tabindex="-1" autocomplete="off"></div>
            <input type="hidden" id="leadid_token" name="universal_leadid" value="">
            <button type="submit" class="btn submit"><span class="spinner" aria-hidden="true"></span><span class="label">{e(legal['buttonLabel'])}</span> {ARROW}</button>
            <!-- Consent: see config/legal.json (_status PENDING_APPROVAL). -->
            <p class="consent" id="consentText">{c['consent_html']}</p>
          </form>
        </div>'''


def hero(c):
    h = c['content']['hero']
    hm, hd = c['images']['hero-mobile'], c['images']['hero-desktop']
    srcset_d = ', '.join(f'{p} {w}w' for w, p in hd['files'])
    return f'''<section class="hero{c['dark_cls']}" aria-labelledby="hero-title">
    <div class="hero-grid">
      <div class="hero-copy">
        <h1 id="hero-title">{e(h['h1'])}</h1>
        <p class="lede">{h['lede']}</p>
      </div>
      <div class="hero-media">
        <picture>
          <source media="(min-width:1024px)" srcset="{srcset_d}" sizes="55vw">
          {img(c, 'hero-mobile', h['imageAlt'], '100vw', lazy=False)}
        </picture>
        {offer_plate(c)}
      </div>
      <div class="hero-form" id="quote">
        {lead_form(c)}
      </div>
    </div>
  </section>'''


def trust(c):
    items = ''.join(f'<li>{icon(t["icon"])}<div><strong>{e(t["title"])}</strong><span>{e(t["text"])}</span></div></li>'
                    for t in c['brand']['copy']['trust'])
    return f'''<section class="trust" aria-label="Why homeowners choose {e(c['brand']['name'])}">
    <div class="wrap"><ul>{items}</ul></div>
  </section>'''


def transformation(c):
    t = c['content']['transformation']
    new = ''.join(f'<li>{CHECK}{e(x)}</li>' for x in t['new'])
    keep = ''.join(f'<li>{DASH}{e(x)}</li>' for x in t['keep'])
    return f'''<section class="sec" aria-labelledby="transform-title">
    <div class="wrap split">
      <div class="split-media">{img(c, 'transform', t['imageAlt'], '(min-width:1024px) 600px, 100vw')}</div>
      <div class="split-copy">
        <h2 id="transform-title">{e(t['h2'])}</h2>
        <p class="lede">{e(t['lede'])}</p>
        <div class="changes">
          <div><h3>{e(t['newTitle'])}</h3><ul>{new}</ul></div>
          <div class="keep"><h3>{e(t['keepTitle'])}</h3><ul>{keep}</ul></div>
        </div>
      </div>
    </div>
  </section>'''


def styles(c):
    s = c['content']['styles']
    items = ''.join(f'<li>{img(c, x["img"], x["alt"], "(min-width:900px) 280px, 50vw")}<h3>{e(x["name"])}</h3><p>{e(x["text"])}</p></li>'
                    for x in s['items'])
    return f'''<section class="sec sec-tint" aria-labelledby="styles-title">
    <div class="wrap">
      <div class="sec-head">
        <h2 id="styles-title">{e(s['h2'])}</h2>
        <p class="lede">{e(s['lede'])}</p>
      </div>
      <ul class="styles">{items}</ul>
    </div>
  </section>'''


def why(c):
    w = c['content']['why']
    items = ''.join(f'<li><div><h3>{e(x["h3"])}</h3></div><p>{e(x["p"])}</p></li>' for x in w['items'])
    return f'''<section class="sec" aria-labelledby="why-title">
    <div class="wrap why">
      <div class="sec-head">
        <h2 id="why-title">{e(w['h2'])}</h2>
        <p class="lede">{e(w['lede'])}</p>
      </div>
      <ol class="benefits">{items}</ol>
    </div>
  </section>'''


def process(c):
    p = c['content']['process']
    steps = ''.join(f'<li><h3>{e(s["h3"])}</h3><p>{e(s["p"])}</p></li>' for s in p['steps'])
    return f'''<section class="sec sec-tint" aria-labelledby="process-title">
    <div class="wrap">
      <div class="sec-head"><h2 id="process-title">{e(p['h2'])}</h2></div>
      <ol class="steps">{steps}</ol>
      <p class="timeline"><strong>How long does it take?</strong> {e(c['brand']['copy']['timelineNote'])}</p>
    </div>
  </section>'''


def gallery(c):
    g = c['content']['gallery']
    side = ''.join(f'<figure class="g-side">{img(c, x["img"], x["alt"], "(min-width:768px) 440px, 50vw")}</figure>' for x in g['side'])
    return f'''<section class="sec" aria-labelledby="gallery-title">
    <div class="wrap">
      <div class="sec-head">
        <h2 id="gallery-title">{e(g['h2'])}</h2>
        <p class="lede">{e(g['lede'])}</p>
      </div>
      <div class="gallery">
        <figure class="g-main">{img(c, g['main']['img'], g['main']['alt'], '(min-width:768px) 720px, 100vw')}</figure>
        {side}
      </div>
      <p class="note">{e(c['legal']['imageNote'])}</p>
    </div>
  </section>'''


def final_cta(c):
    f, o = c['content']['final'], c['offer']
    return f'''<section class="final" aria-labelledby="final-title">
    <div class="wrap">
      <div class="final-card{c['dark_cls']}">
        <div class="final-copy">
          <h2 id="final-title">{e(f['h2'])}</h2>
          <p>{e(c['brand']['copy']['finalLede'])}</p>
          <p class="final-offer" data-offer><b>{e(o['primary'])}</b><i>+</i> {e(o['secondary'])}<a href="#offer-terms" aria-label="See offer terms">*</a></p>
          {cta(c, 'final')}
        </div>
        <div class="final-media">{img(c, 'cta', f['imageAlt'], '(min-width:900px) 480px, 100vw')}</div>
      </div>
    </div>
  </section>'''


def footer(c):
    b, l = c['brand'], c['brand']['legal']
    nmls = f' · <a href="{l["nmlsUrl"]}" target="_blank" rel="noopener">{e(l["nmls"])}</a>' if l.get('nmls') else ''
    warranty = f'<p>{e(l["warrantyNote"])}</p>' if l.get('warrantyNote') else ''
    disclosures = ''.join(f'<p>{e(d)}</p>' for d in c['offer_disclosures'])
    return f'''<footer class="site-footer">
  <div class="wrap">
    <div class="foot-top">
      <div class="foot-brand">
        <img src="{c['logo']['footer']}" alt="{e(b['logo']['alt'])}" width="{c['logo']['fw']}" height="{c['logo']['fh']}" loading="lazy">
        <p><strong>{e(b['name'])}</strong>{e(l['footerOwnership'])} {e(b['serviceArea']['footer'])}</p>
      </div>
      <nav class="foot-links" aria-label="Legal">
        <a href="{l['privacyUrl']}" target="_blank" rel="noopener">Privacy Policy</a>
        <a href="{l['termsUrl']}" target="_blank" rel="noopener">Terms &amp; Conditions</a>
      </nav>
    </div>
    <div class="foot-legal" id="offer-terms">
      <!-- Offer disclosures: see config/offer.json (_status PENDING_APPROVAL). -->
      <div data-offer>{disclosures}</div>
      {warranty}
      <p>{e(c['legal']['imageNote'])}</p>
      <p>&copy; {e(l.get('copyrightYearPrefix', ''))}<span data-year>{c['year']}</span> {e(l['copyright'])}{nmls}</p>
    </div>
  </div>
</footer>'''


def sticky(c):
    o = c['offer']
    return f'''<div class="sticky-cta" id="stickyCta" aria-hidden="true">
  <p data-offer>{e(o['primary'])}<span>+ {e(o['secondary'])}</span></p>
  <a class="btn" href="#quote" data-cta="sticky" tabindex="-1">Get My Free Quote</a>
</div>'''


def head(c, title, description, preload=True):
    b = c['brand']
    pre = ''
    if preload:
        hm, hd = c['images']['hero-mobile'], c['images']['hero-desktop']
        pre = (f'<link rel="preload" as="image" imagesrcset="{", ".join(f"{p} {w}w" for w, p in hm["files"])}" imagesizes="100vw" media="(max-width:1023px)" fetchpriority="high">\n'
               f'<link rel="preload" as="image" imagesrcset="{", ".join(f"{p} {w}w" for w, p in hd["files"])}" imagesizes="55vw" media="(min-width:1024px)" fetchpriority="high">\n')
    return f'''<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<meta name="robots" content="noindex, nofollow">
<meta name="theme-color" content="{b['meta']['themeColor']}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:site_name" content="{e(b['name'])}">
<link rel="icon" href="{c['logo']['icon']}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
{pre}<link rel="stylesheet" href="{b['theme']['fontsHref']}">
<style>
{c['theme_css']}
{c['css']}
</style>
</head>'''
