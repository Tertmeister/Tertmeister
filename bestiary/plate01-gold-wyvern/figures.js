// figures.js — every engraved subject of Plate I, drawn as SVG paths in local units and engraved with the
// library's burin engine: outline + three hatch families from a pillow-lit tone field, back parts occluded by
// front parts (excl). Each builder fills an Ink with named groups so film.js can cut them in time.
import * as B from './engine/burin.js';

export const LIGHT = [-0.6, -0.72];
// offset an open polyline sideways by d (positive = left of travel)
const offsetLine = (P, d) => { const N = B.normals(P, false); return P.map((p, i) => [p[0] + N[i][0] * d, p[1] + N[i][1] * d]); };
const polysOf = (...shs) => shs.flatMap(s => s.polys);

// engrave one closed shape: outline, first hatching, crossing, darks (groups `${g}ol`, `${g}h1`, `${g}h2`, `${g}h3`)
export function engr(ink, sh, { g, spacing = 3.6, angle = -0.62, wMax = 1.45, outlineW = 1.7, excl = null, base = 0.06, seed = 1, tone = null, bend = 0, t2 = 0.5, t3 = 0.78, lz = 0.55 } = {}) {
  const tn = tone || B.formTone(sh.polys, { light: LIGHT, base, lz });
  ink.group(g + 'ol'); for (const p of sh.polys) B.outline(ink, p, { w: outlineW, light: LIGHT, seed, excl });
  for (const l of sh.lines || []) B.stroke(ink, l, outlineW * 0.75, { excl });
  ink.group(g + 'h1'); B.hatch(ink, sh.polys, { angle, spacing, tone: tn, thr: 0.12, wMax, seed, excl, bend });
  ink.group(g + 'h2'); B.hatch(ink, sh.polys, { angle: angle + 1.05, spacing: spacing * 1.1, tone: tn, thr: t2, wMax: wMax * 0.8, seed: seed + 1, excl, bend: -bend * 0.6 });
  ink.group(g + 'h3'); B.hatch(ink, sh.polys, { angle: angle - 0.5, spacing: spacing * 1.25, tone: tn, thr: t3, wMax: wMax * 0.6, seed: seed + 2, excl });
  return tn;
}

// ---------------------------------------------------------------- the wyvern / dragon, in local units (torso centre = 0,0)
const P = {
  torso: 'M -205 30 C -200 -25 -130 -70 -20 -78 C 80 -84 150 -60 172 -22 C 188 8 168 52 100 66 C 10 84 -110 88 -170 72 C -200 64 -208 48 -205 30 Z',
  neck: 'M 118 -48 C 158 -100 198 -150 250 -172 C 280 -184 305 -186 322 -180 L 334 -146 C 306 -148 280 -140 260 -122 C 228 -94 200 -50 176 -12 Z',
  dneck: 'M 118 -48 C 150 -120 180 -200 240 -246 C 270 -268 300 -272 320 -266 L 334 -232 C 306 -232 282 -222 264 -200 C 226 -150 200 -70 176 -12 Z',
  head: 'M 310 -192 C 335 -210 380 -208 410 -194 L 462 -170 C 470 -164 466 -156 456 -156 L 408 -152 L 452 -136 C 448 -126 432 -124 418 -128 L 360 -140 C 338 -130 318 -136 308 -152 C 300 -168 302 -184 310 -192 Z',
  crest: 'M 318 -196 L 272 -230 L 330 -204 Z M 342 -205 L 306 -246 L 354 -209 Z',
  dcrest: 'M 316 -282 L 250 -330 L 330 -290 Z M 342 -292 L 296 -352 L 356 -296 Z',
  tail: 'M -195 20 C -260 22 -320 40 -360 78 C -392 110 -410 150 -398 178 C -388 196 -364 192 -368 172 C -374 146 -350 112 -312 92 C -272 72 -230 66 -192 62 Z',
  barb: 'M -398 168 L -432 192 L -398 224 L -378 194 Z',
  wing: 'M 60 -56 L 118 -168 L 172 -282 C 140 -330 104 -368 64 -394 C 30 -352 -30 -346 -86 -384 C -100 -338 -140 -312 -208 -324 C -206 -276 -232 -244 -284 -214 C -238 -168 -184 -116 -122 -64 C -52 -68 8 -60 60 -56 Z',
  bones: 'M 172 -282 C 140 -320 100 -360 64 -394 M 172 -282 C 90 -320 0 -360 -86 -384 M 172 -282 C 60 -300 -80 -320 -208 -324 M 172 -282 C 40 -260 -140 -230 -284 -214 M 62 -58 L 118 -168 L 172 -282',
  thumb: 'M 172 -282 L 204 -306 L 190 -272 Z',
  leg: 'M -168 24 C -120 10 -62 40 -56 96 C -52 128 -68 148 -86 158 L -92 192 L -54 196 C -44 198 -42 208 -52 210 L -66 211 L -60 218 L -80 214 L -88 220 L -104 214 L -124 214 C -136 212 -138 200 -128 194 L -122 166 C -132 148 -146 128 -156 104 C -170 78 -182 46 -168 24 Z',
  talons: 'M -52 210 C -44 214 -40 220 -42 226 M -66 212 C -60 218 -58 224 -60 230 M -86 216 C -82 222 -82 228 -86 232',
  fleg: 'M 92 36 C 116 60 126 100 116 132 L 146 142 C 154 146 152 158 142 158 L 96 154 C 84 152 84 140 92 132 C 98 110 94 82 78 62 Z',
};

