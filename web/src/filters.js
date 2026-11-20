// Pure filter logic. A society is "match", "likely", "unknown" (not checked yet) or "no".

export const RANK = { match: 4, likely: 3, probable: 2, unknown: 1, no: 0 };

export const DEFAULT_CRITERIA = {
  kinds: ['apartment'],
  bhk: [],          // empty = any
  room: null,       // { a, b } in feet, orientation-free
  roomArea: null,   // sq ft: every bedroom at least this big (used instead of room when set)
  estimates: true,  // allow "probable" from unit-size estimates when plans are unread
  near: [],         // nearby keys, see NEAR
  q: '',            // name filter from search
  only: null,       // array of society ids (my list) or null
  minSqft: 0,
  maxSqft: null,
  minPrice: null,   // rupees, buying
  minRent: null,    // rupees per month
  mode: 'buy',      // 'buy' or 'rent'
  maxPrice: null,   // rupees, buying
  maxRent: null,    // rupees per month, renting
  amenities: [],    // amenity keys, see AMENITY_KEYS
  ready: false,     // only ready to move
};

// Amenity keys -> words that identify them in portal amenity names.
export const AMENITY_KEYS = {
  squash: ['squash'],
  pool: ['swimming pool', 'pool'],
  gym: ['gym'],
  club: ['club house', 'clubhouse'],
  tennis: ['tennis'],
  badminton: ['badminton'],
  jogging: ['jogging'],
  kids: ['kids play', "children's play", 'kids club'],
};

// Nearby filters: OSM place kind and the distance it must be within (metres).
export const NEAR = {
  park: { label: 'Park', kinds: ['park'], m: 500 },
  metro: { label: 'Metro or rail', kinds: ['metro', 'rail'], m: 1500 },
  school: { label: 'School', kinds: ['school'], m: 1000 },
  hospital: { label: 'Hospital', kinds: ['hospital'], m: 2000 },
  shopping: { label: 'Mall or supermarket', kinds: ['shopping'], m: 1500 },
};

export function isNear(s, key) {
  const n = NEAR[key];
  return n.kinds.some((k) => (s.nearby?.[k]?.m ?? Infinity) <= n.m);
}

export function hasAmenity(s, key) {
  if (key.startsWith('n:')) return s.amenities.some((a) => a.toLowerCase() === key.slice(2));
  const fact = s.amen_facts?.[key];
  if (fact) return fact.value === 'yes';
  const words = AMENITY_KEYS[key] || [key];
  return s.amenities.some((a) => words.some((w) => a.toLowerCase().includes(w)));
}

export function roomPasses([short, long], { a, b }) {
  const need = [Math.min(a, b), Math.max(a, b)];
  return short + 1e-6 >= need[0] && long + 1e-6 >= need[1];
}

export function unitSize(u) {
  return u.super_sqft || u.size_sqft || u.carpet_sqft || null;
}

// A unit read by Jev from its floor plan: exact narrowest side, plus confirmed "at least" / "below" steps.
function matchAiUnit(u, c) {
  const a = u.ai;
  let verdict = 'likely'; // Jev alone can overstate a room (about 1 in 10 in spot checks): never a full match
  if (c.minSqft > 0 && u.size_range) {
    if (u.size_range[1] < c.minSqft) return 'no';
    if (u.size_range[0] < c.minSqft) verdict = 'likely'; // which listed size this plan is, is not known
  }
  if (c.roomArea) {
    if (a.area_ub != null && a.area_ub <= c.roomArea) return 'no';
    return a.area_lb != null && a.area_lb >= c.roomArea ? verdict : 'unknown';
  }
  if (c.room) {
    const short = Math.min(c.room.a, c.room.b), long = Math.max(c.room.a, c.room.b);
    if (a.min_short != null && a.min_short < short - 1e-6) return 'no';
    if (a.long_ub != null && a.long_ub <= long) return 'no';
    return a.min_short != null && a.min_short >= short - 1e-6 && a.long_lb != null && a.long_lb >= long - 1e-6 ? verdict : 'unknown';
  }
  return verdict;
}

