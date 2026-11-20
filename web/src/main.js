import './style.css';
import maplibregl from 'maplibre-gl';
import { addBaseLayers, addSocietyLayers, BASE_MODES, createMap, OVERVIEW, setBaseMode, setHighlights, setSelected, setStates, startPulse } from './map.js';
import { searchSocieties } from './search.js';
import { createFeed } from './feed.js';
import { AMENITY_KEYS, DEFAULT_CRITERIA, NEAR, RANK, feetLabel, formatINR, matchSociety, matchUnit, priceFor, roomPasses } from './filters.js';

const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const mobile = matchMedia('(max-width: 700px)').matches;
const REPO = 'https://github.com/kairothq/flat-finder';
const params = new URLSearchParams(location.search);
const store = { // localStorage can be missing or blocked: never let it break the page
  get(k, d) { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch { return d; } },
  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* ignore */ } },
};

const KINDS = [
  ['apartment', 'Apartments', '<path d="M5 21V4h9v17M14 9h5v12M8 7h3M8 11h3M8 15h3"/>'],
  ['builder floor', 'Builder floors', '<path d="M4 21V8l8-5 8 5v13M4 13h16M4 17h16"/>'],
  ['villa', 'Villas', '<path d="M3 11l9-7 9 7M5 9.5V20h14V9.5M10 20v-5h4v5"/>'],
  ['plot', 'Plots', '<path d="M4 6l8-3 8 3v12l-8 3-8-3zM12 3v18M4 6l16 12"/>'],
];
const AMEN_LABELS = { squash: 'Squash', pool: 'Pool', gym: 'Gym', club: 'Clubhouse', tennis: 'Tennis', badminton: 'Badminton', jogging: 'Jogging track', kids: 'Kids play' };
const DIVY = { // Example Bengaluru search (3/4 BHK apartments with spacious bedrooms and squash court)
  ...structuredClone(DEFAULT_CRITERIA), kinds: ['apartment'], bhk: [3, 4], roomArea: 132, minSqft: 1650, amenities: ['squash'] }; // 11' x 12' = 132 sq ft
const STATE_LABEL = { match: 'Matches your search', likely: 'Likely match', probable: 'Probably fits (estimated)', unknown: 'Not checked yet', no: 'Does not match' };

let crit = structuredClone(DEFAULT_CRITERIA);
let baseMode = BASE_MODES.includes(params.get('map')) ? params.get('map') : 'streets';
let roomMode = 'off', areaUnit = 'sqft', sortBy = 'best';
let data, byId, map, feed, selected = null, states = new Map(), tourTimer = null, cityId = 'bangalore', details = null;
let myList = [], allAmenities = [];
const highlights = { glow: true, bounds: true, labels: true, ...store.get('ff-highlights', {}) };

async function boot() {
  const cities = await fetch('/data/cities.json').then((r) => r.json()).catch(() => ({ bangalore: { name: 'Bengaluru' } }));
  const defaultCity = cities.bangalore ? 'bangalore' : Object.keys(cities)[0] || 'bangalore';
  cityId = cities[params.get('city')] ? params.get('city') : defaultCity;
  const [city, shapes] = await Promise.all([
    fetch(`/data/${cityId}.json`).then((r) => r.json()),
    fetch(`/data/${cityId}-shapes.geojson`).then((r) => r.json()),
  ]);
  data = city;
  OVERVIEW.center = city.city.center;
  OVERVIEW.zoom = city.city.zoom || OVERVIEW.zoom;
  byId = new Map(city.societies.map((s) => [s.id, s]));
  $('city-pick').replaceChildren(...Object.entries(cities).map(([id, c]) => new Option(c.name, id, false, id === cityId)));
  $('city-pick').onchange = () => { location.search = `?city=${$('city-pick').value}`; };

  const freq = new Map();
  for (const s of city.societies) for (const a of s.amenities) freq.set(a, (freq.get(a) || 0) + 1);
  allAmenities = [...freq].sort((a, b) => b[1] - a[1]).map(([a, n]) => ({ name: a, n }));

  myList = params.get('list') ? params.get('list').split(',').filter((id) => byId.has(id)) : store.get(`ff-list-${cityId}`, []).filter((id) => byId.has(id));
  const c = city.counts, m = city.price_model || {}, rated = city.societies.filter((s) => s.rating).length;
  const reraName = { bangalore: 'Karnataka RERA', gurgaon: 'HRERA', mumbai: 'MahaRERA' }[cityId] || 'RERA';
  $('note').textContent = `${c.on_map.toLocaleString()} societies · ${(c.for_sale || 0).toLocaleString()} homes for sale, ${(c.for_rent || 0).toLocaleString()} for rent · ${c.verified} verified from brochures and ${reraName} plans`;
  $('about-prices').innerHTML = `Prices and rents are medians of live Magicbricks listings. <b>⚠</b> marks a listing price our checks think is a typo (far from the same home nearby, or rent and price that cannot both be right): it is shown as listed but not used for filters. <b>~</b> marks our estimate: rent is about ${((m.city_yield || 0.025) * 100).toFixed(1)}% of the price per year here (measured on ${m.pairs || 0} society and BHK pairs, correlation ${m.log_price_rent_correlation ?? 'n/a'}). "Probably fits" uses a cautious bedroom size estimated from unit size (${city.room_model?.n || 0} verified unit types). Resident ratings exist for ${rated.toLocaleString()} societies.`;
  $('dl-all').href = `/data/${cityId}-societies.csv`;
  $('dl-units').href = `/data/${cityId}-units.csv`;
  $('dl-results').onclick = exportResults;

  feed = createFeed($('feed'), $('log-mode'), { events: city.events, byId });
  buildFilters();
  buildSearch();
  buildList();
  buildControls();
  buildOnboarding();
  buildMobile();
  hintTilt();
  try {
    map = createMap('map', { mobile });
    window.__map = map; // handy for debugging in the console
  } catch {
    $('note').textContent = 'Your browser could not start WebGL, so the 3D map is off. Filters and results still work.';
    applyFilters();
    feed.ambient();
    return;
  }
  const points = { type: 'FeatureCollection', features: city.societies.map((s) => ({
    type: 'Feature', properties: { sid: s.id, name: s.name, show: 1 }, geometry: { type: 'Point', coordinates: [s.lng, s.lat] } })) };
  map.once('style.load', () => {
    addSocietyLayers(map, shapes, points);
    addBaseLayers(map);
    setBaseMode(map, baseMode);
    setHighlights(map, highlights);
    startPulse(map);
    // any hand on the map stops a running tour
    for (const ev of ['dragstart', 'wheel', 'touchstart']) map.on(ev, (e) => { if (e.originalEvent) stopTour(); });
    for (const l of ['bld', 'site-fill', 'glow']) {
      map.on('click', l, (e) => { stopTour(); openSociety(e.features[0].properties.sid); });
      map.on('mouseenter', l, () => (map.getCanvas().style.cursor = 'pointer'));
      map.on('mouseleave', l, () => (map.getCanvas().style.cursor = ''));
    }
    intro();
  });
}