// a creature: dragon (4 legs, long neck, runes) or wyvern (2 legs, wings as arms). Returns regions and anchors.
export function buildCreature(ink, at, { g = 'c', dragon = false, window = false, seed = 1, spacing = 3.6, wMax = 1.45, outlineW = 1.7 } = {}) {
  const f = (dx = 0, dy = 0, s = 1) => B.compose(at, B.xf(dx, dy, s));
  const sh = d => B.shape(d, f());
  const farWing = B.shape(P.wing, f(dragon ? 36 : 46, dragon ? -40 : -30, 0.9));
  const farBones = B.shape(P.bones, f(dragon ? 36 : 46, dragon ? -40 : -30, 0.9));
  const farLeg = B.shape(P.leg, f(62, -12, 0.95));
  const farFleg = dragon ? B.shape(P.fleg, f(40, -10, 0.95)) : null;
  const tail = sh(P.tail), barb = sh(P.barb), torso = sh(P.torso);
  const neck = sh(dragon ? P.dneck : P.neck);
  const head = B.shape(P.head, dragon ? f(0, -86) : f());
  const crest = B.shape(dragon ? P.dcrest : P.crest, f());
  const wing = B.shape(P.wing, dragon ? f(-10, -18) : f()), bones = B.shape(P.bones, dragon ? f(-10, -18) : f()), thumb = B.shape(P.thumb, dragon ? f(-10, -18) : f());
  const leg = sh(P.leg), fleg = dragon ? sh(P.fleg) : null;
  const o = { spacing, wMax, outlineW };
  // back to front: far wing, far legs, tail, torso, neck, head, near leg(s), near wing
  const front = { wing: wing.polys, leg: leg.polys, fleg: fleg ? fleg.polys : [], head: [...head.polys, ...crest.polys], neck: neck.polys, torso: torso.polys, tail: [...tail.polys, ...barb.polys] };
  const ex = (...keys) => keys.flatMap(k => front[k] || []);
  engr(ink, farWing, { g: g + 'fw', ...o, seed, excl: ex('wing', 'torso', 'neck', 'head', 'tail'), base: 0.22, angle: -1.1 });
  ink.group(g + 'fwol'); for (const l of farBones.lines) B.stroke(ink, l, outlineW * 0.7, { excl: ex('wing', 'torso', 'neck', 'head') });
  engr(ink, farLeg, { g: g + 'fl', ...o, seed: seed + 3, excl: ex('torso', 'leg', 'tail', 'wing'), base: 0.3 });
  if (farFleg) engr(ink, farFleg, { g: g + 'ff', ...o, seed: seed + 4, excl: ex('torso', 'fleg', 'neck', 'wing'), base: 0.3 });
  engr(ink, tail, { g: g + 'tl', ...o, seed: seed + 5, excl: ex('leg', 'wing'), angle: -0.2 });
  engr(ink, barb, { g: g + 'tb', ...o, seed: seed + 6 });
  const torsoTone = engr(ink, torso, { g: g + 'to', ...o, seed: seed + 7, excl: ex('wing', 'leg', 'fleg', 'neck'), bend: 0.0012 });
  engr(ink, neck, { g: g + 'nk', ...o, seed: seed + 8, excl: ex('head', 'wing'), angle: -1.0 });
  engr(ink, head, { g: g + 'hd', ...o, seed: seed + 9, angle: -0.4 });
  // dorsal spines along the back, neck and tail root
  const guide = (dragon ? [[-200, 18], [-150, -44], [-80, -72], [0, -80], [80, -78], [150, -96], [200, -190], [250, -246], [296, -262]]
                        : [[-200, 18], [-150, -44], [-80, -72], [0, -80], [80, -78], [140, -84], [190, -128], [236, -160], [290, -182]]).map(p => p);
  const spineSubs = [];
  const gp = B.resample(guide, 26);
  for (let k = 1; k < gp.length - 1; k++) {
    const [x, y] = gp[k], dx = gp[k + 1][0] - gp[k - 1][0], dy = gp[k + 1][1] - gp[k - 1][1], Lg = Math.hypot(dx, dy) || 1, nx = dy / Lg, ny = -dx / Lg;
    const h = 16 + 6 * Math.sin(k * 1.7), wd = 9;
    spineSubs.push({ pts: [[x - dx / Lg * wd, y - dy / Lg * wd], [x + nx * h + dx / Lg * 4, y + ny * h + dy / Lg * 4], [x + dx / Lg * wd, y + dy / Lg * wd]].map(at), closed: true });
  }
  const spines = B.fromSubs(spineSubs);
  front.spines = spines.polys;
  ink.group(g + 'spol'); for (const pq of spines.polys) B.outline(ink, pq, { w: outlineW * 0.8, light: LIGHT, seed, excl: ex('wing'), run: 0 });
  ink.group(g + 'sph1'); B.hatch(ink, spines.polys, { angle: -0.3, spacing: spacing * 0.9, tone: () => 0.55, thr: 0.12, wMax: wMax * 0.8, seed, excl: ex('wing') });
  engr(ink, crest, { g: g + 'cr', ...o, seed: seed + 10 });
  engr(ink, leg, { g: g + 'lg', ...o, seed: seed + 11, excl: ex('wing'), angle: -1.2 });
  ink.group(g + 'lgol'); for (const l of B.shape(P.talons, f()).lines) B.stroke(ink, l, outlineW * 0.9);
  if (fleg) engr(ink, fleg, { g: g + 'fg', ...o, seed: seed + 12, excl: ex('wing'), angle: -1.2 });
  engr(ink, wing, { g: g + 'wg', ...o, seed: seed + 13, base: 0.02, angle: -1.05, t2: 0.62 });
  ink.group(g + 'wgol'); for (const l of bones.lines) B.stroke(ink, l, outlineW * 0.95); for (const p of thumb.polys) B.outline(ink, p, { w: outlineW, light: LIGHT });
  // the eye
  const hx = dragon ? f(0, -86) : f(), e = hx([372, -184]);
  ink.group(g + 'hdol'); ink.dot(e[0], e[1], 3.4 * (at.scale || 1));
  // scales: rows of small arcs over neck, torso and tail, densest in the half-tones
  ink.group(g + 'sc');
  const S = at.scale || 1, R = B.RNG(seed + 40), bodyPolys = [...torso.polys, ...neck.polys, ...tail.polys];
  const exS = ex('wing', 'leg', 'fleg', 'head');
  const bb = B.bboxOf(bodyPolys);
  for (let y = bb[1]; y < bb[3]; y += 13 * S) for (let x = bb[0] + ((Math.round((y - bb[1]) / (13 * S)) % 2) * 7 * S); x < bb[2]; x += 14 * S) {
    if (!B.inAny(bodyPolys, x, y) || B.inAny(exS, x, y)) continue;
    const tv = torsoTone(x, y); if (R() > 0.35 + tv) continue;
    const pts = []; for (let k = 0; k <= 6; k++) { const a = Math.PI * (k / 6); pts.push([x - Math.cos(a) * 5.5 * S, y + Math.sin(a) * 4.5 * S]); }
    B.stroke(ink, pts, 0.7 * S + 0.4 * tv, { taper: 3 * S });
  }
  // dragon: runes carved round the chest (the mana pathways a wyvern lacks)
  const runes = [];
  if (dragon) {
    ink.group(g + 'rn');
    const glyphs = ['M 0 -9 L 0 9 M 0 -9 L 6 -3 M 0 0 L 6 6', 'M -5 -9 L 5 9 M 5 -9 L -5 9', 'M 0 -9 L 0 9 M -6 -3 L 0 3 L 6 -3', 'M -5 9 L 0 -9 L 5 9 M -3 2 L 3 2', 'M 0 -9 L 0 9 M 0 -2 L 6 -8'];
    const cs = [[120, -36], [138, -14], [146, 10], [140, 34], [124, 52]];
    cs.forEach(([cx, cy], k) => { const sh2 = B.shape(glyphs[k], B.compose(at, B.xf(cx, cy, 1.1))); for (const l of sh2.lines) B.stroke(ink, l, 1.3 * S + 0.4, { taper: 2 }); runes.push(at([cx, cy])); });
  }
  const regions = {
    body: { polys: bodyPolys, path: B.toPath([...torso.subs, ...neck.subs, ...tail.subs]) },
    head: { polys: head.polys, path: head.path },
    chest: (() => { const c = B.ellipse(...at([136, 8]), 34 * S, 66 * S, 0.15); return { polys: c.polys, path: c.path }; })(),
  };
  const anchors = { snout: (dragon ? f(0, -86) : f())([462, -164]), jaw: (dragon ? f(0, -86) : f())([405, -148]), head: (dragon ? f(0, -86) : f())([380, -172]), chest: at([136, 8]), belly: at([-20, 74]), flank: at([215, -122]), runes };
  if (window) Object.assign(anchors, buildWindow(ink, at, regions, g));
  return { regions, anchors };
}

