/* ==========================================================
   Real-time 3D models (three.js)
   - hero: the 3 track models side by side on a glowing ring
   - each track card + the detail sheet: that track's model
   Models are built from simple shapes in code (no model files).
   Performance: lazy-loaded after first paint, renders only what is
   on screen, and picks its own quality from real frame times:
     0 full (DPR ≤ 2, 60fps) → 1 lite (DPR 1.25, ~30fps) → 2 still frame
   If WebGL or the CDN is unavailable, the CSS cubes / images stay.
   ========================================================== */
(function () {
  'use strict';
  var URL3 = (window.AFO && window.AFO.CFG && window.AFO.CFG.threeUrl) ||
    'https://cdn.jsdelivr.net/npm/three@0.169.0/build/three.module.min.js';
  var root = document.documentElement;
  var reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  var heroSlot = document.querySelector('.trio');

  function webgl() {
    try {
      var c = document.createElement('canvas'), g = c.getContext('webgl2') || c.getContext('webgl');
      var ext = g && g.getExtension('WEBGL_lose_context'); if (ext) ext.loseContext();   // don't keep a probe context alive
      return !!g;
    }
    catch (e) { return false; }
  }
  if (root.classList.contains('safe') || !webgl()) return;
  var IOS = root.classList.contains('ios'), MOBILE = IOS || matchMedia('(pointer: coarse)').matches;

  var pending = null;
  var api = window.AFO3D = {
    sheet: function (i, el) { pending = [i, el]; },
    sheetStop: function () { pending = null; }
  };

  // start loading once the first screen has painted
  function load() { import(URL3).then(init).catch(function () {}); }
  if (document.readyState === 'complete') setTimeout(load, 200);
  else addEventListener('load', function () { setTimeout(load, 200); });

  function init(THREE) {
    var lite = function () { return root.classList.contains('lite'); };
    var level = lite() ? 1 : 0;
    var running = false, skip = 0, t0 = performance.now(), prev = 0, gaps = [], stages = [], sheetStage = null, ready = false;
    var DPR = function () { return Math.min(window.devicePixelRatio || 1, level ? 1.25 : (MOBILE ? 1.5 : 2)); };

    /* ---------- modelling kit ---------- */
    var matCache = {};
    function M(color, o) {
      o = o || {};
      var k = color + '|' + JSON.stringify(o);
      if (matCache[k]) return matCache[k];
      return (matCache[k] = new THREE.MeshStandardMaterial({ color: color, roughness: o.r == null ? .42 : o.r, metalness: o.m || 0,
        emissive: o.e || 0x000000, emissiveIntensity: o.ei == null ? 1 : o.ei }));
    }
    function mesh(g, m, x, y, z) { var o = new THREE.Mesh(g, m); o.position.set(x || 0, y || 0, z || 0); return o; }
    var geoCache = {};
    function rbox(w, h, d, r) {
      var k = 'rb' + [w, h, d, r].join('|'); if (geoCache[k]) return geoCache[k];
      r = Math.min(r, w / 2 - .001, h / 2 - .001, d / 2 - .001);
      var s = new THREE.Shape(), x = -w / 2 + r, y = -h / 2 + r, W = w - 2 * r, H = h - 2 * r;
      s.moveTo(x, y - r); s.lineTo(x + W, y - r); s.quadraticCurveTo(x + W + r, y - r, x + W + r, y);
      s.lineTo(x + W + r, y + H); s.quadraticCurveTo(x + W + r, y + H + r, x + W, y + H + r);
      s.lineTo(x, y + H + r); s.quadraticCurveTo(x - r, y + H + r, x - r, y + H);
      s.lineTo(x - r, y); s.quadraticCurveTo(x - r, y - r, x, y - r);
      var g = new THREE.ExtrudeGeometry(s, { depth: Math.max(d - 2 * r, .001), bevelEnabled: true, bevelThickness: r, bevelSize: r * .92, bevelSegments: 4, curveSegments: 8 });
      g.translate(0, 0, -(d - 2 * r) / 2);
      g.computeVertexNormals();
      return (geoCache[k] = g);
    }
    function box(w, h, d) { var k = 'b' + [w, h, d].join('|'); return geoCache[k] || (geoCache[k] = new THREE.BoxGeometry(w, h, d)); }
    function cyl(r1, r2, h, n) { var k = 'c' + [r1, r2, h, n].join('|'); return geoCache[k] || (geoCache[k] = new THREE.CylinderGeometry(r1, r2, h, n || 28)); }
    function sph(r, n) { var k = 's' + r + '|' + n; return geoCache[k] || (geoCache[k] = new THREE.SphereGeometry(r, n || 20, Math.max(10, (n || 20) * .75 | 0))); }
    function tor(r, t, arc) { return new THREE.TorusGeometry(r, t, 10, 40, arc || Math.PI * 2); }

    var SH = (function () {
      var c = document.createElement('canvas'); c.width = c.height = 64;
      var x = c.getContext('2d'), g = x.createRadialGradient(32, 32, 0, 32, 32, 32);
      g.addColorStop(0, 'rgba(0,0,0,.6)'); g.addColorStop(1, 'rgba(0,0,0,0)');
      x.fillStyle = g; x.fillRect(0, 0, 64, 64);
      return new THREE.CanvasTexture(c);
    })();
    function blob(w, d, y) {
      var m = new THREE.Mesh(new THREE.PlaneGeometry(w, d), new THREE.MeshBasicMaterial({ map: SH, transparent: true, depthWrite: false }));
      m.rotation.x = -Math.PI / 2; m.position.y = y; m.userData.skip = true; return m;
    }
    function bulb(s) {
      var g = new THREE.Group();
      g.add(mesh(sph(.34, 24), M(0xffd23f, { e: 0xffb000, ei: .6, r: .25 }), 0, .2, 0));
      g.add(mesh(sph(.12, 12), M(0xfff6c4, { e: 0xffffff, ei: .8 }), -.1, .3, .22));
      [-.13, -.21].forEach(function (y) { g.add(mesh(cyl(.17, .17, .07), M(0xd7dde8, { m: .35, r: .3 }), 0, y, 0)); });
      g.add(mesh(cyl(.12, .06, .1), M(0x8a93a5, { m: .35 }), 0, -.29, 0));
      g.scale.setScalar(s || 1);
      return g;
    }
    function keys(cols, rows, w, d, gx, gz, color) {         // instanced keyboard keys
      var inst = new THREE.InstancedMesh(rbox(w, d, .05, .015), M(color, { r: .55 }), cols * rows);
      var m = new THREE.Matrix4(), q = new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(1, 0, 0), -Math.PI / 2), s = new THREE.Vector3(1, 1, 1), n = 0;
      for (var r = 0; r < rows; r++) for (var c = 0; c < cols; c++) {
        m.compose(new THREE.Vector3((c - (cols - 1) / 2) * gx, 0, (r - (rows - 1) / 2) * gz), q, s); inst.setMatrixAt(n++, m);
      }
      return inst;
    }

    /* ---------- the 3 models ---------- */
    function gameModel() {
      var G = new THREE.Group(), spin = [];
      var navy = M(0x2a3252, { r: .32 }), dark = M(0x151a2b, { r: .5 });
      var mon = new THREE.Group(); mon.position.set(.35, 1.25, -.8);
      mon.add(mesh(rbox(3.1, 2.05, .22, .1), M(0x232a43, { r: .35 })));
      mon.add(mesh(box(2.84, 1.8, .02), M(0x0e1220), 0, 0, .1));
      var scr = new THREE.Group(); scr.position.z = .115; mon.add(scr);
      scr.add(mesh(box(2.76, 1.72, .01), M(0x8fd3ff, { r: .6, e: 0x3a8fd0, ei: .28 })));
      [[2.76, .32, 0, -.7, 0x39c26a], [2.76, .12, 0, -.83, 0x9b6a3c],
       [.3, .3, -.95, -.39, 0xffb23f], [.3, .3, -.65, -.39, 0xff8a3d], [.3, .3, -.8, -.09, 0xffb23f],
       [.3, .6, .75, -.24, 0x4d9fff], [.3, .3, 1.05, -.39, 0x4d9fff], [.3, .9, 1.05, -.09, 0x3d7fe6],
       [.5, .15, -.55, .5, 0xffffff], [.3, .12, -.4, .6, 0xffffff], [.4, .12, .75, .62, 0xffffff],
       [.3, .3, .1, .35, 0xffd23f]].forEach(function (p) { scr.add(mesh(box(p[0], p[1], .03), M(p[4], { r: .7, e: p[4], ei: .12 }), p[2], p[3], .015)); });
      var hero = new THREE.Group(); hero.position.set(-.1, -.36, .04); scr.add(hero);           // pixel character that hops
      hero.add(mesh(box(.18, .16, .04), M(0xd9483b), 0, .12, 0)); hero.add(mesh(box(.14, .1, .04), M(0xffc9a0), 0, .24, 0));
      hero.add(mesh(box(.2, .05, .04), M(0xd9483b), 0, .31, 0));
      hero.add(mesh(box(.06, .08, .04), M(0x3d5bd9), -.05, .01, 0)); hero.add(mesh(box(.06, .08, .04), M(0x3d5bd9), .05, .01, 0));
      spin.push({ o: hero, hop: -.36 });
      mon.add(mesh(sph(.03, 8), M(0x4dff9a, { e: 0x4dff9a }), 1.3, -.92, .12));
      mon.add(mesh(cyl(.09, .11, .55), M(0x3a4260, { m: .3 }), 0, -1.3, -.06));
      mon.add(mesh(rbox(1.2, .1, .6, .045), M(0x232a43), 0, -1.56, 0));
      G.add(mon);
      var pad = new THREE.Group(); pad.position.set(-.25, .1, .85); pad.rotation.set(-.5, .25, -.08);
      pad.add(mesh(rbox(2.1, .95, .5, .22), navy));
      var gl = mesh(new THREE.CapsuleGeometry(.34, .55, 8, 20), navy, -.82, -.42, -.02); gl.rotation.z = .55; pad.add(gl);
      var gr = mesh(new THREE.CapsuleGeometry(.34, .55, 8, 20), navy, .82, -.42, -.02); gr.rotation.z = -.55; pad.add(gr);
      pad.add(mesh(rbox(.5, .14, .22, .06), dark, -.7, .5, -.05)); pad.add(mesh(rbox(.5, .14, .22, .06), dark, .7, .5, -.05));
      pad.add(mesh(rbox(1.5, .6, .06, .03), M(0x323b5e, { r: .3 }), 0, .02, .25));
      pad.add(mesh(box(.36, .11, .1), dark, -.62, .1, .29)); pad.add(mesh(box(.11, .36, .1), dark, -.62, .1, .29));
      [[.62, .3, 0xffd23f], [.84, .1, 0x2fd08b], [.4, .1, 0x3d8bff], [.62, -.1, 0xff4d6d]].forEach(function (b) {
        pad.add(mesh(sph(.1, 18), M(b[2], { r: .2, e: b[2], ei: .12 }), b[0], b[1], .29));
      });
      [[-.28, -.2], [.26, -.2]].forEach(function (s) {
        var st = mesh(cyl(.15, .16, .12), dark, s[0], s[1], .31); st.rotation.x = Math.PI / 2; pad.add(st);
        var cap = mesh(cyl(.11, .12, .06), M(0x5b6480, { r: .6 }), s[0], s[1], .39); cap.rotation.x = Math.PI / 2; pad.add(cap);
      });
      pad.add(mesh(box(.14, .05, .04), M(0x9aa3b5), -.1, .22, .29)); pad.add(mesh(box(.14, .05, .04), M(0x9aa3b5), .1, .22, .29));
      pad.add(mesh(sph(.05, 10), M(0x4d9fff, { e: 0x4d9fff }), 0, .38, .25));
      G.add(pad);
      var cube = mesh(rbox(.55, .55, .55, .1), M(0x3d8bff, { e: 0x1a4fb0, ei: .4, r: .25 }), -1.75, 2.15, -.2);
      spin.push({ o: cube }); G.add(cube);
      G.add(blob(4.8, 2.6, -.6));
      return { g: G, spin: spin };
    }

    function softwareModel() {
      var G = new THREE.Group(), spin = [];
      var alu = M(0xcfd6e3, { m: .3, r: .32 }), alu2 = M(0xb4bdcd, { m: .3, r: .35 });
      var base = mesh(rbox(3.0, 2.0, .14, .06), alu, 0, -.25, .2); base.rotation.x = -Math.PI / 2; G.add(base);
      G.add(mesh(box(2.55, .012, 1.0), M(0x2a3050, { r: .6 }), 0, -.175, -.08));
      var k = keys(12, 4, .17, .17, .205, .215, 0x3a4266); k.position.set(0, -.15, -.08); G.add(k);
      G.add(mesh(rbox(1.0, .02, .58, .01), alu2, 0, -.17, .72));
      var lid = new THREE.Group(); lid.position.set(0, -.2, -.75); lid.rotation.x = -.22;
      lid.add(mesh(rbox(3.0, 1.95, .1, .05), alu, 0, .98, 0));
      lid.add(mesh(box(2.86, 1.82, .01), M(0x0e1220), 0, .98, .055));
      lid.add(mesh(sph(.025, 8), M(0x111111), 0, 1.84, .06));
      var scr = new THREE.Group(); scr.position.set(0, .96, .065); lid.add(scr);
      scr.add(mesh(box(2.72, 1.66, .01), M(0xf3f6ff, { r: .7, e: 0xffffff, ei: .12 })));
      scr.add(mesh(box(2.72, .2, .02), M(0x3d6bff, { e: 0x3d6bff, ei: .15 }), 0, .73, .01));
      [0xff6b6b, 0xffd23f, 0x2fd08b].forEach(function (c, n) { scr.add(mesh(sph(.025, 8), M(c), -1.2 + n * .1, .73, .03)); });
      [[-.85, .22, .78, .72, 0x4d9fff], [.07, .22, .9, .72, 0xffa24d], [.93, .22, .62, .72, 0xb89bff], [-.4, -.48, 1.78, .36, 0xdfe6f5], [.87, -.48, .78, .36, 0x2fd08b]].forEach(function (c) {
        scr.add(mesh(rbox(c[2], c[3], .03, .05), M(c[4], { r: .55, e: c[4], ei: .1 }), c[0], c[1], .02));
        scr.add(mesh(box(c[2] * .6, .05, .02), M(0xffffff), c[0] - c[2] * .12, c[1] + c[3] / 2 - .12, .04));
      });
      G.add(lid);
      var ph = new THREE.Group(); ph.position.set(1.55, .5, .75); ph.rotation.set(-.08, -.45, 0);
      ph.add(mesh(rbox(.9, 1.7, .12, .12), M(0x2a3252, { r: .3 })));
      ph.add(mesh(rbox(.8, 1.58, .02, .009), M(0x0e1220), 0, 0, .062));
      ph.add(mesh(rbox(.76, 1.5, .02, .009), M(0x9fdcff, { r: .6, e: 0x2f8fd0, ei: .22 }), 0, -.02, .07));
      ph.add(mesh(rbox(.22, .06, .02, .009), M(0x0e1220), 0, .72, .075));
      [[-.17, .38, 0xffffff], [.17, .38, 0xffa24d], [-.17, .04, 0x2fd08b], [.17, .04, 0xb89bff]].forEach(function (t) {
        ph.add(mesh(rbox(.28, .28, .03, .014), M(t[2], { r: .55 }), t[0], t[1], .085));
      });
      ph.add(mesh(rbox(.62, .18, .03, .014), M(0x3d6bff, { e: 0x3d6bff, ei: .15 }), 0, -.45, .085));
      G.add(ph);
      var b = bulb(1.1); b.position.set(1.75, 2.05, -.5); spin.push({ o: b }); G.add(b);
      G.add(blob(5, 3, -.33));
      return { g: G, spin: spin };
    }

    function iotModel() {
      var G = new THREE.Group(), spin = [];
      var white = M(0xeef1f7, { r: .36 }), tire = M(0x1e2335, { r: .7 }), orange = M(0xffa21f, { r: .3 });
      G.add(mesh(rbox(2.0, .42, 1.4, .14), white, 0, .15, 0));
      G.add(mesh(rbox(2.06, .12, 1.46, .05), orange, 0, -.02, 0));
      G.add(mesh(box(1.25, .07, .85), M(0x2f9e5b, { r: .5 }), -.1, .4, 0));
      [[-.4, .2, .22], [.1, -.15, .3], [.35, .22, .16]].forEach(function (c) { G.add(mesh(box(c[2], .07, .18), M(0x111522), c[0], .47, c[1])); });
      [-.55, -.45, -.35].forEach(function (x) { G.add(mesh(sph(.035, 8), M(0xffd23f, { e: 0xffb000, ei: .6 }), x, .45, -.25)); });
      [-.3, .3].forEach(function (x) { G.add(mesh(sph(.08, 14), M(0x9aa3b5, { m: .5, r: .2 }), x, .2, .7)); });  // front sensors
      [[-1.1, .45], [1.1, .45], [-1.1, -.45], [1.1, -.45]].forEach(function (w) {
        var sgn = Math.sign(w[0]);
        var wh = mesh(cyl(.42, .42, .3, 32), tire, w[0], -.02, w[1]); wh.rotation.z = Math.PI / 2; G.add(wh);
        var tr = mesh(tor(.36, .05), M(0x2a3050, { r: .8 }), w[0] + sgn * .15, -.02, w[1]); tr.rotation.y = Math.PI / 2; G.add(tr);
        var hub = mesh(cyl(.2, .2, .32, 20), orange, w[0] + sgn * .01, -.02, w[1]); hub.rotation.z = Math.PI / 2; G.add(hub);
        var cap = mesh(cyl(.07, .07, .34, 12), M(0xffffff), w[0] + sgn * .02, -.02, w[1]); cap.rotation.z = Math.PI / 2; G.add(cap);
      });
      G.add(mesh(cyl(.1, .12, .45), M(0x9aa3b5, { m: .35 }), .2, .65, 0));
      var head = new THREE.Group(); head.position.set(.2, 1.15, 0); G.add(head);
      head.add(mesh(rbox(1.1, .72, .78, .2), white));
      head.add(mesh(rbox(.88, .48, .05, .02), M(0x1b2033, { r: .25 }), 0, 0, .39));
      [-.2, .2].forEach(function (x) {
        head.add(mesh(sph(.12, 18), M(0x7fd8ff, { e: 0x2fa8ff, ei: .9 }), x, .01, .42));
        head.add(mesh(sph(.035, 10), M(0xffffff, { e: 0xffffff }), x + .05, .06, .52));
      });
      head.add(mesh(box(.2, .03, .02), M(0x7fd8ff, { e: 0x2fa8ff, ei: .6 }), 0, -.15, .42));
      [-.57, .57].forEach(function (x) { var e = mesh(cyl(.12, .12, .08, 18), orange, x, 0, 0); e.rotation.z = Math.PI / 2; head.add(e); });
      head.add(mesh(cyl(.025, .025, .5, 8), M(0x3a4260), -.25, .6, 0));
      head.add(mesh(sph(.09, 14), M(0xff4d6d, { e: 0xff2040, ei: .7 }), -.25, .88, 0));
      var wifi = new THREE.Group(); wifi.position.set(1.35, 1.55, -.2); wifi.rotation.z = Math.PI / 4;
      [.22, .42, .62].forEach(function (r) { wifi.add(new THREE.Mesh(tor(r, .055, Math.PI / 2), M(0x3d8bff, { e: 0x1a5fd0, ei: .55 }))); });
      wifi.add(mesh(sph(.08, 12), M(0x3d8bff, { e: 0x1a5fd0, ei: .55 })));
      G.add(wifi);
      var b = bulb(.85); b.position.set(-1.35, 1.75, -.4); spin.push({ o: b }); G.add(b);
      G.add(blob(3.8, 2.8, -.45));
      return { g: G, spin: spin, head: head, wifi: wifi };
    }
    var BUILD = [gameModel, softwareModel, iotModel];
    var TINT = [0x2fd08b, 0xff8a3d, 0x4d9fff];

    function fitGroup(g) {                                    // centre on bounding sphere (ignoring shadows)
      var bb = new THREE.Box3();
      g.updateMatrixWorld(true);
      g.children.forEach(function (c) { if (!c.userData.skip) bb.expandByObject(c); });
      var s = bb.getBoundingSphere(new THREE.Sphere());
      g.children.forEach(function (c) { c.position.sub(s.center); });
      return s.radius;
    }
    function animateModel(m, t, k) {
      m.spin.forEach(function (s, n) {
        if (s.hop != null) s.o.position.y = s.hop + Math.abs(Math.sin(t * 3 + k)) * .12;
        else s.o.rotation.y = t * (n ? .9 : .7) + k;
      });
      if (m.head) m.head.rotation.y = Math.sin(t * .9 + k) * .35;
      if (m.wifi) m.wifi.children.forEach(function (a, n) { a.visible = (((t + k) * 2.2 | 0) % 4) >= n; });
    }

    /* ---------- a stage = renderer + scene for one canvas ---------- */
    function Stage(host, kind, i) {
      var canvas = document.createElement('canvas');
      canvas.setAttribute('aria-hidden', 'true');
      host.appendChild(canvas);
      var r = new THREE.WebGLRenderer({ canvas: canvas, alpha: true, antialias: !IOS, powerPreference: MOBILE ? 'low-power' : 'default' });
      r.outputColorSpace = THREE.SRGBColorSpace;
      r.toneMapping = THREE.ACESFilmicToneMapping; r.toneMappingExposure = 1.08;
      this.r = r; this.cam = new THREE.PerspectiveCamera(kind === 'hero' ? 26 : 30, 1.4, .1, 80);
      this.host = host; this.canvas = canvas; this.kind = kind; this.visible = false; this.first = true;
      this.px = this.py = this.tx = this.ty = 0;
      this.setModel(i);
      var self = this;
      if (window.ResizeObserver) new ResizeObserver(function () { self.resize(); }).observe(canvas);
    }
    Stage.prototype.lights = function (sc, tint) {
      sc.add(new THREE.HemisphereLight(0xffffff, 0x3a4466, 1.45));
      var key = new THREE.DirectionalLight(0xffffff, 2.4); key.position.set(3, 5, 5); sc.add(key);
      var fill = new THREE.DirectionalLight(0xbcd4ff, .7); fill.position.set(-5, 1, 3); sc.add(fill);
      var rim = new THREE.DirectionalLight(tint, 2.4); rim.position.set(-4, 3, -4); sc.add(rim);
    };
    Stage.prototype.setModel = function (i) {
      var sc = new THREE.Scene();
      if (this.kind === 'hero') {
        this.lights(sc, 0x7fb4ff);
        var parts = [], G = new THREE.Group();
        [0, 1, 2].forEach(function (k) {
          var m = BUILD[k](), wrap = new THREE.Group(), R = fitGroup(m.g), s = (k === 1 ? 1.75 : 1.5) / R;
          wrap.add(m.g); wrap.scale.setScalar(s);
          wrap.position.set((k - 1) * 3.15, k === 1 ? .3 : 0, k === 1 ? -.5 : 0);
          G.add(wrap); m.wrap = wrap; m.s = s; m.k = s; m.base = [.35, -.1, -.45][k]; parts.push(m);
        });
        var ring = new THREE.Mesh(tor(3.45, .035), new THREE.MeshBasicMaterial({ color: 0x8fc7ff, transparent: true, opacity: .85, toneMapped: false }));
        ring.rotation.x = Math.PI / 2; ring.position.y = -1.1; G.add(ring);
        var ring2 = new THREE.Mesh(tor(3.45, .16), new THREE.MeshBasicMaterial({ color: 0x3d8bff, transparent: true, opacity: .14, toneMapped: false, depthWrite: false }));
        ring2.rotation.x = Math.PI / 2; ring2.position.y = -1.1; G.add(ring2);
        G.add(blob(9, 3.2, -1.12));
        sc.add(G);
        this.mdl = { g: G, parts: parts }; this.fitR = 3.9;
      } else {
        this.lights(sc, TINT[i]);
        var mdl = BUILD[i](); this.fitR = fitGroup(mdl.g); sc.add(mdl.g); this.mdl = mdl;
      }
      this.scene = sc; this.i = i; this.first = true;
      this.resize();
    };
    Stage.prototype.resize = function () {
      var w = this.canvas.clientWidth, h = this.canvas.clientHeight; if (!w || !h) return;
      this.r.setPixelRatio(DPR()); this.r.setSize(w, h, false);
      var cam = this.cam; cam.aspect = w / h;
      var vfov = cam.fov * Math.PI / 180, hfov = 2 * Math.atan(Math.tan(vfov / 2) * cam.aspect);
      var d = this.kind === 'hero'
        ? Math.max(5.1 / Math.tan(hfov / 2), 2.5 / Math.tan(vfov / 2))    // the row is ~10 wide x 5 tall
        : this.fitR / Math.sin(Math.min(vfov, hfov) / 2) * .92;
      if (this.kind === 'hero') { cam.position.set(0, d * .2, d); cam.lookAt(0, -.05, 0); }
      else { cam.position.set(0, d * .26, d); cam.lookAt(0, -this.fitR * .04, 0); }
      cam.updateProjectionMatrix();
      if (this.kind === 'hero' && this.mdl && this.mdl.parts) {       // line the name labels up under each model
        cam.updateMatrixWorld();
        var btns = this.host.parentNode ? this.host.parentNode.querySelectorAll('.trio-hit button') : [];
        this.mdl.parts.forEach(function (p, k) {
          if (!btns[k]) return;
          var v = new THREE.Vector3(p.wrap.position.x, -.2, p.wrap.position.z).project(cam);
          btns[k].style.setProperty('--x', ((v.x + 1) * 50).toFixed(2) + '%');
        });
      }
      this.dirty = true; kick();
    };
    Stage.prototype.frame = function (t) {
      var m = this.mdl, still = reduced || level >= 2;
      this.px += (this.tx - this.px) * .08; this.py += (this.ty - this.py) * .08;
      if (m.parts) {
        var hot = this.hot == null ? -1 : this.hot;
        m.parts.forEach(function (p, k) {
          var tk = p.s * (k === hot ? 1.14 : hot >= 0 ? .92 : 1);
          if (Math.abs(tk - p.k) > .001) { p.k += (tk - p.k) * (still ? 1 : .14); p.wrap.scale.setScalar(p.k); }
          p.wrap.rotation.y = p.base + (still ? 0 : Math.sin(t * .5 + k * 2.1) * .4);
          p.wrap.position.y = (k === 1 ? .3 : 0) + (still ? 0 : Math.sin(t * 1.2 + k * 1.7) * .08);
          if (!still) animateModel(p, t, k);
        });
        m.g.rotation.y = this.px * .3;
      } else {
        m.g.rotation.y = (still ? -.35 : -.35 + Math.sin(t * .45) * .38) + this.px * .6;
        m.g.rotation.x = this.py * .25;
        m.g.position.y = still ? 0 : Math.sin(t * 1.3) * .06;
        if (!still) animateModel(m, t, 0);
      }
      this.r.render(this.scene, this.cam);
      if (this.first) { this.first = false; this.host.classList.add(this.host.classList.contains('cs-host') ? 'live' : 'ready'); }
    };
    function follow(el, st) {
      if (!el || !matchMedia('(hover: hover)').matches) return;
      el.addEventListener('pointermove', function (e) {
        var b = el.getBoundingClientRect();
        st.tx = (e.clientX - b.left) / b.width - .5; st.ty = (e.clientY - b.top) / b.height - .5;
      });
      el.addEventListener('pointerleave', function () { st.tx = st.ty = 0; });
    }

    /* ---------- one shared loop, only while something is visible ---------- */
    function all() { return sheetStage ? stages.concat(sheetStage) : stages; }
    function degrade() {
      level++;
      root.classList.add('lite');
      all().forEach(function (s) { s.resize(); });
    }
    function loop(now) {
      var list = all().filter(function (s) { return s.visible; });
      if (!list.length || document.hidden) { running = false; prev = 0; return; }
      if (level >= 2 || reduced) {                            // still: draw what changed, then stop
        list.forEach(function (s) { if (s.dirty || s.first) { s.frame(1.2); s.dirty = false; } });
        running = false; prev = 0; return;
      }
      requestAnimationFrame(loop);
      if (prev) {
        gaps.push(now - prev);
        if (gaps.length >= 45) {
          gaps.sort(function (a, b) { return a - b; });
          var p75 = gaps[33]; gaps = [];                    // 75th percentile frame gap
          if (p75 > (level ? 36 : 24)) degrade();
        }
      }
      prev = now;
      if (level === 1 && (skip ^= 1)) return;                 // ~30fps
      var t = (now - t0) / 1000;
      list.forEach(function (s) { s.frame(t); s.dirty = false; });
    }
    function kick() { if (ready && !running) { running = true; requestAnimationFrame(loop); } }

    /* ---------- stages ---------- */
    var vis = new IntersectionObserver(function (es) {
      es.forEach(function (e) { all().forEach(function (s) { if (s.canvas === e.target) s.visible = e.isIntersecting; }); });
      kick();
    }, { rootMargin: '60px 0px' });
    var hs = null;
    if (heroSlot) { hs = new Stage(heroSlot, 'hero', 0); stages.push(hs); follow(heroSlot.parentNode, hs); }
    api.trioHot = function (k) { if (hs) { hs.hot = k; hs.dirty = true; kick(); } };
    stages.forEach(function (s) { vis.observe(s.canvas); });

    /* tracks ring: still renders of the 3 models for every card, then one live
       stage that main.js moves into whichever card is at the front */
    if (!MOBILE) (function snaps() {
      var host = document.createElement('div');
      host.style.cssText = 'position:fixed;left:-2000px;top:0;width:520px;height:340px;pointer-events:none';
      document.body.appendChild(host);
      var st = new Stage(host, 'card', 0), out = [];
      level = 0; st.r.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
      [0, 1, 2].forEach(function (i) {
        if (i) st.setModel(i);
        st.resize(); st.frame(1.2);
        try { out[i] = st.canvas.toDataURL('image/png'); } catch (e) {}
      });
      level = lite() ? 1 : 0;
      st.r.dispose(); if (st.r.forceContextLoss) st.r.forceContextLoss(); host.remove();
      window.AFO3D.snaps = out;
      dispatchEvent(new CustomEvent('afo3d:snaps', { detail: out }));
    })();
    var ringStage = null;
    api.ring = function (i, el) {
      if (!el) return;
      if (!ringStage) { ringStage = new Stage(el, 'card', i); stages.push(ringStage); vis.observe(ringStage.canvas); follow(el.closest('.cs'), ringStage); }
      else { el.appendChild(ringStage.canvas); ringStage.host = el; if (ringStage.i !== i) ringStage.setModel(i); else ringStage.resize(); }
      ringStage.first = true; ringStage.visible = true; kick();
    };

    api.sheet = function (i, el) {
      if (!el) return;
      if (!sheetStage) sheetStage = new Stage(el, 'card', i);
      else { el.appendChild(sheetStage.canvas); sheetStage.host = el; if (sheetStage.i !== i) sheetStage.setModel(i); else sheetStage.resize(); }
      sheetStage.first = true; sheetStage.visible = true; kick();
    };
    api.sheetStop = function () { if (sheetStage) sheetStage.visible = false; };
    ready = true;
    if (pending) { api.sheet(pending[0], pending[1]); pending = null; }
    dispatchEvent(new Event('afo3d:ready'));
    document.addEventListener('visibilitychange', kick);
    kick();
  }
})();
