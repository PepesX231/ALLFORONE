/* ==========================================================
   All for One University — interactions
   1. setup         5. tracks carousel
   2. countdown     6. perks spotlight
   3. journey       7. detail sheet (<dialog>, back button, swipe)
   4. header, spy,  8. adaptive quality
      reveal, bar
   ========================================================== */
(function () {
  'use strict';

  /* ---------- 1. setup ---------- */
  var AFO = window.AFO, CFG = AFO.CFG, TRACKS = AFO.TRACKS;
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var root = document.documentElement;
  var clamp = function (v, a, b) { return Math.min(b, Math.max(a, v)); };
  var icon = function (n) { return '<svg class="ic"><use href="#i-' + n + '"/></svg>'; };
  var raf = window.requestAnimationFrame.bind(window);

  var reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  var lite = reduced || (navigator.deviceMemory && navigator.deviceMemory <= 2) ||
             (navigator.hardwareConcurrency && navigator.hardwareConcurrency <= 2);
  if (reduced) root.classList.add('rm');
  if (lite) root.classList.add('lite');
  var canAnimate = typeof Element.prototype.animate === 'function';
  var sda = root.classList.contains('sda');          // CSS scroll-driven animations available
  var mqDesktop = matchMedia('(min-width: 900px)');

  $$('[data-reg]').forEach(function (a) { a.href = CFG.registerUrl; });
  $$('[data-line]').forEach(function (a) { a.href = CFG.lineUrl; });

  var state = { heroVisible: true, sheetOpen: false };


  /* ---------- 0. cartoon shooting stars (fixed layer behind every section) ----------
     Each meteor gets its own shape, colour, size, angle and speed, and picks a new
     start point every loop, so the sky never repeats. Transform/opacity only. */
  (function () {
    var sky = document.getElementById('sky'); if (!sky || reduced || root.classList.contains('safe')) return;
    var ns = 'http://www.w3.org/2000/svg';
    var C = ['#ffd23f', '#ff8a3d', '#6fb2ff', '#ff6b8a', '#9b7bff', '#2fd08b', '#8ff0ff'];
    var SHAPES = [
      '<use href="#starface" width="48" height="48"/>',
      '<use href="#star4" x="4" y="4" width="40" height="40"/>',
      '<path d="M24 5l5.6 11.6 12.7 1.8-9.2 9 2.2 12.6L24 34l-11.3 6 2.2-12.6-9.2-9 12.7-1.8z" fill="currentColor" stroke="#1b1540" stroke-width="3.2" stroke-linejoin="round"/><circle cx="19" cy="21" r="1.9" fill="#1b1540"/><circle cx="29" cy="21" r="1.9" fill="#1b1540"/><path d="M20 27q4 3.2 8 0" fill="none" stroke="#1b1540" stroke-width="2.2" stroke-linecap="round"/>',
      '<circle cx="24" cy="24" r="12" fill="currentColor" stroke="#1b1540" stroke-width="3"/><circle cx="20" cy="20" r="3.6" fill="#fff" opacity=".85"/>',
      '<path d="M24 6c2 10 8 16 18 18-10 2-16 8-18 18-2-10-8-16-18-18 10-2 16-8 18-18z" fill="currentColor" stroke="#1b1540" stroke-width="3" stroke-linejoin="round"/>'
    ];
    var small = innerWidth < 720, n = lite ? (small ? 4 : 6) : (small ? 6 : 12);
    var r = function (a, b) { return a + Math.random() * (b - a); };
    function place(el, first) {
      var a = r(22, 40), s = r(small ? 20 : 26, small ? 36 : 50);
      el.style.setProperty('--x', r(-25, 85) + 'vw');
      el.style.setProperty('--y', r(-15, 55) + 'vh');
      el.style.setProperty('--a', a + 'deg');
      el.style.setProperty('--dist', r(95, 150) + 'vmax');
      el.style.setProperty('--s', s + 'px');
      el.style.setProperty('--len', (s * r(3, 6)) + 'px');
      el.style.setProperty('--c', C[(Math.random() * C.length) | 0]);
      el.style.setProperty('--o', r(.45, .8).toFixed(2));
      el.style.setProperty('--sp', r(1.6, 4).toFixed(1) + 's');
      if (first) { el.style.setProperty('--d', r(5.5, 10).toFixed(1) + 's'); el.style.setProperty('--dl', (-r(0, 10)).toFixed(1) + 's'); }
      el.className = 'mt' + (Math.random() < .3 ? ' dots' : '');
      var svg = el.querySelector('svg');
      svg.innerHTML = SHAPES[(Math.random() * SHAPES.length) | 0];
    }
    for (var k = 0; k < n; k++) {
      var el = document.createElement('i'), svg = document.createElementNS(ns, 'svg');
      svg.setAttribute('viewBox', '5 5 38 38');
      el.appendChild(document.createElement('b')); el.appendChild(svg);
      place(el, true);
      el.addEventListener('animationiteration', function (e) { if (e.animationName === 'fall') place(e.currentTarget, false); });
      sky.appendChild(el);
    }
  })();


  /* ---------- 1b. story hero: scroll drives the scene (--p 0→1) and which step is showing ---------- */
  (function () {
    var st = document.getElementById('top'); if (!st || !st.classList.contains('story')) return;
    var steps = $$('.st', st), cur = 0, ticking = false, cuts = [.18, .43, .68];
    function upd() {
      ticking = false;
      var r = st.getBoundingClientRect(); if (r.bottom < 0 || r.top > innerHeight) return;
      var p = clamp(-r.top / Math.max(1, st.offsetHeight - innerHeight), 0, 1);
      st.style.setProperty('--p', p.toFixed(4));
      var k = p < cuts[0] ? 0 : p < cuts[1] ? 1 : p < cuts[2] ? 2 : 3;
      if (k !== cur) { cur = k; steps.forEach(function (s, i) { s.classList.toggle('on', i === k); s.classList.toggle('past', i < k); }); }
    }
    addEventListener('scroll', function () { if (!ticking) { ticking = true; raf(upd); } }, { passive: true });
    addEventListener('resize', upd, { passive: true });
    upd();
  })();

  /* ---------- 2. countdown (+ status) ---------- */
  var OPEN = new Date(CFG.regOpen), CLOSE = new Date(CFG.regClose), lastPhase = '';
  var pad = function (n) { return (n < 10 ? '0' : '') + n; };
  var boxes = $$('[data-cd]').map(function (el) {
    return ['d', 'h', 'm', 's'].map(function (u) { return $('[data-u=' + u + ']', el); });
  });
  function applyPhase(p) {                 // the page shows the deadline in ONE place only
    $('#cdLabel').textContent = p === 'pre' ? 'เปิดรับสมัครใน' : 'ปิดรับสมัครใน';
    $$('[data-cd-wrap]').forEach(function (w) { w.hidden = p === 'closed'; });
  }
  function tick() {
    var now = new Date(), p = now < OPEN ? 'pre' : (now <= CLOSE ? 'open' : 'closed');
    if (p !== lastPhase) { applyPhase(p); lastPhase = p; }
    if (p === 'closed') return;
    var s = Math.max(0, Math.floor(((p === 'pre' ? OPEN : CLOSE) - now) / 1000));
    var v = [Math.floor(s / 86400), pad(Math.floor(s % 86400 / 3600)), pad(Math.floor(s % 3600 / 60)), pad(s % 60)];
    boxes.forEach(function (b) {
      b.forEach(function (el, k) {
        var t = String(v[k]);
        if (el.textContent === t) return;
        el.textContent = t;
        if (canAnimate && !reduced && lastPhase) el.animate(
          [{ transform: 'translate3d(0,-60%,0)', opacity: 0 }, { transform: 'none', opacity: 1 }],
          { duration: 320, easing: 'cubic-bezier(.2,1.2,.4,1)' });
      });
    });
  }
  tick();
  var cdTimer = setInterval(tick, 1000);
  document.addEventListener('visibilitychange', function () {
    clearInterval(cdTimer);
    if (!document.hidden) { tick(); cdTimer = setInterval(tick, 1000); }
  });

  /* ---------- 3. timeline road: status per stop, draw the road up to "now" ---------- */
  (function () {
    var road = $('#road'), stops = $$('.stop', road), now = new Date(), cur = -1, nextSet = false;
    stops.forEach(function (li, i) {
      var st = new Date(li.dataset.start + 'T00:00:00+07:00'), en = new Date(li.dataset.end + 'T23:59:59+07:00');
      var bd = $('.bd', li);
      if (now > en) { li.classList.add('done'); cur = i; }
      else if (now >= st) { li.classList.add('now'); bd.textContent = 'ตอนนี้'; cur = i; }
      else if (!nextSet) { li.classList.add('next'); bd.textContent = 'ถัดไป'; nextSet = true; }
    });
    // stops sit at 0, 1/3, 2/3, 1 of the road; draw a little past the current one
    var frac = cur < 0 ? 0 : Math.min(1, (cur + (stops[cur].classList.contains('now') ? .35 : 1)) / (stops.length - 1));
    // the road SVG stretches (preserveAspectRatio="none", non-scaling stroke), so dashes are in screen px:
    // measure the on-screen length of the visible path and draw that fraction of it
    function screenLen(p) {
      var m = p.getScreenCTM(); if (!m) return 0;
      var L = p.getTotalLength(), n = 80, len = 0, prev = null;
      for (var k = 0; k <= n; k++) {
        var q = p.getPointAtLength(L * k / n), x = m.a * q.x + m.c * q.y, y = m.b * q.x + m.d * q.y;
        if (prev) len += Math.hypot(x - prev[0], y - prev[1]);
        prev = [x, y];
      }
      return len;
    }
    var shown = false;
    function layout(animate) {
      $$('.prog', road).forEach(function (p) {
        if (!p.getBoundingClientRect().width) return;            // hidden layout (mobile vs desktop path)
        var len = Math.ceil(screenLen(p)) + 2;
        p.style.transition = animate ? '' : 'none';
        p.style.strokeDasharray = len + ' ' + len;
        p.style.strokeDashoffset = String(shown && animate ? len * (1 - frac) : (shown ? len * (1 - frac) : len));
        p.style.opacity = '1';
      });
    }
    layout(false);
    var io = new IntersectionObserver(function (es) {
      if (!es[0].isIntersecting) return;
      io.disconnect();
      road.classList.add('in');
      raf(function () { shown = true; layout(true); });
    }, { threshold: .2 });
    var rt; addEventListener('resize', function () { clearTimeout(rt); rt = setTimeout(function () { layout(false); }, 150); }, { passive: true });
    io.observe(road);
    new IntersectionObserver(function (es) { road.classList.toggle('paused', !es[0].isIntersecting); }).observe(road);
  })();

  /* ---------- 4a. header swap + scroll-spy ---------- */
  var hdr = $('#hdr'), chips = $('#chips');
  var spyLinks = $$('[data-spy]');
  new IntersectionObserver(function (es) {
    state.heroVisible = es[0].isIntersecting;
    hdr.classList.toggle('scrolled', !state.heroVisible);
    $('#top').classList.toggle('hero-paused', !state.heroVisible);
  }, { rootMargin: '-35% 0px 0px 0px' }).observe($('#top'));

  var current = '';
  var spy = new IntersectionObserver(function (es) {
    es.forEach(function (e) {
      if (!e.isIntersecting || e.target.id === current) return;
      current = e.target.id;
      spyLinks.forEach(function (a) { a.setAttribute('aria-current', a.dataset.spy === current ? 'true' : 'false'); });
      var chip = $('.chip[data-spy="' + current + '"]', chips);
      if (chip && chips.scrollWidth > chips.clientWidth) {
        chips.scrollTo({ left: chip.offsetLeft - chips.clientWidth / 2 + chip.offsetWidth / 2, behavior: reduced ? 'auto' : 'smooth' });
      }
    });
  }, { rootMargin: '-45% 0px -50% 0px' });
  ['tracks', 'perks', 'journey', 'faq'].forEach(function (id) { var s = document.getElementById(id); if (s) spy.observe(s); });

  /* ---------- 4b. reveal fallback + pause loops off-screen ---------- */
  if (!sda) {
    var rio = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); rio.unobserve(e.target); } });
    }, { rootMargin: '0px 0px -6% 0px', threshold: .1 });
    $$('.reveal').forEach(function (el) { rio.observe(el); });
  }

  /* ---------- 4c. mobile bottom bar ---------- */
  var bbar = $('#bbar'), heroCtaVisible = true, endVisible = new Set();
  function syncBar() { bbar.classList.toggle('show', !heroCtaVisible && endVisible.size === 0 && !state.sheetOpen); }
  new IntersectionObserver(function (es) { heroCtaVisible = es[0].isIntersecting; syncBar(); }).observe($('#heroCta') || $('#top'));
  var endIO = new IntersectionObserver(function (es) {
    es.forEach(function (e) { if (e.isIntersecting) endVisible.add(e.target); else endVisible.delete(e.target); });
    syncBar();
  });
  endIO.observe($('#register')); endIO.observe($('.ftr'));


  /* ---------- 5. tracks: product-style showcase ----------
     One big live 3D model floats on a glowing backdrop in the track's colour.
     Arrows / thumbnails / swipe / ←→ switch track; tap the model to open details. */
  (function () {
    var cs = $('#cs'); if (!cs) return;
    var host = $('#csHost'), model = $('#csModel'), info = $('#cfInfo'), go = $('#cfGo'), big = $('#csBig');
    var thumbs = $$('.cs-thumb', cs), cur = 0, busy = false, swapT;
    var TAB = ['เกม', 'แอป / เว็บ', 'IoT & นวัตกรรม'], BIG = ['GAME DEV', 'SOFTWARE', 'IOT'], IC = ['game', 'app', 'bulb'];
    var snaps = null;

    function fill(i) {
      var t = TRACKS[i];
      $('#cfName').textContent = t.name;
      $('#cfDesc').textContent = t.desc;
      $('#cfPill').textContent = '“' + t.motto + '”';
      big.textContent = BIG[i];
      model.setAttribute('aria-label', 'ดูรายละเอียดสาย ' + t.name);
      $('.ph use', host).setAttribute('href', '#i-' + IC[i]);
      var img = $('.cs-snap', host);
      if (snaps && snaps[i]) { img.src = snaps[i]; img.hidden = false; }
    }
    function mount() { if (!cs.hidden && window.AFO3D && AFO3D.ring) AFO3D.ring(cur, host); }
    function paint(i) {
      cs.style.setProperty('--c', TRACKS[i].c); cs.style.setProperty('--c2', TRACKS[i].c2);
      go.dataset.track = String(i);
      thumbs.forEach(function (b, k) { b.classList.toggle('on', k === i); b.setAttribute('aria-pressed', k === i ? 'true' : 'false'); });
    }

    /* step 1: all 3 models together (.trio) — tap one to open its big showcase */
    var trioWrap = $('#trioWrap'), back = $('#csBack'), picks = $$('.trio-hit button');
    function openCase(i) {
      cur = i; paint(i); fill(i);
      trioWrap.hidden = true; cs.hidden = false;
      mount();
      var hdr = parseFloat(getComputedStyle(root).scrollPaddingTop) || 68, r = cs.getBoundingClientRect();
      if (Math.abs(r.top - hdr) > 24) scrollTo({ top: scrollY + r.top - hdr, behavior: reduced ? 'auto' : 'smooth' });
      if (reduced || !canAnimate) return;
      host.animate([{ transform: 'translate3d(0,8%,0) scale(.55)', opacity: 0 }, { transform: 'none', opacity: 1 }], { duration: 640, easing: 'cubic-bezier(.2,1.2,.35,1)', fill: 'backwards' });
      big.animate([{ opacity: 0, transform: 'scale(.8)' }, { opacity: 1, transform: 'none' }], { duration: 520, easing: 'cubic-bezier(.16,1,.3,1)', fill: 'backwards' });
      info.animate([{ opacity: 0, transform: 'translate3d(0,18px,0)' }, { opacity: 1, transform: 'none' }], { duration: 480, delay: 120, easing: 'cubic-bezier(.16,1,.3,1)', fill: 'backwards' });
      $('.cs-thumbs', cs).animate([{ opacity: 0 }, { opacity: 1 }], { duration: 400, delay: 220, fill: 'backwards' });
    }
    function closeCase() {
      cs.hidden = true; trioWrap.hidden = false;
      var r = trioWrap.getBoundingClientRect();
      if (r.top < 0) $('#tracks').scrollIntoView({ behavior: reduced ? 'auto' : 'smooth' });
      if (!reduced && canAnimate) trioWrap.animate([{ opacity: 0, transform: 'scale(.94)' }, { opacity: 1, transform: 'none' }], { duration: 420, easing: 'cubic-bezier(.16,1,.3,1)' });
      if (picks[cur]) picks[cur].focus({ preventScroll: true });
    }
    picks.forEach(function (b) {
      b.addEventListener('click', function () { openCase(+b.dataset.i); });
      b.addEventListener('pointerenter', function () { if (window.AFO3D && AFO3D.trioHot) AFO3D.trioHot(+b.dataset.i); });
      b.addEventListener('pointerleave', function () { if (window.AFO3D && AFO3D.trioHot) AFO3D.trioHot(-1); });
    });
    back.addEventListener('click', closeCase);

    function select(i, dir) {
      i = (i + TRACKS.length) % TRACKS.length;
      if (i === cur || busy) return;
      dir = dir || (i > cur ? 1 : -1);
      cur = i; paint(i);
      if (reduced || !canAnimate) { fill(i); mount(); return; }
      busy = true;
      info.classList.add('swap'); clearTimeout(swapT);
      swapT = setTimeout(function () { info.classList.remove('swap'); }, 200);
      big.animate([{ opacity: 1, transform: 'none' }, { opacity: 0, transform: 'translate3d(' + -dir * 60 + 'px,0,0)' }], { duration: 200, fill: 'forwards' });
      var out = host.animate([
        { transform: 'none', opacity: 1 },
        { transform: 'translate3d(' + -dir * 28 + '%,4%,0) rotateY(' + -dir * 50 + 'deg) scale(.6)', opacity: 0 }
      ], { duration: 260, easing: 'cubic-bezier(.5,0,.9,.5)', fill: 'forwards' });
      out.onfinish = function () {
        fill(i); mount();
        out.cancel();
        host.animate([
          { transform: 'translate3d(' + dir * 30 + '%,-6%,0) rotateY(' + dir * 60 + 'deg) scale(.6)', opacity: 0 },
          { transform: 'none', opacity: 1 }
        ], { duration: 620, easing: 'cubic-bezier(.2,1.2,.35,1)', fill: 'backwards' });
        big.animate([{ opacity: 0, transform: 'translate3d(' + dir * 60 + 'px,0,0)' }, { opacity: 1, transform: 'none' }], { duration: 500, easing: 'cubic-bezier(.16,1,.3,1)', fill: 'forwards' })
          .onfinish = function () { busy = false; };
        setTimeout(function () { busy = false; }, 700);
      };
    }

    $$('.cs-arrow', cs).forEach(function (b) { b.addEventListener('click', function () { select(cur + +b.dataset.dir, +b.dataset.dir); }); });
    thumbs.forEach(function (b, k) { b.addEventListener('click', function () { select(k); }); });

    // swipe (horizontal only; vertical keeps scrolling the page)
    var sx = 0, sy = 0, swiping = false, swiped = false;
    cs.addEventListener('pointerdown', function (e) { sx = e.clientX; sy = e.clientY; swiping = true; swiped = false; });
    cs.addEventListener('pointermove', function (e) {
      if (!swiping) return;
      var dx = e.clientX - sx;
      if (Math.abs(e.clientY - sy) > Math.abs(dx) + 6) { swiping = false; return; }
      if (Math.abs(dx) > 50) { swiping = false; swiped = true; select(cur + (dx < 0 ? 1 : -1), dx < 0 ? 1 : -1); }
    });
    cs.addEventListener('pointerup', function () { swiping = false; });
    cs.addEventListener('pointercancel', function () { swiping = false; });
    cs.addEventListener('dragstart', function (e) { e.preventDefault(); });

    model.addEventListener('click', function () { if (swiped) { swiped = false; return; } openSheet(cur, true, host); });
    go.addEventListener('click', function () { openSheet(cur, true, host); });
    cs.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') { e.preventDefault(); select(cur + (e.key === 'ArrowRight' ? 1 : -1)); }
    });

    addEventListener('afo3d:snaps', function (e) {
      snaps = e.detail;
      thumbs.forEach(function (b, k) { var img = $('img', b); if (snaps[k]) { img.src = snaps[k]; img.hidden = false; } });
      picks.forEach(function (b, k) { var img = $('img', b); if (snaps[k]) { img.src = snaps[k]; img.hidden = false; } });
      var img = $('.cs-snap', host); if (snaps[cur]) { img.src = snaps[cur]; img.hidden = false; host.classList.add('snap'); }
    });
    addEventListener('afo3d:ready', mount);
  })();

  /* ---------- 7. detail sheet ---------- */
  var sheet = $('#sheet'), panel = $('#sheetPanel'), backdrop = $('.sheet-backdrop', sheet);
  var scroller = $('#sheetScroll'), content = $('#sheetContent'), tabsEl = $('#sheetTabs');
  var hasDialog = typeof sheet.showModal === 'function';
  var cur = 0, closing = false, switching = false, pushed = false, skipPop = false, lastFocus = null, benefitIO = null;

  tabsEl.innerHTML = TRACKS.map(function (t, i) {
    return '<button class="tab" role="tab" type="button" data-i="' + i + '" style="--tc:' + t.c + '" aria-selected="false">' + t.tab + '</button>';
  }).join('');

  var tpls = [];
  function tpl(i) {                        // pre-built while idle so a tap only clones nodes
    if (tpls[i]) return tpls[i];
    var t = TRACKS[i], el = document.createElement('template');
    var esc = function (s) { return s.replace(/&/g, '&amp;'); };
    var orbs = [['#8ff0c2', '#12a36b'], ['#ffb27a', '#e2601a'], ['#9fc8ff', '#2d6ce0']][i];
    var orb = function (ic, a, b) { return '<span class="orb" style="--a:' + (a || orbs[0]) + ';--b:' + (b || orbs[1]) + '">' + icon(ic) + '</span>'; };
    var star = function (x, y, s, c, face, dl) {
      return '<i style="--x:' + x + ';--y:' + y + ';--s:' + s + 'px;--dl:' + dl + 's;color:' + c + '"><svg viewBox="0 0 ' + (face ? 48 : 40) + ' ' + (face ? 48 : 40) + '"><use href="#' + (face ? 'starface' : 'star4') + '"/></svg></i>';
    };
    var gets = [
      ['folder', 'ผลงานจริง 1 ชิ้น', t.output.replace(' 1 ชิ้น', '').replace(' 1 เกม', '')],
      ['chat', 'เมนเทอร์ช่วยดูงาน', '26 ต.ค. – 12 พ.ย.'],
      ['spark', 'ใช้ AI ช่วยคิด', 'ไปได้ไกลกว่าเดิม'],
      ['users', 'ทีม 2–3 คน', 'ฝึกทำงานเป็นทีม']
    ];
    var SHORT = ['GAME DEV', 'SOFTWARE', 'IOT'];
    var row = function (no, h, body, note) {
      return '<section class="dl-row"><h3 class="dl-h">' + h + (note ? '<small>' + note + '</small>' : '') + '</h3><div class="dl-body">' + body + '</div></section>';
    };
    el.innerHTML =
      '<div class="sh-hero">' +
        '<div class="dl-top" data-pop><span>' + t.th + '</span></div>' +
        '<div class="dl-grid">' +
          '<div class="dl-copy">' +
            '<h2 id="shTitle" class="dl-title" data-pop>' + SHORT[i] + '<i>.</i></h2>' +
            '<p class="dl-name" data-pop>' + esc(t.name) + '</p>' +
            '<p class="sh-desc" data-pop>' + t.desc + '</p>' +
            '<span class="dl-out" data-pop>' + icon('folder') + 'ผลลัพธ์: ' + t.output + '</span>' +
          '</div>' +
          '<div class="sh-img"><span class="ph" aria-hidden="true">' + icon(t.icon) + '</span></div>' +
        '</div>' +
      '</div>' +
      '<div class="dl-rows">' +
        row('01', 'เหมาะกับใคร', '<ul class="fitbox"><li data-b>' + icon('check') + '<span>' + t.fit + '</span></li><li data-b>' + icon('check') + '<span>ยังไม่มีผลงานก็สมัครได้ เริ่มจากศูนย์พร้อมเมนเทอร์</span></li></ul>') +
        row('02', 'ไอเดียตัวอย่าง', '<div class="ideas">' + t.ideas.map(function (x) { return '<div class="idea" data-b>' + orb(x[0]) + '<b>' + x[1] + '</b></div>'; }).join('') + '</div>', 'โจทย์จริงประกาศ 22 ต.ค.') +
        row('03', 'ได้อะไรกลับไป', '<div class="gets">' + gets.map(function (g) { return '<div class="get" data-b>' + orb(g[0]) + '<div><b>' + g[1] + '</b><span>' + g[2] + '</span></div></div>'; }).join('') + '</div>' +
          '<div class="prize" data-b data-prize>' + orb('trophy', '#ffe9a3', '#e39a20') + '<div><b>' + AFO.PRIZE.title + '</b><span>' + AFO.PRIZE.text + '</span><small>' + AFO.PRIZE.note + '</small></div></div>') +
        row('04', 'เส้นทางของสายนี้', '<ol class="steps">' + AFO.ROUTE.map(function (r, k) { return '<li class="step" data-b><i>' + (k + 1) + '</i><b>' + r.d + '</b><span>' + r.t + '</span></li>'; }).join('') + '</ol>') +
      '</div>' +
      '<p class="dl-punch" data-b>“' + t.motto + '”<i>.</i></p>';
    return (tpls[i] = el);
  }
  (window.requestIdleCallback || function (f) { setTimeout(f, 1200); })(function () { TRACKS.forEach(function (_, i) { tpl(i); }); });

  function render(i) {
    var t = TRACKS[i];
    content.style.setProperty('--c', t.c); content.style.setProperty('--c2', t.c2);
    $$('.tab', tabsEl).forEach(function (b, k) { b.setAttribute('aria-selected', k === i ? 'true' : 'false'); });
    content.textContent = '';
    content.appendChild(tpl(i).content.cloneNode(true));
  }

  function popIn(el, delay) {
    el.style.opacity = '';
    if (!canAnimate) return;
    if (reduced) { el.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 220, delay: delay, fill: 'backwards' }); return; }
    var prize = el.hasAttribute('data-prize');
    el.animate([
      { opacity: 0, transform: prize ? 'perspective(800px) translate3d(0,30px,-120px) rotateY(-80deg) scale(.8)' : 'perspective(700px) translate3d(0,26px,-60px) rotateX(-72deg)' },
      { opacity: 1, transform: 'none' }
    ], { duration: prize ? 820 : 640, delay: delay, easing: 'cubic-bezier(.2,1.25,.35,1)', fill: 'backwards' });
  }
  function watchBenefits(base) {
    if (benefitIO) benefitIO.disconnect();
    var items = $$('[data-b]', content), batchAt = 0, k = 0;
    items.forEach(function (el) { el.style.opacity = 0; });
    benefitIO = new IntersectionObserver(function (es) {
      var now = performance.now();
      if (now - batchAt > 150) k = 0;
      batchAt = now;
      es.forEach(function (e) {
        if (!e.isIntersecting) return;
        popIn(e.target, base + k * 85); k++; benefitIO.unobserve(e.target);
      });
      base = 0;
    }, { root: scroller, threshold: .12 });
    items.forEach(function (el) { benefitIO.observe(el); });
  }
  function introHero(delay) {
    if (!canAnimate || reduced) return;
    $('.sh-img', content).animate([
      { transform: 'perspective(700px) rotateY(-70deg) rotateX(20deg) scale(.6)', opacity: 0 },
      { transform: 'perspective(700px) rotateY(8deg) scale(1.04)', opacity: 1, offset: .7 },
      { transform: 'none', opacity: 1 }
    ], { duration: 820, delay: delay, easing: 'cubic-bezier(.2,.9,.25,1)', fill: 'backwards' });
    $$('[data-pop]', content).forEach(function (el, k) {
      el.animate([{ opacity: 0, transform: 'translate3d(0,14px,0)' }, { opacity: 1, transform: 'none' }],
        { duration: 480, delay: delay + 120 + k * 55, easing: 'cubic-bezier(.16,1,.3,1)', fill: 'backwards' });
    });
  }

  function lockPage(on) {                   // inline style: avoids restyling the whole page
    root.style.overflow = on ? 'hidden' : '';
    document.body.style.overflow = on ? 'hidden' : '';
  }

  function openSheet(i, push, fromEl) {
    if (state.sheetOpen) { if (i !== cur) switchTrack(i, i > cur ? 1 : -1); return; }
    if (closing) return;
    cur = i; render(i);
    lastFocus = document.activeElement;
    scroller.scrollTop = 0;
    if (hasDialog) sheet.showModal(); else sheet.setAttribute('open', '');
    state.sheetOpen = true; lockPage(true); syncBar();
    if (canAnimate) {
      backdrop.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 320, easing: 'ease-out', fill: 'backwards' });
      var from = !reduced && fromEl && fromEl.getBoundingClientRect(), to = panel.getBoundingClientRect();
      if (from && from.width && to.width) {                // grow out of the tapped card
        panel.style.transformOrigin = '0 0';
        panel.animate([
          { transform: 'translate3d(' + (from.left - to.left) + 'px,' + (from.top - to.top) + 'px,0) scale(' + from.width / to.width + ',' + from.height / to.height + ')', borderRadius: '40px', opacity: .35 },
          { opacity: 1, offset: .35 },
          { transform: 'none', borderRadius: getComputedStyle(panel).borderRadius, opacity: 1 }
        ], { duration: 640, easing: 'cubic-bezier(.16,1,.3,1)', fill: 'backwards' }).onfinish = function () { panel.style.transformOrigin = ''; };
      } else panel.animate(reduced ? [{ opacity: 0 }, { opacity: 1 }] : [
        { transform: 'perspective(1100px) translate3d(0,62%,-140px) rotateX(34deg) scale(.9)', opacity: 0 },
        { opacity: 1, offset: .45 },
        { transform: 'perspective(1100px) translate3d(0,0,0) rotateX(0) scale(1)', opacity: 1 }
      ], { duration: reduced ? 200 : 620, easing: 'cubic-bezier(.16,1,.3,1)', fill: 'backwards' });
    }
    introHero(170);
    watchBenefits(430);
    if (window.AFO3D) AFO3D.sheet(i, $('.sh-img', content));
    if (push !== false) { history.pushState({ afo: TRACKS[i].id }, '', '#track-' + TRACKS[i].id); pushed = true; }
  }

  function switchTrack(i, dir) {
    if (switching || i === cur) return;
    switching = true;
    function done() {
      cur = i; render(i); scroller.scrollTop = 0;
      if (canAnimate && !reduced) content.animate([
        { opacity: 0, transform: 'perspective(900px) translate3d(' + dir * 34 + '%,0,-140px) rotateY(' + dir * 60 + 'deg)' },
        { opacity: 1, transform: 'none' }
      ], { duration: 480, easing: 'cubic-bezier(.16,1,.3,1)', fill: 'backwards' });
      introHero(90); watchBenefits(240);
      if (window.AFO3D) AFO3D.sheet(i, $('.sh-img', content));
      history.replaceState(history.state, '', '#track-' + TRACKS[i].id);
      switching = false;
    }
    if (!canAnimate || reduced) return done();
    var out = content.animate([
      { opacity: 1, transform: 'none' },
      { opacity: 0, transform: 'perspective(900px) translate3d(' + -dir * 34 + '%,0,-140px) rotateY(' + -dir * 60 + 'deg)' }
    ], { duration: 240, easing: 'cubic-bezier(.5,0,.9,.5)', fill: 'forwards' });
    out.onfinish = function () { out.cancel(); done(); };
  }

  function finishClose() {
    if (hasDialog && sheet.open) sheet.close(); else sheet.removeAttribute('open');
    if (panel.getAnimations) panel.getAnimations().forEach(function (a) { a.cancel(); });
    if (backdrop.getAnimations) backdrop.getAnimations().forEach(function (a) { a.cancel(); });
    panel.style.transform = ''; backdrop.style.opacity = '';
    if (benefitIO) benefitIO.disconnect();
    if (window.AFO3D) AFO3D.sheetStop();
    state.sheetOpen = false; closing = false; lockPage(false); syncBar();
    if (pushed) { pushed = false; skipPop = true; history.back(); }          // drop our history entry
    else if (/^#track-/.test(location.hash)) history.replaceState(null, '', location.pathname + location.search);
    if (lastFocus && lastFocus.focus) lastFocus.focus({ preventScroll: true });
  }
  function closeSheet(fromY, fromPop) {
    if (!state.sheetOpen || closing) return;
    closing = true;
    if (fromPop) pushed = false;
    if (!canAnimate) return finishClose();
    var y = fromY || 0;
    var a = panel.animate([
      { transform: 'translate3d(0,' + y + 'px,0)', opacity: 1 },
      { transform: reduced ? 'translate3d(0,' + y + 'px,0)' : 'perspective(1100px) translate3d(0,100%,-60px) rotateX(16deg)', opacity: reduced ? 0 : .7 }
    ], { duration: reduced ? 160 : 340, easing: 'cubic-bezier(.5,0,.85,.45)', fill: 'forwards' });
    backdrop.animate([{ opacity: backdrop.style.opacity || 1 }, { opacity: 0 }], { duration: 340, fill: 'forwards' });
    a.onfinish = finishClose;
  }

  // Esc and Android back (Chrome routes the back gesture to an open modal <dialog>)
  sheet.addEventListener('cancel', function (e) { e.preventDefault(); closeSheet(); });
  sheet.addEventListener('close', function () { if (state.sheetOpen && !closing) { closing = true; finishClose(); } });
  addEventListener('popstate', function () {
    if (skipPop) { skipPop = false; return; }
    var m = location.hash.match(/^#track-(\w+)/);
    var idx = m ? TRACKS.map(function (t) { return t.id; }).indexOf(m[1]) : -1;
    if (state.sheetOpen && idx < 0) closeSheet(0, true);
    else if (!state.sheetOpen && idx >= 0) openSheet(idx, false);
  });

  $$('[data-track]:not(#cfGo)').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var i = +btn.dataset.track;
      openSheet(i);
    });
  });
  sheet.addEventListener('click', function (e) { if (e.target.closest('[data-close]')) closeSheet(); });
  tabsEl.addEventListener('click', function (e) {
    var b = e.target.closest('.tab'); if (!b) return;
    var i = +b.dataset.i; switchTrack(i, i > cur ? 1 : -1);
  });
  $('#sheetNext').addEventListener('click', function () { switchTrack((cur + 1) % TRACKS.length, 1); });

  // swipe the handle down to close
  (function () {
    var grab = $('#sheetGrab'), startY = 0, dy = 0, lastY = 0, lastT = 0, v = 0, active = false;
    grab.addEventListener('pointerdown', function (e) {
      if (closing) return;
      active = true; startY = lastY = e.clientY; lastT = e.timeStamp; dy = 0; v = 0;
      grab.setPointerCapture(e.pointerId);
      if (panel.getAnimations) panel.getAnimations().forEach(function (a) { a.finish(); });
    });
    grab.addEventListener('pointermove', function (e) {
      if (!active) return;
      dy = Math.max(0, e.clientY - startY);
      v = (e.clientY - lastY) / ((e.timeStamp - lastT) || 16); lastY = e.clientY; lastT = e.timeStamp;
      panel.style.transform = 'translate3d(0,' + dy + 'px,0)';
      backdrop.style.opacity = String(1 - Math.min(dy / 700, .6));
    });
    function end() {
      if (!active) return; active = false;
      if (dy > 110 || v > .7) return closeSheet(dy);
      panel.style.transform = ''; backdrop.style.opacity = '';
      if (canAnimate && dy > 0) panel.animate([{ transform: 'translate3d(0,' + dy + 'px,0)' }, { transform: 'translate3d(0,0,0)' }], { duration: 280, easing: 'cubic-bezier(.2,.9,.3,1)' });
    }
    grab.addEventListener('pointerup', end); grab.addEventListener('pointercancel', end);
  })();

  // deep link: /#track-game opens that track
  (function () {
    var m = location.hash.match(/^#track-(\w+)/);
    var idx = m ? TRACKS.map(function (t) { return t.id; }).indexOf(m[1]) : -1;
    if (idx >= 0) openSheet(idx, false);
  })();


  /* ---------- 8. adaptive quality ---------- */

  /* ---------- 9. posters: arrows + mouse drag on desktop, tap opens an in-page viewer ---------- */
  (function () {
    var list = $('#posterList'), lb = $('#lb'); if (!list || !lb) return;
    var img = $('#lbImg'), cap = $('#lbCap'), count = $('#lbCount'), idx = 0, lbPushed = false, skipLbPop = false;
    function items() { return $$('.poster', list); }
    function step() { var p = items()[0]; return p ? p.getBoundingClientRect().width + 12 : 300; }
    $$('[data-ps]').forEach(function (b) {
      b.addEventListener('click', function () { list.scrollBy({ left: +b.dataset.ps * step() * (innerWidth >= 900 ? 2 : 1), behavior: reduced ? 'auto' : 'smooth' }); });
    });
    function edges() {
      var max = list.scrollWidth - list.clientWidth - 2;
      list.classList.toggle('at-start', list.scrollLeft <= 2);
      list.classList.toggle('at-end', list.scrollLeft >= max);
      $$('[data-ps]').forEach(function (b) { b.disabled = +b.dataset.ps < 0 ? list.scrollLeft <= 2 : list.scrollLeft >= max; });
    }
    list.addEventListener('scroll', function () { raf(edges); }, { passive: true });
    addEventListener('resize', edges, { passive: true }); addEventListener('load', edges); edges();

    // mouse drag (touch already scrolls natively)
    var down = false, moved = 0, sx = 0, sl = 0;
    list.addEventListener('pointerdown', function (e) {
      if (e.pointerType !== 'mouse' || e.button) return;
      down = true; moved = 0; sx = e.clientX; sl = list.scrollLeft;
    });
    addEventListener('pointermove', function (e) {
      if (!down) return;
      var dx = e.clientX - sx; moved = Math.max(moved, Math.abs(dx));
      if (moved > 5) { list.classList.add('dragging'); list.scrollLeft = sl - dx; }
    });
    addEventListener('pointerup', function () { if (!down) return; down = false; list.classList.remove('dragging'); });
    list.addEventListener('dragstart', function (e) { e.preventDefault(); });

    function show(i, dir) {
      var ps = items(); if (!ps.length) return;
      idx = (i + ps.length) % ps.length;
      var a = $('a', ps[idx]), f = $('figcaption', ps[idx]);
      img.src = a.getAttribute('href'); img.alt = $('img', ps[idx]).alt;
      cap.textContent = f ? f.textContent : ''; count.textContent = (idx + 1) + ' / ' + ps.length;
      if (dir && canAnimate && !reduced) img.animate([{ opacity: 0, transform: 'translate3d(' + dir * 40 + 'px,0,0) scale(.97)' }, { opacity: 1, transform: 'none' }], { duration: 320, easing: 'cubic-bezier(.16,1,.3,1)' });
    }
    function openLb(i, from) {
      show(i);
      if (typeof lb.showModal === 'function') lb.showModal(); else lb.setAttribute('open', '');
      lockPage(true);
      if (canAnimate && !reduced) {
        var r = from && from.getBoundingClientRect(), t = img.getBoundingClientRect();
        $('.lb-bg', lb).animate([{ opacity: 0 }, { opacity: 1 }], { duration: 260 });
        img.animate(r && t.width ? [
          { transform: 'translate3d(' + (r.left + r.width / 2 - t.left - t.width / 2) + 'px,' + (r.top + r.height / 2 - t.top - t.height / 2) + 'px,0) scale(' + r.width / t.width + ')' },
          { transform: 'none' }] : [{ opacity: 0, transform: 'scale(.9)' }, { opacity: 1, transform: 'none' }],
          { duration: 420, easing: 'cubic-bezier(.16,1,.3,1)' });
      }
      history.pushState({ lb: 1 }, '', '#poster'); lbPushed = true;
    }
    function closeLb(fromPop) {
      if (!lb.open) return;
      if (typeof lb.close === 'function') lb.close(); else lb.removeAttribute('open');
      lockPage(false);
      if (lbPushed && !fromPop) { skipLbPop = true; history.back(); }
      lbPushed = false;
      var a = $('a', items()[idx]); if (a) a.focus({ preventScroll: true });
    }
    list.addEventListener('click', function (e) {
      var a = e.target.closest('a[data-lb]'); if (!a) return;
      e.preventDefault();
      if (moved > 5) { moved = 0; return; }                 // it was a drag, not a tap
      openLb(items().indexOf(a.closest('.poster')), a);
    });
    lb.addEventListener('click', function (e) {
      if (e.target.closest('[data-lbx]')) closeLb();
      var d = e.target.closest('[data-lbd]'); if (d) show(idx + +d.dataset.lbd, +d.dataset.lbd);
    });
    lb.addEventListener('cancel', function (e) { e.preventDefault(); closeLb(); });
    lb.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') { e.preventDefault(); var d = e.key === 'ArrowRight' ? 1 : -1; show(idx + d, d); }
    });
    var tx = 0, ty = 0;
    lb.addEventListener('touchstart', function (e) { tx = e.touches[0].clientX; ty = e.touches[0].clientY; }, { passive: true });
    lb.addEventListener('touchend', function (e) {
      var dx = e.changedTouches[0].clientX - tx, dy = e.changedTouches[0].clientY - ty;
      if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy)) show(idx + (dx < 0 ? 1 : -1), dx < 0 ? 1 : -1);
      else if (dy > 90 && Math.abs(dy) > Math.abs(dx)) closeLb();
    }, { passive: true });
    addEventListener('popstate', function () {
      if (skipLbPop) { skipLbPop = false; return; }
      if (lb.open && location.hash !== '#poster') closeLb(true);
    });
  })();

  // If the phone can't hold ~45fps while the idle animations run, drop to lite mode.
  if (!lite) setTimeout(function () {
    var dts = [], last = 0;
    (function sample(t) {
      if (document.hidden) return;
      if (last) dts.push(t - last); last = t;
      if (dts.length < 90) return raf(sample);
      dts.sort(function (a, b) { return a - b; });
      if (dts[45] > 22) { lite = true; root.classList.add('lite'); }
    })(performance.now());
  }, 1500);
})();