// ---------------------------------------------------------------- the cut-away rib window on Fig. 2
function buildWindow(ink, at, regions, g) {
  const S = at.scale || 1, W0 = B.ellipse(...at([-10, 4]), 150 * S, 62 * S, -0.04);
  // the window: paper inside, a bevelled double rule around it
  ink.group('win'); B.outline(ink, W0.polys[0], { w: 1.9, light: LIGHT }); B.outline(ink, B.offsetRing(W0.polys[0], 5 * S), { w: 0.7, light: LIGHT });
  // ribs: curved bands across the window
  ink.group('rib');
  for (let x = -138; x <= 128; x += 24) { const pts = []; for (let k = 0; k <= 16; k++) { const u = k / 16, y = -60 + 120 * u; pts.push(at([x + 10 * Math.sin(u * Math.PI) - 6, y])); } const inside = pts.filter(p => B.inPoly(W0.polys, p[0], p[1])); if (inside.length > 2) B.stroke(ink, inside, 1.1 * S, { taper: 4 }); }
  // the two Dynamo Sacs: sheathed columns of stacked discs (electrocytes) along the ribcage
  const sac = y => { const r = B.ring([[-140, y - 15], [96, y - 15], [104, y], [96, y + 15], [-140, y + 15], [-147, y]].map(at)); return r; };
  const upper = sac(-22), lower = sac(26);
  for (const [nm, s] of [['sacU', upper], ['sacL', lower]]) {
    ink.group(nm); B.outline(ink, s.polys[0], { w: 1.5, light: LIGHT });
    const yc = nm === 'sacU' ? -22 : 26;
    for (let x = -132; x <= 92; x += 9) { const e = B.ellipsePts(...at([x, yc]), 2.6 * S, 12.5 * S, 0, 14); B.stroke(ink, [...e, e[0]], 0.8 * S, { taper: 1 }); }
    B.hatch(ink, s.polys, { angle: 0, spacing: 3.2 * S, tone: B.linTone(...at([0, yc - 15]), ...at([0, yc + 15]), 0.15, 0.7), thr: 0.3, wMax: 0.9 * S, seed: 71 });
  }
  // the heart in its triple sheath of fat (the rings are cut later, on the line)
  const heart = B.shape('M 0 -16 C 10 -30 30 -26 30 -8 C 30 10 10 22 0 32 C -10 22 -30 10 -30 -8 C -30 -26 -10 -30 0 -16 Z', B.compose(at, B.xf(124, 2, 0.62)));
  ink.group('heart'); B.outline(ink, heart.polys[0], { w: 1.4, light: LIGHT });
  B.hatch(ink, heart.polys, { angle: -0.8, spacing: 2.6 * S, tone: B.formTone(heart.polys, { light: LIGHT, base: 0.2 }), thr: 0.12, wMax: 0.9 * S, seed: 81 });
  ink.group('sheath');
  for (let k = 1; k <= 3; k++) { const r = B.offsetRing(heart.polys[0], (3.2 + k * 3.4) * S); B.outline(ink, r, { w: 0.75, light: LIGHT, run: 0 }); }
  regions.sacU = { polys: upper.polys, path: upper.path }; regions.sacL = { polys: lower.polys, path: lower.path }; regions.window = { polys: W0.polys, path: W0.path };
  return { window: at([-10, 4]), sacU: at([-20, -22]), sacL: at([-20, 26]), heart: at([124, 2]) };
}