function intro() {
  closeCard();
  if (['divy', 'blr', 'bangalore', 'bengaluru'].includes(params.get('preset'))) useCriteria(DIVY);
  if (params.get('open')) {
    map.jumpTo(OVERVIEW);
    applyFilters();
    setTimeout(() => openSociety(params.get('open')), 300);
    return;
  }
  if (mobile || params.has('nointro')) {
    if (!mobile) map.jumpTo(OVERVIEW);
    applyFilters(true);
    feed.ambient();
    return;
  }
  setStates(map, data.societies.map((s) => [s.id, 'no']));
  map.jumpTo({ center: [78.5, 22.5], zoom: 2.2, pitch: 0, bearing: 0 });
  setTimeout(() => {
    map.flyTo({ ...OVERVIEW, duration: 4250, curve: 1.6, essential: true });
    feed.sweep(data.societies, 4500);
  }, 250);
  map.once('moveend', () => applyFilters(true));
}

// ---------- filters ----------
function chip(label, on, onClick, cls = 'chip') {
  const b = document.createElement('button');
  b.className = cls + (on ? ' on' : '');
  b.innerHTML = label;
  b.onclick = onClick;
  return b;
}
const range = (a, b) => Array.from({ length: b - a + 1 }, (_, i) => a + i);
const toggle = (arr, v) => { const i = arr.indexOf(v); i >= 0 ? arr.splice(i, 1) : arr.push(v); };
// Two-handle slider: a low and a high end, with a value bubble on the handle being moved or hovered.
function dualRange(el, { min, max, step, fmt, onChange }) {
  el.classList.add('dual');
  el.innerHTML = '<div class="track"><i></i></div><input type="range" class="lo" aria-label="Lowest"><input type="range" class="hi" aria-label="Highest"><b class="bubble blo"></b><b class="bubble bhi"></b>';
  const lo = el.querySelector('.lo'), hi = el.querySelector('.hi'), fill = el.querySelector('.track i');
  const api = {
    cfg: { min, max, step, fmt },
    set(a, b) { lo.value = a; hi.value = b; api.paint(); },
    get() { return [+lo.value, +hi.value]; },
    reconfig(c) { Object.assign(api.cfg, c); for (const r of [lo, hi]) { r.min = api.cfg.min; r.max = api.cfg.max; r.step = api.cfg.step; } },
    paint() {
      const { min: a, max: b, fmt: f } = api.cfg;
      const pa = ((+lo.value - a) / (b - a)) * 100, pb = ((+hi.value - a) / (b - a)) * 100;
      fill.style.left = pa + '%'; fill.style.width = (pb - pa) + '%';
      const [l, h] = el.querySelectorAll('.bubble');
      l.style.left = pa + '%'; h.style.left = pb + '%';
      l.textContent = f(+lo.value, 'lo'); h.textContent = f(+hi.value, 'hi');
    },
  };
  api.reconfig({});
  const move = (which) => () => {
    if (+lo.value > +hi.value) (which === 'lo' ? lo : hi).value = which === 'lo' ? hi.value : lo.value;
    el.classList.add('active'); api.paint(); onChange(...api.get());
  };
  lo.oninput = move('lo'); hi.oninput = move('hi');
  for (const r of [lo, hi]) r.onpointerup = r.onblur = () => el.classList.remove('active');
  return api;
}

function useCriteria(c) {
  crit = structuredClone(c);
  roomMode = crit.roomArea ? 'area' : 'off';
  redrawFilters();
  applyFilters();
}

