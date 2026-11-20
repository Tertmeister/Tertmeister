// A Bestiary of Azul · Plate I · The Gold Wyvern — copperplate engraving, portrait sheet 1080×1920, 24 fps.
// One plate grows for the whole film; the camera is a loupe. Times follow TREATMENT.md and timeline.json
// (narration line times); every hit sits on the score's eighth-note grid (75 BPM: 0.1 + 0.4·k s).
import * as B from './engine/burin.js';
import { drawSheet, borderInk, engraveText, writeScript, wrapLines, roundelFrame, paperTexture, measure, PAL, FONTS } from './engine/plate.js';
import { Wash } from './engine/wash.js';
import { buildCreature, buildSacDetail, buildSkullDetail, buildTickDetail, buildTinyMite, buildGizzard, buildArc, buildEmblems } from './figures.js';
import { clamp, eio, eo, ss } from '/core/lib.js';

export const W = 1080, H = 1920;
const PLATE = [40, 60, 1040, 1860], BORDER = [62, 84, 1018, 1836];
const seg = (t, a, b) => clamp((t - a) / (b - a));
// the sheet: paper texture tiled beyond the 1080×1920 world so the margins continue under any framing, then the
// plate tone and the bevelled plate mark (as plate.js drawSheet, which paints the texture once)
function drawBigSheet(ctx) {
  const [x0, y0, x1, y1] = PLATE, tex = paperTexture(W, H);
  ctx.save(); ctx.fillStyle = PAL.paper; ctx.fillRect(-W, -H, W * 3, H * 3);
  ctx.globalCompositeOperation = 'multiply';
  for (let i = -1; i <= 1; i++) for (let j = -1; j <= 1; j++) ctx.drawImage(tex, i * W, j * H, W, H);
  ctx.globalAlpha = 0.55; ctx.fillStyle = PAL.plateTone; ctx.fillRect(x0, y0, x1 - x0, y1 - y0);
  ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
  const b = 5;
  ctx.fillStyle = PAL.bevelDark; ctx.beginPath(); ctx.moveTo(x0 - b, y0 - b); ctx.lineTo(x1 + b, y0 - b); ctx.lineTo(x1, y0); ctx.lineTo(x0, y0); ctx.lineTo(x0, y1); ctx.lineTo(x0 - b, y1 + b); ctx.closePath(); ctx.fill();
  ctx.fillStyle = PAL.bevelLight; ctx.beginPath(); ctx.moveTo(x1 + b, y0 - b); ctx.lineTo(x1 + b, y1 + b); ctx.lineTo(x0 - b, y1 + b); ctx.lineTo(x0, y1); ctx.lineTo(x1, y1); ctx.lineTo(x1, y0); ctx.closePath(); ctx.fill();
  ctx.strokeStyle = 'rgba(90,64,36,0.25)'; ctx.lineWidth = 1; ctx.strokeRect(x0 - b, y0 - b, x1 - x0 + 2 * b, y1 - y0 + 2 * b);
  ctx.restore();
}
const lerp = (a, b, t) => a + (b - a) * t;

// ------------------------------------------------------------------ cue times (eighth-note grid, see TREATMENT.md §6)
export const T = {
  runes: [2.1, 3.3], gold: 4.1, labelA: 0.9, small: [5.7, 9.7], mana: 7.3, labelB: 9.3,
  fig1: 12.1, rule: [12.5, 13.3], latin: 14.5, title: 16.5, series: 18.1, thunder: 18.5,
  border: [19.7, 23.3], main: { ol: [20.1, 22.5], h1: [21.3, 24.5], h2: [22.9, 25.7], h3: [24.1, 26.5], sc: [24.9, 26.9] }, fig2: 26.1,
  win: [27.7, 28.9], rib: [28.5, 29.7], sacU: [29.7, 31.3], sacL: [31.3, 32.9],
  r3: { ring: [35.7, 36.1], fly: [36.1, 37.3], cut: [36.1, 38.5], name: 37.7, note: 38.5, num: 37.3 },
  pulses: [43.7, 45.7, 47.7], charged: 51.7,
  r4: { ring: [65.7, 66.1], fly: [66.1, 67.3], cut: [66.1, 68.6], name: 67.5, num: 67.3 },
  giz: [58.5, 59.7], gizNote: 59.3, fangs: 68.5, scales: 70.1, burnish: [72.9, 73.3], shut: [73.3, 73.7], crystals: [74.9, 75.7], spark: [76.5, 76.9],
  arc: [81.3, 82.9], fork: [82.5, 83.1], arcWash: 83.3,
  heart: [84.9, 86.1], sheath: [89.3, 90.5], heartNote: 89.7,
  r5: { ring: [93.7, 94.1], fly: [94.1, 95.3], cut: [94.1, 96.5], name: 96.1, note: 96.9, num: 95.3 }, blue: 95.7, wax: [100.7, 101.5], rain: [104.9, 106.1], nat: 97.7,
  cart: [117.3, 118.1], cartTitle: 117.7, items: [121.3, 123.7, 127.3], cross: 121.9,
  red: 133.3, aim: 133.7, credits: 136.1,
};
const SLOT = { r3: [205, 1450], r4: [540, 1450], r5: [875, 1450] }, RR = 118;

