/* Shared runtime for every Renuity kitchen brand page.
   Reads window.KITCHEN_CONFIG (written by build.py from config/*.json).
   Nothing here counts a lead as submitted until the endpoint returns 2xx. */
(function(){
  var C = window.KITCHEN_CONFIG, T = C.tracking, d = document, w = window;
  var STORE_KEY = 'rk_attr_' + C.brandId;
  var DONE_KEY = 'rk_lead_sent_' + C.brandId;

  // --- Data layer -----------------------------------------------------------
  w.dataLayer = w.dataLayer || [];
  function push(event, extra){
    var o = { event: event, brand_id: C.brandId, landing_page_id: C.landingPageId, page_path: location.pathname };
    for (var k in extra) o[k] = extra[k];
    w.dataLayer.push(o);
  }
  if (T.gtmId) {
    w.dataLayer.push({ 'gtm.start': Date.now(), event: 'gtm.js' });
    var g = d.createElement('script'); g.async = true;
    g.src = 'https://www.googletagmanager.com/gtm.js?id=' + encodeURIComponent(T.gtmId);
    d.head.appendChild(g);
  }

  // --- Offer: hide automatically once it expires ----------------------------
  var offerLive = C.offer.enabled && new Date() <= new Date(C.offer.expires + 'T23:59:59');
  if (!offerLive) d.querySelectorAll('[data-offer]').forEach(function(el){ el.hidden = true; });

  // --- Attribution: first touch per session, per brand ----------------------
  var attr = {};
  try { attr = JSON.parse(sessionStorage.getItem(STORE_KEY) || '{}'); } catch(e) {}
  var qs = new URLSearchParams(location.search), changed = false;
  T.attributionKeys.forEach(function(k){ var v = qs.get(k); if (v && !attr[k]) { attr[k] = v.slice(0, 500); changed = true; } });
  if (!attr.landing_page_url) { attr.landing_page_url = location.href; attr.referrer = d.referrer || ''; changed = true; }
  if (changed) { try { sessionStorage.setItem(STORE_KEY, JSON.stringify(attr)); } catch(e) {} }

  // --- Optional lead-certification scripts (off until configured) -----------
  if (T.trustedForm) {
    var tf = d.createElement('script'); tf.async = true;
    tf.src = 'https://api.trustedform.com/trustedform.js?field=xxTrustedFormCertUrl&ping_field=xxTrustedFormPingUrl&l=' + Date.now() + Math.random();
    d.body.appendChild(tf);
  }
  if (T.jornayaCampaignKey) {
    var jn = d.createElement('script'); jn.async = true; jn.id = 'LeadiDscript_campaign';
    jn.src = '//create.lidstatic.com/campaign/' + encodeURIComponent(T.jornayaCampaignKey) + '.js?snippet_version=2';
    d.body.appendChild(jn);
  }

  // --- Form -----------------------------------------------------------------
  var form = d.getElementById('leadForm');
  var btn = form.querySelector('.submit'), label = btn.querySelector('.label'), btnText = label.textContent;
  var alertBox = d.getElementById('formAlert');
  var el = function(n){ return form.elements[n]; };

  var rules = {
    first_name: function(v){ return /\p{L}/u.test(v); },
    last_name: function(v){ return /\p{L}/u.test(v); },
    email: function(v){ return /^[^\s@]+@[^\s@.]+(\.[^\s@.]+)*\.[a-z]{2,}$/i.test(v.trim()); },
    phone: function(v){ var n = digits10(v); return n.length === 10 && /^[2-9]\d{2}[2-9]/.test(n); },
    zip: function(v){ return /^\d{5}$/.test(v.trim()); }
  };
  var messages = {
    first_name: 'Please enter your first name.',
    last_name: 'Please enter your last name.',
    email: 'Please enter a valid email, like name@example.com.',
    phone: 'Please enter a valid 10-digit U.S. phone number.',
    zip: 'Please enter a valid 5-digit ZIP code.'
  };
  function digits10(v){ var n = v.replace(/\D/g, ''); if (n.length === 11 && n[0] === '1') n = n.slice(1); return n.slice(0, 10); }

  function check(name){
    var input = el(name), ok = rules[name](input.value), field = input.closest('.field');
    if (ok) { field.removeAttribute('data-invalid'); input.removeAttribute('aria-invalid'); }
    else { field.setAttribute('data-invalid', ''); input.setAttribute('aria-invalid', 'true'); d.getElementById(name + '-err').textContent = messages[name]; }
    return ok;
  }

  var started = false;
  Object.keys(rules).forEach(function(name){
    var input = el(name);
    input.addEventListener('focus', function(){ if (!started) { started = true; push(T.events.formStart, { first_field: name }); } });
    input.addEventListener('blur', function(){ if (input.value.trim()) { input.dataset.touched = '1'; check(name); } });
    input.addEventListener('input', function(){ if (input.dataset.touched) check(name); });
  });

  el('phone').addEventListener('input', function(){
    var n = digits10(this.value);
    this.value = n.length > 6 ? '(' + n.slice(0,3) + ') ' + n.slice(3,6) + '-' + n.slice(6)
               : n.length > 3 ? '(' + n.slice(0,3) + ') ' + n.slice(3) : n;
  });
  el('zip').addEventListener('input', function(){ this.value = this.value.replace(/\D/g, '').slice(0, 5); geo = null; });

  // ZIP -> city/state, same fields the Renuity form sends. Never blocks a lead for more than 3s.
  var geo = null;
  function lookupZip(zip){
    if (geo && geo.zip === zip) return Promise.resolve(geo);
    var done = fetch(T.zipLookup + zip).then(function(r){ return r.ok ? r.json() : null; }).then(function(j){
      var p = j && j.places && j.places[0];
      geo = { zip: zip, city: p ? p['place name'] : '', state: p ? p['state abbreviation'] : '' };
      return geo;
    }).catch(function(){ return { zip: zip, city: '', state: '' }; });
    return Promise.race([done, new Promise(function(r){ setTimeout(function(){ r({ zip: zip, city: '', state: '' }); }, 3000); })]);
  }
  el('zip').addEventListener('change', function(){ if (rules.zip(this.value)) lookupZip(this.value); });

  function hidden(name){ var f = form.querySelector('[name="' + name + '"]'); return f ? f.value : ''; }

  // Lead adapter. 'renuity-form' mirrors the field names of the live Renuity bathroom form
  // (renuityhomedeals.com/bathrooms submit.php) and adds attribution; 'json' posts one flat object.
  function buildLead(g){
    var f = form.elements;
    return Object.assign({
      fname: f.first_name.value.trim(),
      lname: f.last_name.value.trim(),
      email: f.email.value.trim(),
      phone: digits10(f.phone.value),
      zip: f.zip.value.trim(),
      city: g.city, state: g.state,
      landingpage: location.origin + location.pathname,
      landingpagedetail: location.href,
      ua: navigator.userAgent,
      trustedform: hidden('xxTrustedFormCertUrl'),
      jornaya: hidden('universal_leadid'),
      brand: C.brandId,
      brand_name: C.brandName,
      landing_page_id: C.landingPageId,
      service: 'kitchen_cabinet_refacing',
      offer: offerLive ? C.offer.summary : '',
      consent_text: d.getElementById('consentText').textContent.replace(/\s+/g, ' ').trim(),
      submitted_at: new Date().toISOString(),
      source: 'site'
    }, attr);
  }
  function send(lead){
    var json = T.payloadFormat === 'json';
    return fetch(T.endpoint, {
      method: 'POST',
      headers: { 'Content-Type': json ? 'application/json' : 'application/x-www-form-urlencoded' },
      body: json ? JSON.stringify(lead) : new URLSearchParams(lead).toString()
    }).then(function(res){ if (!res.ok) throw new Error('HTTP ' + res.status); return res; });
  }

  function showAlert(msg){ alertBox.textContent = msg; alertBox.classList.add('show'); alertBox.setAttribute('tabindex', '-1'); alertBox.focus(); }
  function reset(){ sending = false; btn.removeAttribute('aria-busy'); btn.disabled = false; label.textContent = btnText; }

  var sending = false;
  form.addEventListener('submit', function(e){
    e.preventDefault();
    if (sending) return;
    alertBox.classList.remove('show');
    if (el('company').value) return; // honeypot

    var bad = [];
    Object.keys(rules).forEach(function(name){ el(name).dataset.touched = '1'; if (!check(name)) bad.push(name); });
    if (bad.length) { push(T.events.formError, { error_fields: bad.join(',') }); el(bad[0]).focus(); return; }

    push(T.events.submitAttempt, {});
    if (!T.endpoint) {
      console.warn('[kitchens] tracking.endpoint is not configured; the lead was NOT sent.', buildLead({ city: '', state: '' }));
      push(T.events.submitFailure, { failure_reason: 'endpoint_not_configured' });
      showAlert('Sorry, we couldn’t send your request right now. Please try again in a few minutes.');
      return;
    }

    sending = true;
    btn.setAttribute('aria-busy', 'true'); btn.disabled = true; label.textContent = 'Sending…';
    var lead;
    lookupZip(el('zip').value.trim())
      .then(function(g){ lead = buildLead(g); return send(lead); })
      .then(function(){
        var go = function(){ if (go.done) return; go.done = true; location.href = T.thankYouPath; };
        var already = false;
        try { already = sessionStorage.getItem(DONE_KEY) === lead.email + lead.phone; sessionStorage.setItem(DONE_KEY, lead.email + lead.phone); } catch(e) {}
        if (already) return go(); // same person re-submitting: no second conversion
        push(T.events.submitSuccess, {
          lead_service: 'kitchen_cabinet_refacing',
          user_data: { email: lead.email, phone_number: '+1' + lead.phone, address: { postal_code: lead.zip } },
          eventCallback: go, eventTimeout: 1500
        });
        setTimeout(go, T.gtmId ? 1600 : 0);
      })
      .catch(function(err){
        console.error('[kitchens] lead submit failed', err);
        push(T.events.submitFailure, { failure_reason: String(err && err.message || err) });
        reset();
        showAlert('Something went wrong sending your request. Please check your connection and try again.');
      });
  });

  // --- CTAs scroll to the form ----------------------------------------------
  var fine = w.matchMedia('(pointer: fine)').matches;
  d.querySelectorAll('[data-cta]').forEach(function(a){
    a.addEventListener('click', function(e){
      e.preventDefault();
      push(T.events.ctaClick, { cta_location: a.getAttribute('data-cta') });
      var reduce = w.matchMedia('(prefers-reduced-motion: reduce)').matches;
      var target = d.getElementById('quote');
      var y = target.getBoundingClientRect().top + w.scrollY - d.querySelector('.site-header').offsetHeight - 12;
      w.scrollTo({ top: y, behavior: reduce ? 'auto' : 'smooth' });
      // Desktop only: focusing on touch devices would pop the keyboard mid-scroll.
      if (fine) setTimeout(function(){ el('first_name').focus({ preventScroll: true }); }, reduce ? 0 : 450);
    });
  });

  // --- Sticky mobile CTA: after the hero, while the form is off screen, never over a keyboard
  var sticky = d.getElementById('stickyCta');
  if (sticky && 'IntersectionObserver' in w) {
    var formVisible = true, pastHero = false, typing = false;
    var update = function(){
      var show = !formVisible && pastHero && !typing;
      sticky.classList.toggle('show', show);
      sticky.setAttribute('aria-hidden', show ? 'false' : 'true');
      sticky.querySelector('a').tabIndex = show ? 0 : -1;
      d.body.classList.toggle('has-sticky', show);
    };
    new IntersectionObserver(function(en){ formVisible = en[0].isIntersecting; update(); }).observe(form);
    new IntersectionObserver(function(en){ pastHero = !en[0].isIntersecting && en[0].boundingClientRect.top < 0; update(); }).observe(d.querySelector('.hero'));
    d.addEventListener('focusin', function(e){ typing = /INPUT|TEXTAREA|SELECT/.test(e.target.tagName); update(); });
    d.addEventListener('focusout', function(){ typing = false; update(); });
  }
})();