let redrawFilters = () => {};
let sizeSlider, priceSlider;
function buildFilters() {
  const amenList = () => {
    const q = $('amen-q').value.toLowerCase();
    $('amen-list').replaceChildren(...allAmenities.filter((a) => !q || a.name.toLowerCase().includes(q)).slice(0, 80).map((a) => {
      const key = 'n:' + a.name.toLowerCase();
      const l = document.createElement('label');
      l.innerHTML = `<input type="checkbox" ${crit.amenities.includes(key) ? 'checked' : ''}> ${esc(a.name)} <small>${a.n}</small>`;
      l.querySelector('input').onchange = () => { toggle(crit.amenities, key); redrawFilters(); applyFilters(); };
      return l;
    }));
  };
  sizeSlider = dualRange($('f-size'), { min: 0, max: 8000, step: 50, fmt: (v, end) => (end === 'hi' && v >= 8000 ? 'Any' : `${v.toLocaleString()} sq ft · ${Math.round(v / 9)} gaj`),
    onChange: (a, b) => { crit.minSqft = a; crit.maxSqft = b >= 8000 ? null : b; labels(); applyFilters(); } });
  priceSlider = dualRange($('f-price'), { min: 0, max: 20, step: 0.25, fmt: (v) => v, onChange: (a, b) => {
    const top = priceSlider.cfg.max, unit = crit.mode === 'rent' ? 1000 : 1e7;
    if (crit.mode === 'rent') { crit.minRent = a > 0 ? a * unit : null; crit.maxRent = b >= top ? null : b * unit; }
    else { crit.minPrice = a > 0 ? a * unit : null; crit.maxPrice = b >= top ? null : b * unit; }
    labels(); applyFilters();
  } });
  redrawFilters = () => {
    $('f-kind').replaceChildren(...KINDS.map(([k, l, icon]) => chip(`<svg viewBox="0 0 24 24">${icon}</svg><span>${l}</span>`, crit.kinds.includes(k), () => { toggle(crit.kinds, k); redrawFilters(); applyFilters(); }, 'tile')));
    $('f-bhk').replaceChildren(...[1, 2, 3, 4, 5].map((n) => chip(n === 5 ? '5+' : String(n), crit.bhk.includes(n), () => {
      toggle(crit.bhk, n); if (n === 5) toggle(crit.bhk, 6); redrawFilters(); applyFilters(); })));
    const custom = crit.amenities.filter((k) => k.startsWith('n:'));
    $('f-amen').replaceChildren(
      ...Object.keys(AMENITY_KEYS).map((k) => chip(AMEN_LABELS[k], crit.amenities.includes(k), () => { toggle(crit.amenities, k); redrawFilters(); applyFilters(); })),
      ...custom.map((k) => chip(`${esc(allAmenities.find((a) => a.name.toLowerCase() === k.slice(2))?.name || k.slice(2))} ×`, true, () => { toggle(crit.amenities, k); redrawFilters(); applyFilters(); })),
      chip($('amen-more').hidden ? `More (${allAmenities.length})` : 'Fewer', false, () => { $('amen-more').hidden = !$('amen-more').hidden; redrawFilters(); if (!$('amen-more').hidden) { amenList(); $('amen-q').focus(); } }, 'chip more-chip'));
    $('f-near').replaceChildren(...Object.entries(NEAR).map(([k, n]) => chip(`${n.label} <small>${n.m >= 1000 ? n.m / 1000 + ' km' : n.m + ' m'}</small>`, crit.near.includes(k), () => { toggle(crit.near, k); redrawFilters(); applyFilters(); })));
    document.querySelectorAll('#f-mode button').forEach((b) => b.classList.toggle('on', b.dataset.m === crit.mode));
    document.querySelectorAll('#f-room-mode button').forEach((b) => b.classList.toggle('on', b.dataset.r === roomMode));
    document.querySelectorAll('#f-area-unit button').forEach((b) => b.classList.toggle('on', b.dataset.u === areaUnit));
    $('f-area').hidden = roomMode !== 'area';
    $('room-hint').hidden = roomMode === 'off';
    $('f-est').parentElement.hidden = roomMode === 'off';
    $('f-est').checked = crit.estimates !== false;
    if (crit.roomArea) $('f-area-range').value = crit.roomArea / 9;
    sizeSlider.set(crit.minSqft || 0, crit.maxSqft ?? 8000);
    const rent = crit.mode === 'rent';
    priceSlider.reconfig(rent ? { min: 0, max: 500, step: 5, fmt: (v, end) => (end === 'hi' && v >= 500 ? 'Any' : v ? `${formatINR(v * 1000)}/mo` : '₹0') }
      : { min: 0, max: 20, step: 0.25, fmt: (v, end) => (end === 'hi' && v >= 20 ? 'Any' : v ? formatINR(v * 1e7) : '₹0') });
    priceSlider.set(rent ? (crit.minRent || 0) / 1000 : (crit.minPrice || 0) / 1e7, rent ? (crit.maxRent ? crit.maxRent / 1000 : 500) : (crit.maxPrice ? crit.maxPrice / 1e7 : 20));
    $('f-ready').checked = crit.ready;
    $('f-only').checked = !!crit.only;
    if (!$('amen-more').hidden) amenList();
    labels();
  };
  function readRoom() {
    crit.room = null;
    crit.roomArea = roomMode === 'area' ? Math.round(+$('f-area-range').value * 9) : null;
    labels();
    applyFilters();
  }
  function labels() {
    const range = (a, b, f) => (a && b ? `${f(a)} to ${f(b)}` : a ? `from ${f(a)}` : b ? `up to ${f(b)}` : 'Any');
    $('v-size').textContent = range(crit.minSqft, crit.maxSqft, (v) => `${v.toLocaleString()} sq ft`);
    const rent = crit.mode === 'rent';
    $('v-price').textContent = range(rent ? crit.minRent : crit.minPrice, rent ? crit.maxRent : crit.maxPrice, (v) => formatINR(v) + (rent ? '/mo' : ''));
    $('l-price').textContent = rent ? 'Monthly rent' : 'Budget';
    const g = +$('f-area-range').value;
    $('v-area').textContent = areaUnit === 'gaj' ? `at least ${g.toFixed(2).replace(/\.?0+$/, '')} gaj (${Math.round(g * 9)} sq ft)` : `at least ${Math.round(g * 9)} sq ft (${g.toFixed(1)} gaj)`;
    $('room-hint').textContent = 'Every bedroom must be at least this big (length × width).';
  }
  document.querySelectorAll('#f-mode button').forEach((b) => (b.onclick = () => { crit.mode = b.dataset.m; redrawFilters(); applyFilters(); }));
  document.querySelectorAll('#f-room-mode button').forEach((b) => (b.onclick = () => { roomMode = b.dataset.r; redrawFilters(); readRoom(); }));
  document.querySelectorAll('#f-area-unit button').forEach((b) => (b.onclick = () => { areaUnit = b.dataset.u; redrawFilters(); }));
  $('f-area-range').oninput = readRoom;
  $('f-est').onchange = () => { crit.estimates = $('f-est').checked; applyFilters(); };
  $('amen-q').oninput = amenList;
  $('f-ready').onchange = () => { crit.ready = $('f-ready').checked; applyFilters(); };
  $('f-sort').onchange = () => { sortBy = $('f-sort').value; renderResults(); };
  $('preset-divy').onclick = () => useCriteria(DIVY);
  $('btn-replay').onclick = intro;
  $('btn-tour').onclick = tour;
  $('btn-hide').onclick = () => document.body.classList.toggle('bare');
  $('btn-log').onclick = () => toggleLog();
  $('log-close').onclick = () => toggleLog(false);
  redrawFilters();
}

function toggleLog(show = document.body.classList.contains('nolog')) {
  document.body.classList.toggle('nolog', !show);
  $('btn-log').classList.toggle('off', !show);
  store.set('ff-log', show);
}

// ---------- apply and results ----------
let waveTimer = null;
function applyFilters(wave = false) {
  const next = new Map(data.societies.map((s) => [s.id, matchSociety(s, crit)]));
  const changed = [...next].filter(([id, st]) => states.get(id) !== st);
  states = next;
  clearInterval(waveTimer);
  if (wave && map) {
    const c = OVERVIEW.center;
    changed.sort((a, b) => dist(byId.get(a[0]), c) - dist(byId.get(b[0]), c));
    let i = 0;
    const per = Math.ceil(changed.length / 30);
    waveTimer = setInterval(() => { setStates(map, changed.slice(i, i + per)); i += per; if (i >= changed.length) clearInterval(waveTimer); }, 50);
  } else if (map?.getSource?.('shapes')) setStates(map, changed);
  renderResults();
  if (selected) renderCard(byId.get(selected));
}
const dist = (s, c) => (s.lng - c[0]) ** 2 + (s.lat - c[1]) ** 2;