export function makeFilm(lines, DUR) {
  // ------------------------------------------------------------------ the engraving
  const ink = new B.Ink();
  const dragon = buildCreature(ink, B.xf(270, 520, 0.44), { g: 'd', dragon: true, seed: 3, spacing: 3.0, wMax: 1.15, outlineW: 1.25 });
  const small = buildCreature(ink, B.xf(790, 520, 0.44), { g: 's', seed: 5, spacing: 3.0, wMax: 1.15, outlineW: 1.25 });
  const main = buildCreature(ink, B.xf(560, 1090, 0.92), { g: 'm', window: true, seed: 7, spacing: 3.4, wMax: 1.4, outlineW: 1.7 });
  const giz = buildGizzard(ink, B.xf(180, 905, 0.7));
  const mA = main.anchors, snout = mA.snout;
  const arc = buildArc(ink, [snout[0] + 4, snout[1] + 6], [778, 1292], 11);
  const emb = buildEmblems(ink, B.xf(540, 1738, 0.74));
  const natMite = buildTinyMite(ink, B.xf(985, 1658, 1));
  // the cartouche frame and the band rule
  ink.group('cart');
  B.outline(ink, [[110, 1668], [970, 1668], [970, 1814], [110, 1814]], { w: 1.8, light: [-0.6, -0.7], run: 0 });
  B.outline(ink, [[118, 1676], [962, 1676], [962, 1806], [118, 1806]], { w: 0.6, light: [-0.6, -0.7], run: 0 });
  for (const [x, sd] of [[110, -1], [970, 1]]) { const pts = []; for (let k = 0; k <= 20; k++) { const a = k / 20 * Math.PI * 1.6; pts.push([x + sd * (10 + 12 * Math.cos(a) * (1 - k / 30)), 1741 + 12 * Math.sin(a) * (1 - k / 30)]); } B.stroke(ink, pts, 1.2, { taper: 4 }); }
  ink.group('rule1'); B.stroke(ink, [[120, 686], [960, 686]], 0.9, { taper: 30 });

  // which groups belong to which figure, for scheduling
  const G = ink.groups(), of = p => G.filter(g => g.startsWith(p));
  const pick = (pref, suf) => G.filter(g => g.startsWith(pref) && g.endsWith(suf) && !g.endsWith('sc') && g !== pref + 'rn');
  // fig. 1a: the dragon is already two-thirds cut when the film starts
  ink.schedule(pick('d', 'ol'), -3.2, 1.0, { conc: 10 }); ink.schedule(pick('d', 'h1'), -2.2, 1.8, { conc: 60 });
  ink.schedule(pick('d', 'h2'), -1.0, 2.4, { conc: 60 }); ink.schedule(pick('d', 'h3'), -0.2, 2.8, { conc: 60 }); ink.schedule('dsc', 0.4, 2.6, { conc: 40 });
  ink.schedule('drn', ...T.runes, { conc: 3 });
  // fig. 1b: the small wyvern, cut while the camera looks at it
  const [s0, s1] = T.small;
  ink.schedule(pick('s', 'ol'), s0, s0 + 1.6, { conc: 8 }); ink.schedule(pick('s', 'h1'), s0 + 0.9, s0 + 2.9, { conc: 60 });
  ink.schedule(pick('s', 'h2'), s0 + 1.8, s0 + 3.5, { conc: 60 }); ink.schedule(pick('s', 'h3'), s0 + 2.4, s1, { conc: 60 }); ink.schedule('ssc', s0 + 2.6, s1, { conc: 40 });
  ink.schedule('rule1', ...T.rule, { conc: 1 });
  // fig. 2: the main figure in three passes
  const M = T.main;
  ink.schedule(pick('m', 'ol'), ...M.ol, { conc: 14 }); ink.schedule(pick('m', 'h1'), ...M.h1, { conc: 90 });
  ink.schedule(pick('m', 'h2'), ...M.h2, { conc: 90 }); ink.schedule(pick('m', 'h3'), ...M.h3, { conc: 90 }); ink.schedule('msc', ...M.sc, { conc: 60 });
  ink.schedule('win', ...T.win, { conc: 1.5 }); ink.schedule('rib', ...T.rib, { conc: 4 });
  ink.schedule('sacU', ...T.sacU, { conc: 12 }); ink.schedule('sacL', ...T.sacL, { conc: 12 });
  ink.schedule('heart', ...T.heart, { conc: 8 }); ink.schedule('sheath', ...T.sheath, { conc: 1 });
  ink.schedule('giz', ...T.giz, { conc: 6 });
  ink.schedule('arc', ...T.arc, { conc: 1 }); ink.schedule('fork', ...T.fork, { conc: 3 });
  ink.schedule('cart', ...T.cart, { conc: 4 });
  T.items.forEach((t, k) => { const e = 'e' + (k + 1); ink.schedule([e + 'ol'], t, t + 0.4, { conc: 4 }); ink.schedule([e + 'h1', e + 'h2', e + 'h3'], t + 0.2, t + 0.75, { conc: 30 }); });
  ink.schedule('e1x', T.cross, T.cross + 0.3, { conc: 2 });
  ink.schedule('nat', T.nat, T.nat + 0.5, { conc: 4 });
  ink.build();
  const frameInk = new B.Ink(); borderInk(frameInk, BORDER); frameInk.schedule('main', ...T.border, { conc: 1.2 }); frameInk.build();

  // ------------------------------------------------------------------ roundels
  const sac = buildSacDetail(), skull = buildSkullDetail(), tick = buildTickDetail();
  const sched = (art, [c0, c1], extra = {}) => {
    const D = c1 - c0, has = g => art.ink.groups().includes(g);
    if (has('ol')) art.ink.schedule('ol', c0, c0 + 0.5 * D, { conc: 12 });
    if (has('h1')) art.ink.schedule('h1', c0 + 0.2 * D, c0 + 0.78 * D, { conc: 60 });
    if (has('h2')) art.ink.schedule('h2', c0 + 0.42 * D, c0 + 0.92 * D, { conc: 60 });
    if (has('h3')) art.ink.schedule('h3', c0 + 0.5 * D, c1, { conc: 60 });
    if (has('rule')) art.ink.schedule('rule', c0 + 0.55 * D, c1, { conc: 30 });
    for (const [g, a, b, conc] of extra.more || []) if (has(g)) art.ink.schedule(g, a, b, { conc });
    art.ink.build();
  };
  sched(sac, T.r3.cut);
  sched(skull, T.r4.cut, { more: [['fang', T.r4.cut[0] + 1.2, T.r4.cut[1], 6], ['jool', T.r4.cut[0] + 0.6, T.r4.cut[0] + 1.6, 6], ['joh1', T.r4.cut[0] + 1.0, T.r4.cut[1], 40], ['joh2', T.r4.cut[0] + 1.3, T.r4.cut[1], 40], ['joh3', T.r4.cut[0] + 1.5, T.r4.cut[1], 40],
    ['jsol', ...T.shut, 6], ['jsh1', T.shut[0] + 0.1, T.shut[1] + 0.2, 40], ['jsh2', T.shut[0] + 0.15, T.shut[1] + 0.25, 40], ['jsh3', T.shut[0] + 0.2, T.shut[1] + 0.3, 40], ['cry', ...T.crystals, 4], ['spk', ...T.spark, 6]] });
  sched(tick, T.r5.cut, { more: [['mite', T.r5.cut[0] + 0.8, T.r5.cut[1], 8], ['wax', ...T.wax, 6], ['rain', ...T.rain, 10]] });
  // the open jaw is burnished out (drawn separately so it can fade) once the shut jaw is cut
  const jawOpen = new B.Ink(); jawOpen.S = skull.ink.S.filter(s => s.g.startsWith('jo')); jawOpen.build();
  skull.ink.S = skull.ink.S.filter(s => !s.g.startsWith('jo')); skull.ink.build();
  const R3 = { art: sac, slot: SLOT.r3, focus: { x: mA.window[0], y: mA.window[1], r: 52 }, t: T.r3, num: '3', name: 'FIG. 3 · THORACIC ELECTROPLAQUES', note: 'the Dynamo Sacs' };
  const R4 = { art: skull, slot: SLOT.r4, focus: { x: mA.head[0], y: mA.head[1], r: 46 }, t: T.r4, num: '4', name: 'FIG. 4 · THE JAWS', note: 'hollow copper-enamel fangs', noteT: T.fangs };
  const R5 = { art: tick, slot: SLOT.r5, focus: { x: mA.flank[0], y: mA.flank[1], r: 40 }, t: T.r5, num: '5', name: 'FIG. 5 · STATIC-TICK', note: 'metallic blue, at natural size' };
  const RS = [R3, R4, R5];
  function roundelAt(R, t) {
    const a = R.t; if (t < a.ring[0]) return null;
    const u = eio(seg(t, ...a.fly));
    return { x: lerp(R.focus.x, R.slot[0], u), y: lerp(R.focus.y, R.slot[1], u) - Math.sin(u * Math.PI) * 34, r: Math.exp(lerp(Math.log(R.focus.r), Math.log(RR), u)), ring: seg(t, ...a.ring), u };
  }

  // ------------------------------------------------------------------ hand colouring
  const wash = new Wash({ scale: 1.3 });
  wash.add({ path: dragon.regions.chest.path, polys: dragon.regions.chest.polys, color: '#c9973a', alpha: 0.85, t0: T.gold, dur: 1.4, seed: 1, spill: 2.5 });
  wash.add({ path: main.regions.body.path, polys: main.regions.body.polys, color: '#d29a3c', alpha: 0.42, t0: T.scales, dur: 1.8, seed: 2, origin: mA.chest });
  wash.add({ path: main.regions.head.path, polys: main.regions.head.polys, color: '#d29a3c', alpha: 0.42, t0: T.scales + 0.4, dur: 1.2, seed: 3 });
  wash.add({ path: arc.band.path, polys: arc.band.polys, color: '#efd46a', alpha: 0.8, t0: T.arcWash, dur: 1.0, seed: 4, origin: arc.main[0], spill: 2 });
  wash.add({ path: natMite.path, polys: natMite.polys, color: '#6f8ea3', alpha: 0.9, t0: T.nat + 0.4, dur: 0.6, seed: 5, spill: 1.5 });
  const sacWash = new Wash({ scale: 1.3 });
  for (const k of ['sacU', 'sacL']) sacWash.add({ path: main.regions[k].path, polys: main.regions[k].polys, color: '#d9902a', alpha: 0.85, t0: T.pulses[0], dur: 0.6, seed: k === 'sacU' ? 6 : 7, spill: 2.5 });
  const redWash = new Wash({ scale: 1.3 });
  redWash.add({ path: main.regions.sacL.path, polys: main.regions.sacL.polys, color: '#a8363a', alpha: 0.95, t0: T.red, dur: 1.4, seed: 8, spill: 2.5 });
  const r3Wash = new Wash({ scale: 0.6 }); for (const k of ['colU', 'colL']) r3Wash.add({ path: sac.regions[k].path, polys: sac.regions[k].polys, color: '#d9902a', alpha: 0.75, t0: T.pulses[0], dur: 0.6, seed: 11, spill: 10, offset: [6, 4] });
  const r4Wash = new Wash({ scale: 0.6 }); r4Wash.add({ path: skull.regions.fangs.path, polys: skull.regions.fangs.polys, color: '#b46a34', alpha: 0.8, t0: T.fangs, dur: 1.2, seed: 12, spill: 10, offset: [6, 4] });
  r4Wash.add({ path: skull.regions.crystals.path, polys: skull.regions.crystals.polys, color: '#e6c86e', alpha: 0.7, t0: T.spark[0], dur: 0.8, seed: 13, spill: 8, offset: [5, 3] });
  const r5Wash = new Wash({ scale: 0.6 }); r5Wash.add({ path: tick.regions.mites.path, polys: tick.regions.mites.polys, color: '#6f8ea3', alpha: 0.85, t0: T.blue, dur: 1.2, seed: 14, spill: 10, offset: [6, 4] });
  // the charge: three pulses on the downstrokes, then the sacs stay full
  const charge = t => { if (t < T.pulses[0]) return 0; let k = 0.22; for (const p of T.pulses) k = Math.max(k, Math.exp(-Math.pow((t - p - 0.25) / 0.45, 2))); return Math.max(k, ss(seg(t, T.charged, T.charged + 0.9))); };

  // ------------------------------------------------------------------ camera: a loupe over the sheet
  // key: { cx, cy } world point shown at the screen anchor (ax, ay) with zoom z
  const keys = [];
  const K = (t, cx, cy, z, ay = 820, e = eio) => keys.push([t, { cx, cy, z, ay }, e]);
  K(0, 270, 505, 2.25); K(5.5, 270, 505, 2.31); K(7.0, 800, 505, 2.25); K(11.3, 800, 505, 2.28);
  K(13.1, 540, 430, 1.15); K(19.3, 540, 430, 1.15); K(22.9, 540, 960, 1.0, 960); K(26.9, 540, 960, 1.0, 960);
  K(28.3, mA.window[0], mA.window[1], 2.5); K(35.6, mA.window[0], mA.window[1], 2.55); K(37.7, 400, 1290, 1.55); K(55.0, 400, 1290, 1.55);
  K(57.2, 240, 950, 2.2); K(64.4, 240, 950, 2.2); K(65.7, mA.head[0] - 30, mA.head[1], 2.3);
  K(67.9, 620, 1320, 1.75); K(69.4, 620, 1320, 1.75); K(70.4, 560, 1110, 1.05); K(72.2, 560, 1110, 1.05); K(72.8, 540, 1452, 2.4); K(79.4, 540, 1452, 2.4);
  K(80.6, snout[0] - 40, snout[1] + 20, 2.4);
  // 81.3–82.9: the camera follows the burin tip down the arc (see camAt)
  K(83.0, 800, 1280, 2.2); K(83.9, 850, 1110, 1.45); K(84.6, mA.heart[0], mA.heart[1], 2.8); K(91.9, mA.heart[0], mA.heart[1], 2.85);
  K(93.4, mA.flank[0], mA.flank[1], 2.6); K(95.9, 760, 1330, 1.5); K(97.4, 760, 1330, 1.5); K(98.4, 875, 1470, 2.25); K(108.4, 875, 1470, 2.3);
  K(110.4, 540, 470, 1.15); K(115.6, 540, 470, 1.18); K(116.6, 540, 1100, 1.0, 960); K(117.6, 540, 1740, 1.22, 1100); K(121.0, 540, 1740, 1.22, 1100); K(130.6, 540, 1745, 1.25, 1110); K(131.5, 520, 1110, 1.7); K(132.9, 520, 1110, 1.72); K(133.6, 520, 1110, 1.74);
  K(136.4, 540, 960, 1.0, 960); K(DUR + 1, 540, 958, 1.016, 960);
  const arcSh = ink.S.find(s => s.g === 'arc');
  const tipAt = t => { const f = (arcSh.n - 1) * clamp((t - arcSh.s0) / (arcSh.s1 - arcSh.s0)), j = Math.min(arcSh.n - 2, Math.floor(f)), u = f - j, xy = arcSh.xy; return [xy[2 * j] + (xy[2 * j + 2] - xy[2 * j]) * u, xy[2 * j + 1] + (xy[2 * j + 3] - xy[2 * j + 1]) * u]; };
  function camAt(t) {
    if (t >= T.arc[0] - 0.05 && t <= T.arc[1] + 0.1) { const p = tipAt(clamp(t, arcSh.s0, arcSh.s1)); const k = ss(seg(t, T.arc[0] - 0.05, T.arc[0] + 0.25)); const a = baseCam(T.arc[0] - 0.05); return { cx: lerp(a.cx, p[0], k), cy: lerp(a.cy, p[1], k), z: lerp(a.z, 2.2, seg(t, ...T.arc)), ay: 820 }; }
    if (t > T.arc[1] + 0.1 && t < 83.0) { const p = tipAt(arcSh.s1), u = eio(seg(t, T.arc[1] + 0.1, 83.0)); return { cx: lerp(p[0], 800, u), cy: lerp(p[1], 1280, u), z: 2.2, ay: 820 }; }
    return baseCam(t);
  }
  function baseCam(t) {
    let i = 0; while (i < keys.length - 1 && keys[i + 1][0] <= t) i++;
    const [ta, ca] = keys[i], nx = keys[i + 1]; if (!nx) return ca;
    const [tb, cb, e] = nx, u = e(seg(t, ta, tb));
    const za = Math.log(ca.z), zb = Math.log(cb.z), z = Math.exp(lerp(za, zb, u));
    const wa = 1 / ca.z, wb = 1 / cb.z, v = Math.abs(wb - wa) > 1e-6 ? (1 / z - wa) / (wb - wa) : u, k = Math.abs(za - zb) > 0.3 ? clamp(v) : u;
    return { cx: lerp(ca.cx, cb.cx, k), cy: lerp(ca.cy, cb.cy, k), z, ay: lerp(ca.ay, cb.ay, k) };
  }
  const applyCam = (ctx, c) => { ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.translate(540, c.ay); ctx.scale(c.z, c.z); ctx.translate(-c.cx, -c.cy); };
  const toScreen = (c, x, y) => [540 + (x - c.cx) * c.z, c.ay + (y - c.cy) * c.z];

  // ------------------------------------------------------------------ lettering (all of it, with its time), also used by TEXTS
  const L = [];
  const lab = (id, text, x, y, o, t0, kind = 'cut', dur = null) => L.push({ id, text, x, y, o, t0, kind, dur: dur ?? (kind === 'cut' ? Math.max(0.5, text.length * 0.045) : Math.max(0.8, text.length * 0.06)) });
  lab('series', 'A BESTIARY OF AZUL', BORDER[0] + 22, 132, { size: 15, weight: 500, track: 0.24, align: 'left' }, T.series);
  lab('plate', 'PLATE I.', BORDER[2] - 22, 132, { size: 20, weight: 700, track: 0.12, align: 'right' }, T.series + 0.3);
  lab('title', 'THE GOLD WYVERN.', 540, 200, { size: 44, weight: 700, track: 0.14 }, T.title, 'cut', 0.9);
  lab('latin', 'Dracunculus fulgur', 540, 242, { size: 26, italic: true, weight: 500 }, T.latin, 'cut', 1.0);
  lab('fig1', 'FIG. 1.', 540, 300, { size: 13, weight: 700, track: 0.2 }, T.fig1);
  lab('a', 'a. Draco verus', 270, 652, { size: 21, italic: true, weight: 500 }, T.labelA);
  lab('b', 'b. Dracunculus fulgur', 790, 652, { size: 21, italic: true, weight: 500 }, T.labelB);
  lab('mana', 'no mana pathways', 1000, 604, { size: 23, font: FONTS.script, align: 'right' }, T.mana, 'write');
  lab('fig2', 'FIG. 2.', BORDER[0] + 22, 722, { size: 13, weight: 700, track: 0.2, align: 'left' }, T.fig2);
  lab('giz', 'FIG. 2a · GIZZARD STONES', 180, 962, { size: 11.5, weight: 700, track: 0.1 }, T.gizNote);
  lab('giz2', 'copper ore, quartz', 180, 992, { size: 19, font: FONTS.script }, T.gizNote + 0.5, 'write');
  lab('giz3', 'and Sylvan iron', 180, 1016, { size: 19, font: FONTS.script }, T.gizNote + 1.2, 'write');
  lab('n3', '3', mA.window[0] - 70, mA.window[1] - 66, { size: 16, italic: true, weight: 500 }, T.r3.num);
  lab('n4', '4', mA.head[0] + 6, mA.head[1] - 46, { size: 16, italic: true, weight: 500 }, T.r4.num);
  lab('n5', '5', mA.flank[0] + 16, mA.flank[1] + 34, { size: 16, italic: true, weight: 500 }, T.r5.num);
  for (const R of RS) { lab('nm' + R.num, R.name, R.slot[0], R.slot[1] + RR + 34, { size: R.name.length > 24 ? 11 : 13, weight: 700, track: 0.1 }, R.t.name); lab('nt' + R.num, R.note, R.slot[0], R.slot[1] + RR + 64, { size: 21, font: FONTS.script }, R.noteT ?? R.t.note ?? R.t.name + 0.6, 'write'); }
  lab('heartN', 'triple sheaths of fat', 700, 1204, { size: 20, font: FONTS.script }, T.heartNote, 'write');
  lab('cart', 'GUILD SURVIVAL DOCTRINE.', 540, 1704, { size: 17, weight: 700, track: 0.16 }, T.cartTitle);
  ['I · drop all steel', 'II · flat on dry stone', 'III · wood to the underbelly'].forEach((s, k) => lab('item' + k, s, emb.centers[k][0], 1794, { size: 19, italic: true, weight: 500 }, T.items[k] + 0.2));
  lab('aim', 'aim here', 330, 1052, { size: 26, font: FONTS.script }, T.aim, 'write');
  lab('credL', 'Drawn from life.', BORDER[0] + 2, 1852, { size: 13, italic: true, weight: 500, align: 'left' }, T.credits);
  lab('credR', 'Plate I.', BORDER[2] - 2, 1852, { size: 13, italic: true, weight: 500, align: 'right' }, T.credits + 0.3);
  function drawLetters(ctx, t) {
    for (const l of L) {
      if (t < l.t0) continue; const p = seg(t, l.t0, l.t0 + l.dur);
      if (l.kind === 'write') writeScript(ctx, l.text, l.x, l.y, { ...l.o, p }); else engraveText(ctx, l.text, l.x, l.y, { ...l.o, p });
    }
  }
  const lineDot = (ctx, a, b, w = 0.8, p = 1) => { if (p <= 0) return; ctx.save(); ctx.strokeStyle = PAL.ink; ctx.lineWidth = w; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(...a); ctx.lineTo(a[0] + (b[0] - a[0]) * p, a[1] + (b[1] - a[1]) * p); ctx.stroke(); ctx.fillStyle = PAL.ink; ctx.beginPath(); ctx.arc(a[0], a[1], w * 1.8, 0, 7); ctx.fill(); ctx.restore(); };

  // ------------------------------------------------------------------ subtitles: one slip per spoken line
  const subs = lines.map((l, i) => ({ t0: l.t0 - 0.1, t1: i + 1 < lines.length ? lines[i + 1].t0 - 0.1 : l.t1 + 0.6, text: l.text }));
  function drawSubs(ctx, t) {
    const sb = subs.find(x => t >= x.t0 && t < x.t1); if (!sb) return;
    const a = Math.min(seg(t, sb.t0, sb.t0 + 0.2), 1 - seg(t, sb.t1 - 0.15, sb.t1));
    ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0);
    let size = 37, lines2 = wrapLines(ctx, sb.text, 900, { size, font: FONTS.script });
    while (lines2.length > 2 && size > 28) { size -= 1; lines2 = wrapLines(ctx, sb.text, 900, { size, font: FONTS.script }); }
    const lh = size * 1.14, hgt = lines2.length * lh + 26, wid = Math.max(...lines2.map(l => measure(ctx, l, { size, font: FONTS.script, weight: 400 }).tw)) + 70;
    const y1 = 1600, y0 = y1 - hgt, x0 = 540 - wid / 2;
    ctx.globalAlpha = a; ctx.shadowColor = 'rgba(60,40,20,0.3)'; ctx.shadowBlur = 14; ctx.shadowOffsetY = 4; ctx.fillStyle = '#f4eddb'; ctx.beginPath();
    const R = B.RNG(7); ctx.moveTo(x0, y0); for (let x = x0; x <= x0 + wid; x += 14) ctx.lineTo(x, y0 + (R() - 0.5) * 2.2); for (let y = y0; y <= y1; y += 12) ctx.lineTo(x0 + wid + (R() - 0.5) * 2, y); for (let x = x0 + wid; x >= x0; x -= 14) ctx.lineTo(x, y1 + (R() - 0.5) * 2.2); for (let y = y1; y >= y0; y -= 12) ctx.lineTo(x0 + (R() - 0.5) * 2, y); ctx.closePath(); ctx.fill();
    ctx.shadowColor = 'transparent';
    lines2.forEach((ln, i) => writeScript(ctx, ln, 540, y0 + 13 + lh * (i + 0.8), { size, color: '#2b1e14', p: 1, alpha: a }));
    ctx.restore();
  }

  // ------------------------------------------------------------------ render
  function drawRoundels(ctx, t, cam) {
    for (const R of RS) {
      const r = roundelAt(R, t); if (!r) continue;
      ctx.save(); ctx.beginPath(); ctx.arc(r.x, r.y, r.r, 0, Math.PI * 2); ctx.clip();
      const burn = ss(seg(t, R.t.ring[0] + 0.1, R.t.ring[1] + 0.25));
      ctx.globalAlpha = burn; ctx.fillStyle = PAL.paper; ctx.fillRect(r.x - r.r, r.y - r.r, r.r * 2, r.r * 2);
      ctx.globalCompositeOperation = 'multiply'; ctx.drawImage(paperTexture(W, H), 0, 0, W, H);
      ctx.globalAlpha = 0.55 * burn; ctx.fillStyle = PAL.plateTone; ctx.fillRect(r.x - r.r, r.y - r.r, r.r * 2, r.r * 2);
      ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
      ctx.translate(r.x, r.y); const k = r.r / 500; ctx.scale(k, k);
      const ws = Math.max(1, 0.55 / (k * cam.z)) ** 0.6;
      if (R === R3) { r3Wash.draw(ctx, t, { k: charge(t) }); }
      if (R === R4) r4Wash.draw(ctx, t);
      if (R === R5) r5Wash.draw(ctx, t);
      if (R === R4) { const fade = 1 - seg(t, ...T.burnish); if (fade > 0) { ctx.save(); ctx.globalAlpha = fade; jawOpen.draw(ctx, t, { wScale: ws }); ctx.restore(); } }
      R.art.ink.draw(ctx, t, { wScale: ws });
      ctx.restore();
      roundelFrame(ctx, r.x, r.y, r.r, { p: r.ring, w: 2.0 });
    }
  }
  function render(ctx, t) {
    ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over'; ctx.filter = 'none';
    const cam = camAt(t);
    applyCam(ctx, cam);
    drawBigSheet(ctx);
    wash.draw(ctx, t);
    sacWash.draw(ctx, t, { k: charge(t) });
    redWash.draw(ctx, t);
    ink.draw(ctx, t);
    frameInk.draw(ctx, t);
    // the heart note's leader and the "aim here" leader
    lineDot(ctx, [mA.heart[0] + 8, mA.heart[1] + 22], [700 - 6, 1182], 0.8, seg(t, T.heartNote - 0.3, T.heartNote));
    lineDot(ctx, [mA.sacL[0] - 108, mA.sacL[1] + 4], [372, 1040], 0.9, seg(t, T.aim - 0.3, T.aim));
    lineDot(ctx, [small.anchors.chest[0] - 4, small.anchors.chest[1] + 10], [918, 582], 0.7, seg(t, T.mana - 0.3, T.mana));
    drawRoundels(ctx, t, cam);
    drawLetters(ctx, t);
    // print finish: a warm vignette
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    const vg = ctx.createRadialGradient(540, 900, 700, 540, 960, 1250); vg.addColorStop(0, 'rgba(255,255,255,0)'); vg.addColorStop(1, 'rgba(120,86,46,0.2)');
    ctx.globalCompositeOperation = 'multiply'; ctx.fillStyle = vg; ctx.fillRect(0, 0, W, H); ctx.globalCompositeOperation = 'source-over';
    drawSubs(ctx, t);
  }

  // ------------------------------------------------------------------ texts on screen at t (for readcheck; subtitles are checked by the .srt)
  function texts(ctx, t) {
    const cam = camAt(t), out = [];
    for (const l of L) {
      if (t < l.t0) continue;
      const m = measure(ctx, l.text, { size: l.o.size, font: l.o.font || FONTS.roman, weight: l.o.weight || 400, italic: l.o.italic, track: l.o.track || 0 });
      const al = l.o.align || 'center', x0 = al === 'center' ? l.x - m.tw / 2 : al === 'right' ? l.x - m.tw : l.x;
      const a = toScreen(cam, x0, l.y - l.o.size * 0.8), b = toScreen(cam, x0 + m.tw, l.y + l.o.size * 0.25);
      out.push({ id: l.id, text: l.text, x0: a[0], y0: a[1], x1: b[0], y1: b[1], ...(/^n\d$|^cred|^fig|^series|^plate$/.test(l.id) ? { pass: true } : {}) });
    }
    return out;
  }

  // ------------------------------------------------------------------ events for the mixer
  const EV = [];
  const ev = (t, type, o = {}) => EV.push({ t: +t.toFixed(3), type, ...o });
  // burin cutting: one event per scheduled window of real cutting
  for (const [a, b] of [[0, 2.8], T.runes, T.small, T.rule, T.main.ol, [T.main.h1[0], T.main.sc[1]], T.win, T.rib, T.sacU, T.sacL, T.r3.cut, T.r4.cut, T.giz, T.shut, T.crystals, T.heart, T.r5.cut, T.wax, T.cart]) ev(a, 'burin', { until: b });
  ev(T.arc[0], 'arcburin', { until: T.arc[1] });
  for (const l of L) ev(l.t0, l.kind === 'write' ? 'quill' : 'letters', { dur: l.dur, n: l.text.length });
  for (const R of RS) { ev(R.t.ring[0], 'ring'); ev(R.t.fly[0], 'travel', { until: R.t.fly[1] }); ev(R.t.fly[1], 'land'); }
  ev(T.gold, 'drop'); ev(T.scales, 'drop'); ev(T.fangs, 'drop'); ev(T.arcWash, 'drop'); ev(T.blue, 'drop'); ev(T.red, 'drop');
  ev(T.gold, 'glass'); ev(T.thunder, 'thunder');
  T.pulses.forEach(p => { ev(p, 'wingbeat'); ev(p, 'hum', { dur: 1.4 }); }); ev(T.charged, 'hum', { dur: 2.6 }); ev(T.charged, 'cello');
  ev(T.giz[0], 'pebbles'); ev(T.burnish[0], 'burnish', { until: T.burnish[1] }); ev(T.shut[0], 'clack'); ev(T.crystals[0], 'crystal'); ev(T.spark[0], 'crackle', { dur: 0.5 });
  ev(T.arc[0], 'crackle', { dur: 2.2, big: 1 }); ev(T.arcWash, 'glass');
  for (let k = 0; k < 3; k++) ev(T.sheath[0] + k * 0.4, 'ting');
  ev(92.6, 'rain', { until: 108.6 }); ev(T.blue - 0.4, 'chitter', { until: 103.0 }); ev(T.blue, 'buzz', { until: 108.4 });
  ev(T.cart[0], 'press'); ev(T.items[0], 'steel'); ev(T.items[2], 'bowstring'); ev(T.red, 'lowcello'); ev(136.0, 'wind', { until: DUR });
  ev(80.0, 'silence', { until: 81.3 }); ev(131.9, 'silence', { until: T.red });
  EV.sort((a, b) => a.t - b.t);

  return { render, texts, DUR, EV, subs, cam: camAt };
}