// ---------------------------------------------------------------- roundel contents (local units, radius 500)
export function buildSacDetail() {
  const ink = new B.Ink(), regions = {};
  // ribs behind
  ink.group('h1');
  for (let x = -420; x <= 420; x += 140) { const r = B.ring([[x - 26, -520], [x + 26, -520], [x + 30, 520], [x - 30, 520]]); B.hatch(ink, r.polys, { angle: 1.57, spacing: 7, tone: () => 0.5, thr: 0.1, wMax: 1.6, seed: 9 + x }); }
  const cols = [];
  for (const [nm, yc] of [['colU', -120], ['colL', 130]]) {
    const env = B.ring([[-430, yc - 88], [400, yc - 88], [440, yc], [400, yc + 88], [-430, yc + 88], [-462, yc]]);
    ink.group('ol'); B.outline(ink, env.polys[0], { w: 4.2, light: LIGHT });
    const discs = [];
    for (let x = -400; x <= 380; x += 34) {
      const e = B.ellipse(x, yc, 11, 70, 0, 40); discs.push(...e.polys);
      ink.group('ol'); B.outline(ink, e.polys[0], { w: 2.0, light: LIGHT, run: 0 });
      ink.group('h2'); B.hatch(ink, e.polys, { angle: 1.57, spacing: 6, tone: B.cylTone(x, yc, 70, 0), thr: 0.2, wMax: 1.8, seed: 3 + x });
    }
    ink.group('h3'); B.hatch(ink, env.polys, { angle: 0.02, spacing: 8, tone: B.linTone(0, yc - 88, 0, yc + 88, 0.2, 0.85), thr: 0.55, wMax: 1.4, seed: 5, excl: discs });
    regions[nm] = { polys: env.polys, path: env.path }; cols.push(env);
  }
  ink.group('rule'); for (let y = -480; y <= 480; y += 22) { const half = Math.sqrt(Math.max(0, 500 * 500 - y * y)); B.stroke(ink, [[-half, y], [half, y]], 0.45, { excl: cols.flatMap(c => c.polys) }); }
  return { ink, regions };
}