function sorted(list) {
  const price = (s) => priceFor(s, crit.mode, crit.bhk)?.value ?? Infinity;
  const by = {
    best: (a, b) => RANK[states.get(b.id)] - RANK[states.get(a.id)] || b.verified - a.verified || (b.score || 0) - (a.score || 0),
    score: (a, b) => (b.score || 0) - (a.score || 0),
    rating: (a, b) => (b.rating || 0) - (a.rating || 0) || (b.rating_count || 0) - (a.rating_count || 0),
    price: (a, b) => price(a) - price(b),
    listings: (a, b) => ((b.sale_count || 0) + (b.rent_count || 0)) - ((a.sale_count || 0) + (a.rent_count || 0)),
  }[sortBy];
  return list.sort(by);
}

function ranked() {
  return sorted(data.societies.filter((s) => ['match', 'likely', 'probable'].includes(states.get(s.id))));
}

const shown = { match: 25, likely: 25, probable: 25 };
function renderResults() {
  const counts = { match: 0, likely: 0, probable: 0, unknown: 0 };
  for (const st of states.values()) if (st in counts) counts[st]++;
  animateNumber($('count'), counts.match + counts.likely + counts.probable);
  const rooms = crit.room || crit.roomArea;
  const bits = [];
  if (rooms) bits.push(`${counts.match} verified`, `${counts.likely} likely`, `${counts.probable} probably fit`);
  if (counts.unknown) bits.push(`${counts.unknown.toLocaleString()} not checked yet`);
  $('count-sub').textContent = bits.join(' · ');
  $('v-list').textContent = myList.length ? `${myList.length} saved` : 'empty';
  const groups = rooms
    ? [['match', 'Rooms read from floor plans: every bedroom passes'], ['likely', 'Likely: rooms read so far pass'], ['probable', 'Probably fits: estimated from unit size, plans not read yet']]
    : [['match', null]];
  const all = ranked();
  $('results').replaceChildren(...groups.flatMap(([st, title]) => {
    const list = rooms ? all.filter((s) => states.get(s.id) === st) : all;
    if (!list.length) return [];
    const out = [];
    if (title) { const h = document.createElement('div'); h.className = `group ${st}`; h.textContent = `${title} (${list.length})`; out.push(h); }
    const ol = document.createElement('ol');
    ol.className = 'results';
    ol.replaceChildren(...list.slice(0, shown[st]).map(resultItem));
    out.push(ol);
    if (list.length > shown[st]) out.push(chip(`Show more (${list.length - shown[st]} left)`, false, () => { shown[st] += 50; renderResults(); }, 'linkbtn'));
    return out;
  }));
}

function resultItem(s) {
  const li = document.createElement('li');
  const st = states.get(s.id);
  const p = priceFor(s, crit.mode, crit.bhk);
  const money = p ? `${p.estimated ? '~' : ''}${formatINR(p.value)}${crit.mode === 'rent' ? '/mo' : ''}` : '';
  const how = s.verified ? ' · checked by hand' : s.ai_read ? ' · AI-read plans' : '';
  li.innerHTML = `<span class="nm">${myList.includes(s.id) ? '★ ' : ''}${esc(s.name)}<small>${esc(s.locality || '')}${how}</small></span>
    <span class="tag ${st}">${money}${s.score != null ? `<small>score ${s.score}</small>` : ''}</span>`;
  li.onclick = () => { stopTour(); openSociety(s.id); };
  return li;
}