export function matchUnit(u, c) {
  if (c.maxSqft) {
    const size = unitSize(u) ?? u.size_range?.[0];
    if (size != null && size > c.maxSqft) return 'no';
  }
  if (u.ai) return matchAiUnit(u, c);
  if (c.minSqft > 0 && u.size_range && !unitSize(u)) {
    if (u.size_range[1] < c.minSqft) return 'no';
  } else if (c.minSqft > 0) {
    const size = unitSize(u);
    if (size == null) return 'unknown';
    if (size < c.minSqft) return 'no';
  }
  const area = c.roomArea;
  if (!c.room && !area) return 'match';
  if (!u.bedrooms?.length) {
    // plans unread: a cautious lower bound from unit size can say "probably fits", never "fits"
    if (c.estimates !== false && u.est_short != null) {
      const ok = area ? u.est_area >= area : u.est_short >= Math.min(c.room.a, c.room.b) && u.est_area >= c.room.a * c.room.b;
      if (ok) return 'probable';
    }
    return 'unknown';
  }
  const fails = area ? u.bedrooms.some(([a, b]) => a * b < area - 1e-6) : u.bedrooms.some((r) => !roomPasses(r, c.room));
  if (fails) return 'no';
  return u.rooms_complete ? 'match' : 'likely';
}

const norm = (t) => (t || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();

export function matchSociety(s, c) {
  if (c.only && !c.only.includes(s.id)) return 'no';
  if (c.q) {
    const hay = `${norm(s.name)} ${norm(s.developer)} ${norm(s.locality)}`;
    if (!norm(c.q).split(' ').every((w) => hay.includes(w))) return 'no';
  }
  if (c.kinds.length && !c.kinds.includes(s.kind)) return 'no';
  for (const key of c.near || []) if (!isNear(s, key)) return 'no';
  if (c.ready && !/ready/i.test(s.status || '')) return 'no';
  const budget = c.mode === 'rent' ? c.maxRent : c.maxPrice;
  const floor = c.mode === 'rent' ? c.minRent : c.minPrice;
  if (budget || floor) {
    const p = priceFor(s, c.mode, c.bhk);
    if (p && budget && p.value > budget) return 'no';
    if (p && floor && p.value < floor) return 'no';
  }
  for (const key of c.amenities) if (!hasAmenity(s, key)) return 'no';

  const unitFilters = c.bhk.length || c.minSqft > 0 || c.maxSqft || c.room || c.roomArea;
  if (!unitFilters) return 'match';
  const units = s.unit_types.filter((u) => !c.bhk.length || c.bhk.includes(u.bhk));
  if (!units.length) return s.unit_types.length ? 'no' : 'unknown';
  let best = 'no';
  for (const u of units) {
    const r = matchUnit(u, c);
    if (RANK[r] > RANK[best]) best = r;
    if (best === 'match') break;
  }
  return best;
}

export function feetLabel(ft) {
  let f = Math.floor(ft + 1e-6);
  let i = Math.round((ft - f) * 12);
  if (i === 12) { f += 1; i = 0; }
  return `${f}'${i}"`;
}

// Cheapest price for the chosen BHKs: listing median first, our estimate otherwise. null when unknown.
// Medians flagged as likely typos (p.flags) are skipped, so one mistyped listing cannot hide or promote a society.
export function priceFor(s, mode, bhk = []) {
  let best = null;
  for (const [b, p] of Object.entries(s.prices || {})) {
    if (bhk.length && !bhk.includes(+b)) continue;
    const real = p.flags?.[mode] ? null : p[mode]?.median;
    const est = p[`${mode}_est`]?.value;
    const v = real ?? est;
    if (v && (!best || v < best.value)) best = { value: v, estimated: real == null, bhk: +b, basis: real == null ? p[`${mode}_est`].basis : null, n: real == null ? null : p[mode]?.n };
  }
  if (!best && mode === 'buy' && s.price_min && !bhk.length) best = { value: s.price_min, estimated: false, bhk: null, basis: 'builder price range' };
  return best;
}

export function formatINR(r) {
  if (r == null) return '';
  if (r >= 1e7) return `₹${(r / 1e7).toFixed(2).replace(/\.?0+$/, '')} Cr`;
  if (r >= 1e5) return `₹${(r / 1e5).toFixed(1).replace(/\.0$/, '')} L`;
  return `₹${Math.round(r / 1000)}k`;
}