const SKULL = 'M -360 -40 C -330 -150 -200 -210 -60 -200 C 60 -192 200 -150 330 -100 L 430 -60 C 448 -52 446 -34 428 -30 L 120 -20 C 40 -10 -80 10 -200 30 C -300 40 -372 20 -360 -40 Z';
const JAW_OPEN = 'M -300 40 C -200 60 -40 80 120 120 L 380 200 C 396 206 394 222 376 222 L 100 170 C -20 150 -180 120 -290 90 C -330 78 -330 48 -300 40 Z';
const JAW_SHUT = 'M -300 40 C -200 50 -40 40 120 20 L 400 -8 C 416 -8 416 8 400 12 L 110 70 C -10 92 -180 110 -290 92 C -330 82 -330 50 -300 40 Z';
export function buildSkullDetail() {
  const ink = new B.Ink(), regions = {};
  const skull = B.shape(SKULL), orbit = B.ellipse(-60, -110, 58, 42, -0.1), nostril = B.ellipse(330, -84, 22, 12, 0.2);
  engr(ink, skull, { g: '', spacing: 7, wMax: 2.6, outlineW: 4.4, excl: [...orbit.polys, ...nostril.polys], seed: 21 });
  ink.group('ol'); B.outline(ink, orbit.polys[0], { w: 3.2, light: LIGHT }); B.outline(ink, nostril.polys[0], { w: 2.4, light: LIGHT });
  ink.group('h3'); B.hatch(ink, orbit.polys, { angle: 0.6, spacing: 5, tone: () => 0.95, thr: 0.1, wMax: 2.2, seed: 23 }); B.hatch(ink, orbit.polys, { angle: -0.6, spacing: 5.5, tone: () => 0.95, thr: 0.1, wMax: 2.0, seed: 24 });
  // hollow copper-enamel fangs: a long upper pair with a canal down each, smaller teeth behind
  const fangs = [];
  for (const [x, len, w] of [[250, 150, 34], [150, 120, 30], [40, 70, 22], [-50, 60, 20]]) {
    const fg = B.shape(`M ${x - w / 2} -24 C ${x - w / 2} ${-24 + len * 0.5} ${x - 4} ${-24 + len * 0.9} ${x + 4} ${-24 + len} C ${x + 6} ${-24 + len * 0.7} ${x + w / 2} ${-24 + len * 0.4} ${x + w / 2} -24 Z`);
    fangs.push(fg);
    ink.group('fang'); B.outline(ink, fg.polys[0], { w: 2.6, light: LIGHT });
    B.hatch(ink, fg.polys, { angle: 1.4, spacing: 5, tone: B.formTone(fg.polys, { light: LIGHT, base: 0.15 }), thr: 0.2, wMax: 1.5, seed: 30 + x });
    B.stroke(ink, [[x, -18], [x + 1, -24 + len * 0.82]], 1.3, { taper: 6 });          // the hollow canal
  }
  regions.fangs = { polys: fangs.flatMap(f => f.polys), path: B.toPath(fangs.flatMap(f => f.subs)) };
  // palate crystals: a row of hexagonal prisms along the roof of the mouth (cut on the line)
  const crys = [];
  for (let k = 0; k < 6; k++) { const cx = -150 + k * 74, cy = -44 - k * 3; const pts = []; for (let i = 0; i < 6; i++) { const a = i * Math.PI / 3 + 0.5; pts.push([cx + Math.cos(a) * 30, cy + Math.sin(a) * 22]); } crys.push(B.ring(pts)); }
  ink.group('cry'); for (const c of crys) { B.outline(ink, c.polys[0], { w: 3.0, light: LIGHT, run: 0 }); B.hatch(ink, c.polys, { angle: 0.9, spacing: 5, tone: () => 0.5, thr: 0.1, wMax: 1.6, seed: 51 }); }
  regions.crystals = { polys: crys.flatMap(c => c.polys), path: B.toPath(crys.flatMap(c => c.subs)) };
  // the lower jaw, open and shut (the open state is burnished out and the shut one cut on the line)
  const jo = B.shape(JAW_OPEN), js = B.shape(JAW_SHUT);
  engr(ink, jo, { g: 'jo', spacing: 7, wMax: 2.4, outlineW: 4, seed: 61, angle: -0.3 });
  engr(ink, js, { g: 'js', spacing: 7, wMax: 2.4, outlineW: 4, seed: 62, angle: -0.3 });
  // the spark between the fangs
  ink.group('spk');
  for (let k = 0; k < 12; k++) { const a = k / 12 * Math.PI * 2, L = k % 2 ? 80 : 160; B.stroke(ink, [[300 + Math.cos(a) * 18, 70 + Math.sin(a) * 18], [300 + Math.cos(a) * L, 70 + Math.sin(a) * L]], k % 2 ? 2.8 : 4.6, { taper: 14 }); }
  ink.group('rule'); for (let y = -480; y <= 480; y += 22) { const half = Math.sqrt(Math.max(0, 500 * 500 - y * y)); B.stroke(ink, [[-half, y], [half, y]], 0.45, { excl: [...skull.polys, ...jo.polys, ...js.polys, ...fangs.flatMap(f => f.polys)] }); }
  return { ink, regions };
}