function animateNumber(el, to) {
  const from = +el.textContent.replace(/,/g, '') || 0;
  const t0 = performance.now();
  const step = (t) => {
    const k = Math.max(0, Math.min(1, (t - t0) / 700));
    el.textContent = Math.round(from + (to - from) * (1 - (1 - k) ** 3)).toLocaleString();
    if (k < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

// ---------- society details (right side on desktop) ----------
function openSociety(sid, { fly = true } = {}) {
  const s = byId.get(sid);
  if (!s) return;
  if (map) setSelected(map, sid, selected);
  selected = sid;
  if (fly && map) map.flyTo({ center: [s.lng, s.lat], zoom: mobile ? 15.4 : 16.2, pitch: is3d ? 55 : 0, bearing: 0, duration: 2600, essential: true,
    offset: mobile ? [0, -80] : [-180, 0] });
  document.body.classList.add('has-card');
  if (mobile) showMobile('society');
  renderCard(s);
  feed.play(sid);
}

function closeCard() {
  $('card').hidden = true;
  document.body.classList.remove('has-card');
  if (mobile) showMobile('search');
  if (map && selected) setSelected(map, null, selected);
  selected = null;
  feed?.ambient();
}

const metres = (m) => (m >= 1000 ? `${(m / 1000).toFixed(1)} km` : `${Math.round(m / 10) * 10} m`);

function renderCard(s) {
  const st = states.get(s.id);
  const rooms = crit.room || crit.roomArea;
  const unitRows = s.unit_types.filter((u) => !crit.bhk.length || crit.bhk.includes(u.bhk)).slice(0, 14).map((u) => {
    const v = rooms || crit.minSqft ? matchUnit(u, crit) : null;
    const bad = (r) => (crit.roomArea ? r[0] * r[1] < crit.roomArea : crit.room && !roomPasses(r, crit.room));
    const ai = u.ai && [u.ai.min_short != null && `narrowest bedroom ${feetLabel(u.ai.min_short)}`, u.ai.long_lb != null && `every bedroom at least ${feetLabel(u.ai.long_lb)} long`,
      u.ai.area_lb != null && `at least ${u.ai.area_lb} sq ft`].filter(Boolean).join(', ');
    const roomText = u.ai ? `${ai || 'partly read'} <span class="fine">(AI estimate from the plan, not confirmed)</span>` : u.bedrooms?.length
      ? u.bedrooms.map((r) => `<span class="${bad(r) ? 'fail' : ''}">${feetLabel(r[0])} × ${feetLabel(r[1])}</span>`).join(', ') + (u.rooms_complete ? '' : ' <span class="fine">(not all rooms read)</span>')
        + (u.confidence === 'ocr' ? ` <span class="fine">(read from the plan by ${esc(u.checked_by || 'OCR')})</span>` : '')
      : u.est_short ? `<span class="fine">plans not read · estimated at least ${feetLabel(u.est_short)} wide, ~${u.est_area} sq ft</span>` : '<span class="fine">room sizes not read yet</span>';
    const srcLabel = u.confidence === 'ai' || u.confidence === 'ocr' ? 'plan image' : u.confidence === 'primary' ? `plan${u.page ? ' p.' + esc(u.page) : ''}` : `portal${u.page ? ' p.' + esc(u.page) : ''}`;
    const src = u.source ? `<a href="${esc(u.source)}" target="_blank" rel="noopener">${srcLabel}</a>` : '';
    const size = u.super_sqft ? `${u.super_sqft.toLocaleString()} super` : u.carpet_sqft ? `${u.carpet_sqft.toLocaleString()} carpet` : u.size_sqft ? `${u.size_sqft.toLocaleString()}` : '';
    const vl = { unknown: 'unread', probable: 'probably' }[v] || v;
    return `<tr><td>${esc(u.label)}<div class="fine">${size ? size + ' sq ft' : ''}</div></td><td>${roomText}</td><td>${v ? `<span class="badge ${v}">${vl}</span>` : ''}</td><td>${src}</td></tr>`;
  }).join('');
  const cell = (real, est, rent, flag, rangeFlag) => real
    ? `<b${flag ? ` class="flagged" title="${esc(flag)}"` : ''}>${formatINR(real.median)}${rent ? '/mo' : ''}${flag ? ' ⚠' : ''}</b><div class="fine">${real.n > 1 ? `${formatINR(real.min)} to ${formatINR(real.max)} · ` : ''}${real.n} listing${real.n > 1 ? 's' : ''}${rangeFlag ? ` · <span title="${esc(rangeFlag)}">⚠ odd listings</span>` : ''}</div>${flag ? `<div class="fine flag-note">⚠ Our check: ${esc(flag)}.${est ? ` Our estimate: ~${formatINR(est.value)}${rent ? '/mo' : ''}.` : ''}</div>` : ''}`
    : est ? `<b class="est" title="${esc(est.basis)}">~${formatINR(est.value)}${rent ? '/mo' : ''}</b><div class="fine">our estimate: ${esc(est.basis)}</div>` : '<span class="fine">no data</span>';
  const priceRows = Object.entries(s.prices || {}).filter(([b]) => !crit.bhk.length || crit.bhk.includes(+b)).map(([b, p]) =>
    `<tr><td>${b} BHK${p.psf ? `<div class="fine">₹${p.psf.toLocaleString()}/sq ft</div>` : ''}</td><td>${cell(p.buy, p.buy_est, false, p.flags?.buy, p.flags?.buy_range)}</td><td>${cell(p.rent, p.rent_est, true, p.flags?.rent, p.flags?.rent_range)}</td></tr>`).join('');
  const d = details?.[s.id];
  const want = new Set(crit.amenities.flatMap((k) => AMENITY_KEYS[k] || [k.slice(2)]));
  const facts = Object.entries(s.amen_facts || {}).map(([k, f]) => `<span class="hit">${esc(AMEN_LABELS[k] || k)}: ${esc(f.value)} (<a href="${esc(f.source)}" target="_blank" rel="noopener">p.${esc(f.page)}</a>)</span>`).join('');
  const amen = s.amenities.map((a) => `<span class="${[...want].some((w) => a.toLowerCase().includes(w)) ? 'hit' : ''}">${esc(a)}</span>`).join('');
  const plans = Object.entries(s.plan_links || {}).map(([b, urls]) => urls.slice(0, 2).map((u, i) => `<a href="${esc(u)}" target="_blank" rel="noopener">${b} BHK plan${urls.length > 1 ? ' ' + (i + 1) : ''}</a>`).join(' ')).join(' ');
  const issue = `${REPO}/issues/new?title=${encodeURIComponent('Research: ' + s.name)}&body=${encodeURIComponent(`Please verify room sizes and amenities for ${s.name} (${s.locality || ''}).\n\nPortal page: ${s.url}\n${s.brochure_url ? 'Brochure: ' + s.brochure_url : ''}`)}`;
  const facts2 = [s.towers && `${s.towers} towers`, s.units && `${Number(s.units).toLocaleString()} units`, s.acres && `${s.acres} acres`, s.status, s.possession && `possession ${s.possession}`].filter(Boolean).join(' · ');
  const counts = (s.sale_count || s.rent_count) ? `${(s.sale_count || 0).toLocaleString()} for sale · ${(s.rent_count || 0).toLocaleString()} for rent now` : 'No live listings';
  const parts = s.score_parts || {};
  const score = s.score != null ? `<div class="score"><div class="big">${s.score}<small>/10</small></div><div class="parts">
      ${parts.residents != null ? `<span>Residents <b>${parts.residents}</b></span>` : '<span class="fine">No resident ratings yet</span>'}<span>Nearby <b>${parts.nearby}</b></span><span>Amenities <b>${parts.amenities}</b></span>
      <span class="fine">Flat Finder score: residents' rating 50%, what is nearby 30%, amenities 20%</span></div></div>` : '';
  const near = s.nearby || {};
  const nearRows = [['park', 'Park'], ['metro', 'Metro'], ['rail', 'Rail station'], ['school', 'School'], ['hospital', 'Hospital'], ['shopping', 'Mall or supermarket']]
    .filter(([k]) => near[k]).map(([k, l]) => `<div><span>${l}</span><b>${metres(near[k].m)}</b><small>${esc(near[k].name || '')}${near[k].n > 1 ? ` · ${near[k].n} within 1 km` : ''}</small></div>`).join('');
  const ratingBars = d && Object.keys(d.ratings || {}).length ? `<div class="bars">${Object.entries(d.ratings).map(([k, v]) => `<div><span>${esc(k)}</span><i style="--w:${(v / 5) * 100}%"></i><b>${v}</b></div>`).join('')}</div>` : '';
  const reviews = d?.reviews?.length ? `<div class="reviews">${d.reviews.slice(0, 3).map((r) => `<blockquote>${esc(r.text)}<cite>${esc(r.by || 'Resident')}${r.date ? ' · ' + esc(r.date) : ''}</cite></blockquote>`).join('')}</div>` : '';
  const trend = d?.trend?.length > 1 ? sparkline(d.trend) : '';
  const about = d?.description ? `<details><summary>About this project</summary><p class="fine">${esc(d.description)}</p></details>` : '';
  const inList = myList.includes(s.id);
  const photos = d?.images?.length ? `<div class="photos">${d.images.map((im) => `<a href="${esc(im.full)}" target="_blank" rel="noopener"><img src="${esc(im.thumb)}" alt="" loading="lazy" referrerpolicy="no-referrer" onerror="this.parentElement.remove()"></a>`).join('')}</div><div class="fine">Photos: Magicbricks, opens full size</div>` : '';
  $('card').innerHTML = `
    <div class="card-head">
      <div><span class="badge ${st}">${STATE_LABEL[st]}</span> ${s.verified ? '<span class="badge match">checked by hand</span>' : ''}${s.ai_read ? '<span class="badge likely">AI-read plans</span>' : ''}</div>
      <div class="row-gap"><button class="iconbtn star ${inList ? 'on' : ''}" id="c-star" title="${inList ? 'Remove from my list' : 'Add to my list'}">${inList ? '★' : '☆'}</button><button class="iconbtn" id="c-close" aria-label="Close">×</button></div>
    </div>
    ${photos}
    <h2>${esc(s.name)}</h2>
    <div class="meta">${esc(s.developer || '')}${s.locality ? ' · ' + esc(s.locality) : ''} · ${esc(s.config_text || s.kind)}${s.kind_inferred ? ' <span class="fine">(type inferred from name)</span>' : ''}</div>
    <div class="meta">${esc(facts2)}</div>
    ${score}
    <div class="meta">${s.rating ? `<span class="stars">★ ${s.rating.toFixed(1)}</span> ${s.rating_count || 0} resident ratings · ${s.review_count || 0} reviews · ` : ''}${counts}</div>
    ${s.note ? `<div class="fine">${esc(s.note)}</div>` : ''}
    <h4>Buy and rent</h4>
    ${priceRows ? `<table class="prices"><tr><th>Home</th><th>Buy</th><th>Rent</th></tr>${priceRows}</table>` : '<div class="fine">No price data.</div>'}
    ${trend}
    <h4>Bedrooms</h4>
    ${unitRows ? `<table><tr><th>Unit</th><th>Bedrooms</th><th></th><th>Source</th></tr>${unitRows}</table>` : '<div class="fine">No unit types listed.</div>'}
    ${nearRows ? `<h4>Nearby</h4><div class="near">${nearRows}</div>` : ''}
    ${ratingBars ? `<h4>What residents rate</h4>${ratingBars}` : ''}${reviews}
    ${facts || amen ? `<h4>Amenities (${s.amenities.length})</h4><div class="amen">${facts}${amen}</div>` : ''}
    ${about}
    <div class="links">
      <a class="btnlink" href="${esc(s.gmaps)}" target="_blank" rel="noopener">Google Maps and reviews</a>
      <a class="btnlink" href="https://www.google.com/maps/dir/?api=1&destination=${s.lat},${s.lng}" target="_blank" rel="noopener">Directions</a>
      <a href="${esc(s.url)}" target="_blank" rel="noopener">Magicbricks page</a>
      ${s.brochure_url ? `<a href="${esc(s.brochure_url)}" target="_blank" rel="noopener">Brochure</a>` : ''}
      ${plans}
      ${!s.verified ? `<a href="${esc(issue)}" target="_blank" rel="noopener">Request a room check →</a>` : ''}
    </div>
    <div class="fine">${s.rera_id ? 'RERA ' + esc(s.rera_id) + ' · ' : ''}${s.shape === 'osm' ? 'Buildings from OpenStreetMap' : s.shape === 'osm-site' ? 'Boundary from OpenStreetMap, towers drawn approximately' : 'Approximate shape: towers drawn from the listed tower count'}</div>`;
  $('card').hidden = false;
  $('c-close').onclick = () => { stopTour(); closeCard(); };
  $('c-star').onclick = () => { toggle(myList, s.id); saveList(); renderCard(s); renderResults(); };
  if (!details) loadDetails().then(() => { if (selected === s.id) renderCard(s); });
}

let detailsPromise = null;
function loadDetails() {
  detailsPromise ||= fetch(`/data/${cityId}-details.json`).then((r) => r.json()).then((d) => (details = d)).catch(() => (details = {}));
  return detailsPromise;
}

function sparkline(trend) {
  const vals = trend.map((t) => t[1]), lo = Math.min(...vals), hi = Math.max(...vals), w = 200, h = 36;
  const pts = vals.map((v, i) => `${(i / (vals.length - 1)) * w},${h - 4 - ((v - lo) / (hi - lo || 1)) * (h - 8)}`).join(' ');
  const ch = ((vals.at(-1) - vals[0]) / vals[0]) * 100;
  return `<div class="trend"><svg viewBox="0 0 ${w} ${h}" width="${w}" height="${h}" aria-hidden="true"><polyline points="${pts}" fill="none" stroke="currentColor" stroke-width="2"/></svg>
    <span class="fine">Average price per sq ft ${trend[0][0]} to ${trend.at(-1)[0]}: ₹${vals[0].toLocaleString()} to ₹${vals.at(-1).toLocaleString()} (${ch >= 0 ? '+' : ''}${ch.toFixed(0)}%)</span></div>`;
}

// ---------- phone: one bottom sheet, two tabs (search | society) ----------
function showMobile(tab) {
  document.body.classList.toggle('m-society', tab === 'society');
  document.body.classList.remove('m-collapsed');
  document.querySelectorAll('#mtabs [data-t]').forEach((b) => b.classList.toggle('on', b.dataset.t === tab));
  $('mt-society').disabled = !selected && tab !== 'society';
}

function buildMobile() {
  document.querySelectorAll('#mtabs [data-t]').forEach((b) => (b.onclick = () => showMobile(b.dataset.t)));
  const collapse = () => {
    const c = document.body.classList.toggle('m-collapsed');
    $('m-collapse').textContent = c ? '⌃' : '⌄';
    $('btn-mhide').textContent = c ? 'Show panel' : 'Hide panel';
  };
  $('m-collapse').onclick = collapse;
  $('btn-mhide').onclick = collapse;
}

// ---------- first visit: point out the 2D / 3D switch ----------
function hintTilt() {
  if (store.get('ff-tilt-seen', false)) return;
  const b = $('ctl-tilt');
  b.classList.add('pulse');
  b.dataset.tip = 'Flat map or 3D';
  const done = () => { b.classList.remove('pulse'); store.set('ff-tilt-seen', true); };
  b.addEventListener('click', done, { once: true });
  setTimeout(done, 15000);
}

// ---------- my list ----------
function saveList() {
  store.set(`ff-list-${cityId}`, myList);
  if (crit.only) { crit.only = [...myList]; applyFilters(); }
}

function buildList() {
  $('f-only').onchange = () => {
    if ($('f-only').checked && !myList.length) { $('f-only').checked = false; toast('Your list is empty. Star a society or paste names first.'); return; }
    crit.only = $('f-only').checked ? [...myList] : null;
    applyFilters();
  };
  $('btn-paste').onclick = () => { $('paste').hidden = false; $('paste-result').textContent = ''; $('paste-text').focus(); };
  $('paste-cancel').onclick = () => ($('paste').hidden = true);
  $('paste-clear').onclick = () => { myList = []; saveList(); crit.only = null; redrawFilters(); applyFilters(); $('paste-result').textContent = 'List cleared.'; };
  $('paste-add').onclick = () => {
    const names = $('paste-text').value.split(/[\n,;]+/).map((t) => t.trim()).filter(Boolean);
    const found = [], missed = [];
    for (const n of names) {
      const hit = searchSocieties(data.societies, n, 1)[0];
      if (hit) { if (!myList.includes(hit.id)) myList.push(hit.id); found.push(`${n} → ${hit.name}`); } else missed.push(n);
    }
    saveList();
    crit.only = myList.length ? [...myList] : null;
    redrawFilters();
    applyFilters();
    $('paste-result').innerHTML = `${found.length ? `<b>Added ${found.length}:</b> ${found.map(esc).join(' · ')}` : ''}${missed.length ? `<br><b>Not found:</b> ${missed.map(esc).join(', ')}` : ''}`;
    if (map && myList.length) {
      const pts = myList.map((id) => byId.get(id));
      const b = pts.reduce((bb, s) => bb.extend([s.lng, s.lat]), new maplibregl.LngLatBounds([pts[0].lng, pts[0].lat], [pts[0].lng, pts[0].lat]));
      map.fitBounds(b, { padding: { top: 80, bottom: 80, left: mobile ? 40 : 380, right: mobile ? 40 : 460 }, maxZoom: 15, bearing: 0 });
    }
  };
  $('btn-share').onclick = async () => {
    if (!myList.length) { toast('Your list is empty.'); return; }
    const url = `${location.origin}/?city=${cityId}&list=${myList.join(',')}`;
    try { await navigator.clipboard.writeText(url); toast('Link to your list copied.'); } catch { prompt('Copy this link', url); }
  };
  if (params.get('list') && myList.length) crit.only = [...myList];
}

function toast(msg) {
  $('toast').textContent = msg;
  $('toast').hidden = false;
  clearTimeout(toast.t);
  toast.t = setTimeout(() => ($('toast').hidden = true), 2600);
}

// ---------- CSV export of the current results ----------
function exportResults() {
  const cols = ['name', 'locality', 'verdict', 'type', crit.mode === 'rent' ? 'rent_from' : 'price_from', 'estimated', 'for_sale', 'for_rent', 'flat_finder_score', 'resident_rating', 'towers', 'units', 'nearest_park_m', 'nearest_metro_m', 'magicbricks_url', 'google_maps_url', 'flat_finder_url'];
  const q = (v) => (v == null ? '' : /[",\n]/.test(String(v)) ? `"${String(v).replace(/"/g, '""')}"` : String(v));
  const rows = ranked().map((s) => {
    const p = priceFor(s, crit.mode, crit.bhk);
    return [s.name, s.locality, states.get(s.id), s.kind, p?.value, p ? p.estimated : '', s.sale_count, s.rent_count, s.score, s.rating, s.towers, s.units,
      s.nearby?.park?.m, s.nearby?.metro?.m, s.url, s.gmaps, `${location.origin}/?city=${cityId}&open=${s.id}`];
  });
  const blob = new Blob([[cols, ...rows].map((r) => r.map(q).join(',')).join('\n')], { type: 'text/csv' });
  const a = Object.assign(document.createElement('a'), { href: URL.createObjectURL(blob), download: `flat-finder-${cityId}-${crit.mode}-results.csv` });
  a.click();
  URL.revokeObjectURL(a.href);
  toast(`Downloaded ${rows.length} societies.`);
}

// ---------- map buttons and theme ----------
let is3d = true, youMarker = null;
const SUN = '<svg viewBox="0 0 24 24" width="16" height="16"><circle cx="12" cy="12" r="4" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" stroke="currentColor" stroke-width="1.8"/></svg>';
const MOON = '<svg viewBox="0 0 24 24" width="16" height="16"><path d="M20 14.5A8 8 0 0 1 9.5 4 8 8 0 1 0 20 14.5z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></svg>';
function setBase(mode) {
  baseMode = mode;
  document.body.dataset.base = mode;
  if (map?.getLayer?.('st-bg')) setBaseMode(map, mode);
  document.querySelectorAll('#layers button[data-mode]').forEach((b) => b.classList.toggle('on', b.dataset.mode === mode));
  $('btn-theme').innerHTML = mode === 'light' ? MOON : SUN;
  $('btn-theme').title = mode === 'light' ? 'Dark mode' : 'Light mode';
  const q = new URLSearchParams(location.search);
  mode === 'streets' ? q.delete('map') : q.set('map', mode);
  history.replaceState(null, '', q.toString() ? `?${q}` : location.pathname);
}

function buildControls() {
  $('ctl-in').onclick = () => map?.zoomIn();
  $('ctl-out').onclick = () => map?.zoomOut();
  $('ctl-tilt').onclick = () => { is3d = !is3d; $('ctl-tilt').textContent = is3d ? '2D' : '3D'; map?.easeTo({ pitch: is3d ? 50 : 0, bearing: 0, duration: 800 }); };
  $('ctl-home').onclick = () => { closeCard(); map?.flyTo({ ...OVERVIEW, pitch: is3d ? OVERVIEW.pitch : 0, duration: 2000 }); };
  $('ctl-locate').onclick = () => {
    if (!navigator.geolocation) return;
    $('ctl-locate').classList.add('busy');
    navigator.geolocation.getCurrentPosition((p) => {
      $('ctl-locate').classList.remove('busy');
      const at = [p.coords.longitude, p.coords.latitude];
      if (!youMarker) { const el = document.createElement('div'); el.className = 'you'; youMarker = new maplibregl.Marker({ element: el }); }
      youMarker.setLngLat(at).addTo(map);
      map.flyTo({ center: at, zoom: 15, bearing: 0, duration: 2000 });
    }, () => { $('ctl-locate').classList.remove('busy'); toast('Could not get your location.'); }, { enableHighAccuracy: true, timeout: 10000 });
  };
  $('layers-btn').onclick = () => $('layers').classList.toggle('open');
  document.querySelectorAll('#layers button[data-mode]').forEach((b) => (b.onclick = () => { setBase(b.dataset.mode); $('layers').classList.remove('open'); }));
  $('btn-theme').onclick = () => setBase(baseMode === 'light' ? 'streets' : 'light');
  for (const k of ['glow', 'bounds', 'labels']) {
    const box = $(`hl-${k}`);
    box.checked = highlights[k];
    box.onchange = () => { highlights[k] = box.checked; store.set('ff-highlights', highlights); if (map) setHighlights(map, highlights); };
  }
  if (store.get('ff-log', true) === false) toggleLog(false);
  setBase(baseMode);
}

// ---------- onboarding ----------
function buildOnboarding() {
  const c = data.counts;
  const steps = [
    ['Every society in ' + data.city.name + ', on one map', `${c.on_map.toLocaleString()} housing societies, ${(c.for_sale || 0).toLocaleString()} homes for sale and ${(c.for_rent || 0).toLocaleString()} for rent. Each one has its prices, rents, resident ratings, what is nearby, and links to Google Maps.`],
    ['Start with what you cannot live without', 'Pick Buy or Rent and your budget. Then set the smallest bedroom you can live with, by both sides or by area in gaj or sq ft. Add amenities and what you want nearby, like a park within 500 m.'],
    ['How to read the map', '<span class="lg match"></span> Verified: every bedroom read from builder plans and passes.<br><span class="lg likely"></span> Likely: the rooms read so far pass.<br><span class="lg probable"></span> Probably fits: plans not read yet, estimated from unit size.<br><span class="lg unknown"></span> Not checked yet: no room data, so neither pass nor fail.'],
    ['Open a society, keep a list', 'Click any building for prices, bedrooms, ratings and the research behind every number. Star the ones you like, or paste a list of names you already have. Export your results as a CSV any time.'],
  ];
  let i = 0;
  const show = () => {
    $('ob-steps').innerHTML = steps.map((_, j) => `<i class="${j === i ? 'on' : ''}"></i>`).join('');
    $('ob-body').innerHTML = `<h3>${steps[i][0]}</h3><p>${steps[i][1]}</p>${i === 1 ? '<button class="preset" id="ob-divy">Try an example search</button>' : ''}`;
    $('ob-back').hidden = i === 0;
    $('ob-next').textContent = i === steps.length - 1 ? 'Start exploring' : 'Next';
    $('ob-divy')?.addEventListener('click', () => { useCriteria(DIVY); done(); });
  };
  const done = () => { $('onboard').hidden = true; store.set('ff-onboarded', true); };
  $('ob-next').onclick = () => (i === steps.length - 1 ? done() : (i++, show()));
  $('ob-back').onclick = () => { i = Math.max(0, i - 1); show(); };
  $('ob-skip').onclick = done;
  $('btn-guide').onclick = () => { i = 0; show(); $('onboard').hidden = false; };
  if (!store.get('ff-onboarded', false) && !params.has('nointro') && !params.has('open') && !params.has('preset')) { show(); $('onboard').hidden = false; }
}

// ---------- society search ----------
function buildSearch() {
  const input = $('q'), list = $('q-results');
  let items = [], active = -1;
  const close = () => { list.hidden = true; active = -1; };
  const render = () => {
    const all = searchSocieties(data.societies, input.value, 400);
    items = all.slice(0, 8);
    if (!items.length) {
      list.innerHTML = input.value.trim() ? '<li class="empty">No society by that name</li>' : '';
      list.hidden = !input.value.trim();
      return;
    }
    const rows = items.map((s, i) => {
      const li = document.createElement('li');
      li.className = i === active ? 'on' : '';
      li.innerHTML = `<span>${esc(s.name)}</span><span class="tag ${states.get(s.id)}">${esc(s.locality || '')}${s.verified ? ' · verified' : ''}</span><button class="iconbtn star ${myList.includes(s.id) ? 'on' : ''}" title="Add to my list">${myList.includes(s.id) ? '★' : '☆'}</button>`;
      li.onmousedown = (e) => {
        e.preventDefault();
        if (e.target.closest('.star')) { toggle(myList, s.id); saveList(); renderResults(); render(); return; }
        pick(s);
      };
      return li;
    });
    if (all.length > 1) {
      const li = document.createElement('li');
      li.className = 'showall';
      li.innerHTML = `<span>Show all ${all.length} matching "${esc(input.value.trim())}" on the map</span>`;
      li.onmousedown = (e) => { e.preventDefault(); setQuery(input.value.trim()); close(); input.blur(); };
      rows.unshift(li);
    }
    list.replaceChildren(...rows);
    list.hidden = false;
  };
  const pick = (s) => { stopTour(); input.value = s.name; close(); input.blur(); if (mobile) window.scrollTo(0, 0); openSociety(s.id); };
  input.oninput = () => { active = -1; render(); };
  input.onfocus = render;
  input.onblur = close;
  input.onkeydown = (e) => {
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault();
      if (!items.length) return;
      active = (active + (e.key === 'ArrowDown' ? 1 : -1) + items.length) % items.length;
      render();
    } else if (e.key === 'Enter' && items.length) pick(items[Math.max(0, active)]);
    else if (e.key === 'Escape') { close(); input.blur(); }
  };
  addEventListener('keydown', (e) => {
    if (e.key === '/' && !/INPUT|SELECT|TEXTAREA/.test(document.activeElement?.tagName)) { e.preventDefault(); input.focus(); }
  });
}

function setQuery(q) {
  crit.q = q;
  $('q-pill').hidden = !q;
  $('q-pill').innerHTML = q ? `Showing names matching "<b>${esc(q)}</b>" <button class="iconbtn" aria-label="Clear">×</button>` : '';
  $('q-pill').querySelector('button')?.addEventListener('click', () => { $('q').value = ''; setQuery(''); });
  applyFilters();
  if (q && map) {
    const hits = data.societies.filter((s) => states.get(s.id) !== 'no');
    if (hits.length) {
      const b = hits.reduce((bb, s) => bb.extend([s.lng, s.lat]), new maplibregl.LngLatBounds([hits[0].lng, hits[0].lat], [hits[0].lng, hits[0].lat]));
      map.fitBounds(b, { padding: { top: 80, bottom: 80, left: mobile ? 40 : 380, right: mobile ? 40 : 460 }, maxZoom: 15, bearing: 0 });
    }
  }
}

// ---------- tour ----------
let touring = false;
function stopTour() {
  if (!touring) return;
  touring = false;
  clearTimeout(tourTimer);
  map?.stop();
  $('btn-tour').textContent = 'Tour';
  $('btn-tour').classList.remove('live');
}

function tour() {
  if (touring) { stopTour(); return; }
  const list = ranked().slice(0, 10);
  if (!list.length) { toast('No matches to tour. Loosen your filters.'); return; }
  touring = true;
  $('btn-tour').textContent = 'Stop tour';
  $('btn-tour').classList.add('live');
  let i = 0;
  const next = () => {
    if (!touring) return;
    if (i >= list.length) { stopTour(); closeCard(); map.flyTo({ ...OVERVIEW, pitch: is3d ? OVERVIEW.pitch : 0, duration: 4000 }); return; }
    openSociety(list[i++].id);
    tourTimer = setTimeout(next, 7000);
  };
  next();
}
addEventListener('keydown', (e) => { if (e.key === 'Escape') stopTour(); });

boot().catch((e) => { console.error(e); document.title = 'ERR ' + e.message; });
