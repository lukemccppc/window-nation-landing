# Renuity Kitchen Refacing Landing Pages

One shared kitchen-refacing landing page, built for each Renuity brand from config.

| Route | Brand | Market |
|---|---|---|
| `/fhia-kitchens/` | FHIA Remodeling | Florida |
| `/mad-city-kitchens/` | Mad City Kitchens | Wisconsin |

Each route is a static `index.html` + `thank-you.html` + `assets/`. It needs no server code and works on GitHub Pages, Netlify, or WordPress uploads, including direct navigation and refresh.

## Build

```bash
python3 renuity-kitchens/build.py            # all brands
python3 renuity-kitchens/build.py mad-city   # one brand
```

This needs Python 3 and Pillow (with AVIF support, which is standard in Pillow ≥ 11.2). The build crops and resizes the source photos to responsive WebP, trims and exports each logo without distortion, and inlines the CSS and JS. It writes to `../<route>/`. **Never edit the generated pages. Edit the source and rebuild.**

Local preview: `python3 -m http.server 4340` from the repo root, then open `/fhia-kitchens/`.

## Layout

```
renuity-kitchens/
  build.py              orchestration + image pipeline
  components.py         Header, Hero, Offer, LeadForm, TrustStrip, Transformation,
                        Styles, Benefits, Process, Gallery, FinalCTA, Footer, StickyCTA
  config/
    brands/<id>.json    name, logo, colors/fonts, metadata, trust claims, legal links, attribution ids
    content.json        shared section copy
    offer.json          campaign offer + disclosures + expiry
    legal.json          consent text + links
    tracking.json       endpoint, GTM, events, attribution keys
  styles/kitchen.css    shared styles; brand values arrive as CSS custom properties
  scripts/lead-form.js  validation, attribution, dataLayer events, lead adapter, sticky CTA
  assets/shared|fhia|mad-city
```

**Adding a brand:** copy `config/brands/fhia.json` to `config/brands/<new>.json`, add its logo under `assets/<new>/`, and run the build. Set `theme.mode` to `light` or `dark` for the hero surface. The body class `shape-round` or `shape-gable` sets the offer plate's brand detail.

## Lead form and tracking

The form has 5 fields: first name, last name, email, phone, and ZIP. Validation runs inline; NANP phone format and a 5-digit ZIP are enforced. Errors are announced and focus moves to the first invalid field. Values are kept after errors, and duplicate submits are blocked.

- **Endpoint (`tracking.json → endpoint`)**: empty by default. With no endpoint, submit shows an error, logs the payload to the console, and fires `kitchen_form_submit_failure`. It never fakes a success.
- **Payload (`payloadFormat`)**: `renuity-form` sends URL-encoded data with the same field names as the live Renuity form (`fname, lname, email, phone, zip, city, state, landingpage, landingpagedetail, ua, trustedform, jornaya, transid, pubid, s1–s3, cid, source`). It adds `brand`, `landing_page_id`, `service`, `offer`, `consent_text`, and all captured attribution. `json` posts the same object as JSON. City and state come from the ZIP via zippopotam.us, with a 3-second cap so the lookup never blocks a lead.
- **Attribution**: `gclid, gbraid, wbraid, utm_*, msclkid, fbclid, transid, pubid, s1–s3, cid`, plus the landing URL and referrer. Values are first-touch per session and stored separately for each brand.
- **dataLayer events** (all carry `brand_id`, `landing_page_id`, `page_path`):
  `kitchen_cta_click` (`cta_location`), `kitchen_form_start`, `kitchen_form_validation_error` (`error_fields`), `kitchen_form_submit_attempt`, `kitchen_lead_submitted` (only after a 2xx; includes `user_data` for enhanced conversions; deduped per session), and `kitchen_form_submit_failure` (`failure_reason`).
- **GTM**: set `gtmId` to load the container. Google Ads and GA4 conversions should trigger on `kitchen_lead_submitted`.
- **TrustedForm / Jornaya**: off until `trustedForm: true` and `jornayaCampaignKey` are set.
- **Cake**: the live Renuity page sets `transid` with a Cake SDK snippet. The snippet isn't included here. Either pass `transid` (and `pubid`/`s1–s3`) in the URL, or add the snippet once the offer ID is confirmed (`cakeOfferId` in the brand config).

## Needs approval before paid traffic

1. **Offer disclosures** (`offer.json`, `_status: PENDING_APPROVAL`). The headline offer matches renuityhome.com/kitchens. The fine print is the Renuity bathroom-page text with the dates changed, because no kitchen-specific disclosure was published. Mad City's own site currently advertises **18** months, not 12.
2. **Consent** (`legal.json`). This is Renuity's current consent from madcitywindows.com, with only the button name changed.
3. **Claims**: FHIA's "250,000+ customers" is a Renuity-wide figure. Mad City's lifetime warranty wording and "one day" timing are summarized from madcitywindows.com.
4. **Legal entity and links**: FHIA uses Renuity Operations, LLC / NMLS #2781386 and renuityhome.com policies. Mad City uses "© 2013 – Mad City Windows" and madcitywindows.com policies.
5. **Photos**: shown as inspiration, not labeled as customer projects. No before-and-after images are used.