export function buildTickDetail() {
  const ink = new B.Ink(), regions = {}, scales = [];
  // overlapping scales, four rows, each lower row tucked under the one above
  for (let row = 3; row >= 0; row--) for (let k = -4; k <= 4; k++) {
    const cx = k * 150 + (row % 2) * 75, cy = -260 + row * 150;
    scales.push(B.shape(`M ${cx - 92} ${cy - 40} C ${cx - 92} ${cy + 80} ${cx - 30} ${cy + 140} ${cx} ${cy + 150} C ${cx + 30} ${cy + 140} ${cx + 92} ${cy + 80} ${cx + 92} ${cy - 40} Z`));
  }
  // later scales (upper rows) cover earlier ones
  const order = scales.slice();
  order.forEach((s, i) => {
    const ex = order.slice(i + 1).flatMap(o => o.polys);
    ink.group('ol'); B.outline(ink, s.polys[0], { w: 3.2, light: LIGHT, excl: ex });
    ink.group('h1'); B.hatch(ink, s.polys, { angle: 1.2, spacing: 8, tone: B.formTone(s.polys, { light: LIGHT, base: 0.1 }), thr: 0.15, wMax: 2.0, seed: 90 + i, excl: ex });
    ink.group('h2'); B.hatch(ink, s.polys, { angle: -0.3, spacing: 9, tone: B.formTone(s.polys, { light: LIGHT, base: 0.1 }), thr: 0.55, wMax: 1.6, seed: 140 + i, excl: ex });
  });
  // Static-Ticks: oval bodies with eight legs, crawling out from under the scale edges
  const mites = [];
  for (const [x, y, r] of [[-170, 10, 0.4], [120, 150, -0.5], [-20, -140, 0.2], [260, -60, -1.1]]) {
    const body = B.ellipse(x, y, 34, 24, r), head = B.ellipse(x + Math.cos(r) * 38, y + Math.sin(r) * 38, 14, 11, r);
    mites.push(body, head);
    ink.group('mite'); B.outline(ink, body.polys[0], { w: 2.4, light: LIGHT, run: 0 }); B.outline(ink, head.polys[0], { w: 2.0, light: LIGHT, run: 0 });
    B.hatch(ink, body.polys, { angle: r + 1.2, spacing: 4.5, tone: B.formTone(body.polys, { light: LIGHT, base: 0.25 }), thr: 0.15, wMax: 1.4, seed: 200 + x });
    for (let k = 0; k < 4; k++) for (const sd of [-1, 1]) { const a = r + sd * (0.9 + k * 0.42); const p0 = [x + Math.cos(a) * 26, y + Math.sin(a) * 18]; const p1 = [x + Math.cos(a) * 58, y + Math.sin(a) * 50 + 6]; B.stroke(ink, [p0, [(p0[0] + p1[0]) / 2 + sd * 6, (p0[1] + p1[1]) / 2 - 8], p1], 1.6, { taper: 5 }); }
  }
  regions.mites = { polys: mites.flatMap(m => m.polys), path: B.toPath(mites.flatMap(m => m.subs)) };
  // the dielectric wax: a glossy highlight along each scale edge
  ink.group('wax'); order.slice(-9).forEach((s, i) => { const P0 = s.polys[0]; const pts = P0.slice(Math.floor(P0.length * 0.3), Math.floor(P0.length * 0.55)); if (pts.length > 2) B.stroke(ink, offsetLine(pts, 10).slice(1, -1), 1.2, { taper: 8 }); });
  // rain beading off the wax
  ink.group('rain');
  const R = B.RNG(77);
  for (let k = 0; k < 26; k++) { const x = -430 + R() * 860, y = -460 + R() * 380; B.stroke(ink, [[x, y], [x - 26, y + 70]], 1.1, { taper: 10 }); }
  for (let k = 0; k < 14; k++) { const x = -360 + R() * 720, y = -220 + R() * 520; const b = B.ellipse(x, y, 9, 11, 0, 20); B.outline(ink, b.polys[0], { w: 1.4, light: LIGHT, run: 0 }); ink.dot(x - 3, y - 4, 1.6); }
  ink.group('rule'); for (let y = -480; y <= 480; y += 22) { const half = Math.sqrt(Math.max(0, 500 * 500 - y * y)); B.stroke(ink, [[-half, y], [half, y]], 0.45, { excl: [...scales.flatMap(s => s.polys)] }); }
  return { ink, regions };
}

