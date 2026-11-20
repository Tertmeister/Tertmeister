// page contract for core/render: window.READY, window.render(t), window.DUR, window.EV, window.TEXTS(t)
import { makeFilm } from './film.js';
const ctx = document.getElementById('c').getContext('2d');
await Promise.all(['500 40px "Bodoni Moda"', '700 40px "Bodoni Moda"', 'italic 500 40px "Bodoni Moda"', '400 40px "Pinyon Script"']
  .map(f => document.fonts.load(f, 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,:;·\'-')));
await document.fonts.ready;
const tl = await (await fetch('timeline.json')).json();
const film = makeFilm(tl.lines, tl.dur);
window.DUR = film.DUR; window.EV = film.EV;
window.render = t => film.render(ctx, t);
window.TEXTS = t => { film.render(ctx, t); return film.texts(ctx, t); };
const q = new URLSearchParams(location.search);
film.render(ctx, parseFloat(q.get('t') || '0'));
window.READY = true;