// a Static-Tick at natural size, for the margin
export function buildTinyMite(ink, at) {
  const f = p => at(p);
  const body = B.ring(B.ellipsePts(0, 0, 6, 4.2, 0.3, 24).map(f));
  ink.group('nat'); B.outline(ink, body.polys[0], { w: 1.0, light: LIGHT, run: 0 });
  for (let k = 0; k < 4; k++) for (const sd of [-1, 1]) { const a = 0.3 + sd * (0.9 + k * 0.42); B.stroke(ink, [f([Math.cos(a) * 4, Math.sin(a) * 3]), f([Math.cos(a) * 9, Math.sin(a) * 8])], 0.6, { taper: 1 }); }
  return { polys: body.polys, path: body.path };
}

// ---------------------------------------------------------------- gizzard stones: copper ore, quartz, Sylvan iron
export function buildGizzard(ink, at) {
  const S = at.scale || 1, stones = [];
  const shapes = [
    'M -30 -18 C -10 -30 20 -26 30 -8 C 36 8 22 26 0 28 C -22 30 -40 12 -30 -18 Z',
    'M -18 -24 L 14 -28 L 30 -2 L 16 26 L -16 24 L -30 0 Z',
    'M -26 -14 C -18 -30 18 -30 28 -12 C 34 4 24 22 4 24 C -16 26 -34 6 -26 -14 Z',
  ];
  shapes.forEach((d, k) => {
    const sh = B.shape(d, B.compose(at, B.xf(-70 + k * 70, k === 1 ? -6 : 4, 1)));
    stones.push(sh);
    ink.group('giz'); B.outline(ink, sh.polys[0], { w: 1.4, light: LIGHT });
    if (k === 1) { for (let i = 0; i < 3; i++) B.stroke(ink, [at([-70 + k * 70 - 10 + i * 9, -18]), at([-70 + k * 70 - 2 + i * 9, 18])], 0.7 * S, { taper: 2 }); }
    else B.hatch(ink, sh.polys, { angle: k ? 0.8 : -0.8, spacing: 3 * S, tone: B.formTone(sh.polys, { light: LIGHT, base: k === 2 ? 0.45 : 0.2 }), thr: 0.15, wMax: 0.9 * S, seed: 300 + k });
  });
  return { stones, centers: [at([-70, 4]), at([0, -6]), at([70, 4])] };
}

// ---------------------------------------------------------------- the arc: a forked bolt from the snout to the ground
export function buildArc(ink, from, to, seed = 7) {
  const R = B.RNG(seed), main = [from]; const n = 9;
  for (let k = 1; k < n; k++) { const u = k / n; main.push([from[0] + (to[0] - from[0]) * u + (R() - 0.5) * 70, from[1] + (to[1] - from[1]) * u + (R() - 0.5) * 24]); }
  main.push(to);
  ink.group('arc'); B.stroke(ink, B.resample(main, 3), 4.4, { taper: 14, swell: true });
  const forks = [];
  for (const k of [4, 6, 7]) { const p = main[k], q = [p[0] + (R() - 0.2) * 110, p[1] + 60 + R() * 70]; const mid = [(p[0] + q[0]) / 2 + (R() - 0.5) * 30, (p[1] + q[1]) / 2]; forks.push([p, mid, q]); }
  ink.group('fork'); for (const fk of forks) B.stroke(ink, B.resample(fk, 3), 2.3, { taper: 10 });
  // a band around the bolt, for the pale wash
  const mr = B.resample(main, 6), band = B.ring([...offsetLine(mr, 10), ...offsetLine(mr, -10).reverse()]);
  return { main, forks, band };
}

// ---------------------------------------------------------------- the Guild's doctrine: three emblems
export function buildEmblems(ink, at) {
  const S = at.scale || 1;
  // I. a sword laid down
  const sword = B.shape('M -70 -4 L 40 -4 L 52 0 L 40 4 L -70 4 Z M -78 -16 L -70 -16 L -70 16 L -78 16 Z M -104 -3 L -78 -3 L -78 3 L -104 3 Z', B.compose(at, B.xf(-400, 0, 1)));
  engr(ink, sword, { g: 'e1', spacing: 2.6 * S, wMax: 0.9, outlineW: 1.3, seed: 401, angle: 0.2 });
  ink.group('e1x'); B.stroke(ink, [at([-470, -26]), at([-330, 26])], 1.6, { taper: 6 }); B.stroke(ink, [at([-470, 26]), at([-330, -26])], 1.6, { taper: 6 });
  // II. a slab of dry stone
  const slab = B.shape('M -60 -18 L 50 -24 L 62 10 L 56 22 L -58 24 L -66 6 Z', B.compose(at, B.xf(0, 0, 1)));
  engr(ink, slab, { g: 'e2', spacing: 2.6 * S, wMax: 1.0, outlineW: 1.3, seed: 402, angle: -0.6 });
  // III. a wooden-shafted bolt, pointing up
  const bolt = B.shape('M -3 30 L -3 -26 L -9 -26 L 0 -42 L 9 -26 L 3 -26 L 3 30 Z M -3 30 L -10 44 L -3 40 Z M 3 30 L 10 44 L 3 40 Z', B.compose(at, B.xf(400, 0, 1)));
  engr(ink, bolt, { g: 'e3', spacing: 2.4 * S, wMax: 0.8, outlineW: 1.2, seed: 403, angle: 1.4 });
  return { centers: [at([-400, 0]), at([0, 0]), at([400, 0])] };
}

export { polysOf };
