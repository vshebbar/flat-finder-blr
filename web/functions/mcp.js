// Flat Finder MCP server (Streamable HTTP, JSON responses), so people can add Flat Finder to Claude as a connector.
// Runs as a Cloudflare Pages Function at /mcp and reads the same static data the website uses.
import { DEFAULT_CRITERIA, NEAR, feetLabel, formatINR, hasAmenity, matchSociety, priceFor, unitSize } from '../src/filters.js';
import { searchSocieties } from '../src/search.js';

const PROTOCOL = '2025-06-18';
const SITE = 'https://flat-finder.pages.dev';
const cache = new Map();

async function city(env, origin, id) {
  if (!cache.has(id)) {
    const res = await env.ASSETS.fetch(new Request(`${origin}/data/${id}.json`));
    if (!res.ok) throw new Error(`Unknown city "${id}"`);
    cache.set(id, await res.json());
  }
  return cache.get(id);
}

const KINDS = ['apartment', 'builder floor', 'villa', 'plot', 'commercial', 'other'];
const PLACES = ['park', 'metro', 'rail', 'school', 'hospital', 'shopping'];
const FILTERS = {
  city: { type: 'string', description: 'City id, e.g. "bangalore" or "gurgaon"', default: 'bangalore' },
  mode: { type: 'string', enum: ['buy', 'rent'], default: 'buy', description: 'Which price the budget and price sorting use' },
  localities: { type: 'array', items: { type: 'string' }, description: 'Localities or areas, e.g. ["Whitefield", "Sarjapur Road", "Hebbal", "Indiranagar"]. Matches the locality exactly, or as its start ("Whitefield" also matches "Varthur, Whitefield"). Use list_localities to see names.' },
  name_contains: { type: 'string', description: 'Words that must appear in the society name, developer or locality, e.g. "Prestige" or "Sobha"' },
  within_km_of: { type: 'object', properties: { lat: { type: 'number' }, lng: { type: 'number' }, km: { type: 'number' } }, required: ['lat', 'lng', 'km'], description: 'Only societies within km of a point, e.g. an office. Results then show distance_km.' },
  bhk: { type: 'array', items: { type: 'integer' }, description: 'BHK types, e.g. [3,4]' },
  min_bedroom_ft: { type: 'array', items: { type: 'number' }, minItems: 2, maxItems: 2, description: 'Smallest bedroom sides in feet, e.g. [11.25, 12.25]' },
  min_bedroom_sqft: { type: 'number', description: 'Smallest bedroom area in sq ft (1 gaj = 9 sq ft). Use instead of min_bedroom_ft.' },
  min_home_sqft: { type: 'number' },
  max_home_sqft: { type: 'number' },
  min_price_inr: { type: 'number' }, max_price_inr: { type: 'number', description: 'Buy budget in rupees' },
  min_rent_inr: { type: 'number' }, max_rent_inr: { type: 'number', description: 'Monthly rent budget in rupees' },
  amenities: { type: 'array', items: { type: 'string' }, description: 'All must be present: "squash","pool","gym","club","tennis","badminton","jogging","kids", or any exact amenity name' },
  nearby: { type: 'array', items: { type: 'string', enum: Object.keys(NEAR) }, description: 'Default distances: park 500 m, metro 1.5 km, school 1 km, hospital 2 km, shopping 1.5 km' },
  nearby_within_m: { type: 'object', additionalProperties: { type: 'number' }, description: `Custom distances in metres, e.g. {"metro": 800, "school": 2000}. Keys: ${PLACES.join(', ')}` },
  min_rating: { type: 'number', description: 'Resident rating out of 5' },
  types: { type: 'array', items: { type: 'string', enum: KINDS }, default: ['apartment'], description: 'Use ["any"] for every type' },
  ready_to_move: { type: 'boolean' },
  include_estimates: { type: 'boolean', default: true },
};

const TOOLS = [
  {
    name: 'search_societies',
    description: 'List housing societies in an Indian city that fit any mix of filters: sector/locality, distance from a point, BHK, smallest bedroom, home size, buy or rent range, amenities, distance to park/metro/school/hospital/mall, rating. With no filters but a locality it lists every society there. Each result has per-BHK buy and rent (median of live listings, or a marked estimate), sizes, smallest bedroom, distances to nearby places and key amenities. Paginate with offset; total says how many matched. Verdict: match = bedrooms read from plans and all pass (or no room filter used); likely = rooms read so far pass; probable = estimated from unit size.',
    inputSchema: { type: 'object', properties: { ...FILTERS,
      sort_by: { type: 'string', enum: ['best', 'price', 'rent', 'rating', 'score', 'size', 'metro', 'distance', 'name'], default: 'best', description: 'best = verdict, then verified, then Flat Finder score. price/rent/size/metro/distance ascending, rating/score descending.' },
      offset: { type: 'integer', default: 0 },
      limit: { type: 'integer', default: 25, maximum: 200 },
      include_all_amenities: { type: 'boolean', default: false, description: 'Return the full amenity list for each society' } } },
  },
  {
    name: 'breakdown',
    description: 'Group the societies that fit the same filters as search_societies and summarise each group: how many societies, median buy price and rent (for the chosen BHKs), median size, rating, and how many have room sizes read. Use for "break sector 56 down by BHK", "which sectors are cheapest for a 3 BHK rent", "how many have a pool", "by distance to metro".',
    inputSchema: { type: 'object', properties: { ...FILTERS,
      group_by: { type: 'string', enum: ['locality', 'bhk', 'type', 'status', 'developer', 'amenity', 'metro_distance', 'rent_band', 'price_band'], default: 'locality' },
      top: { type: 'integer', default: 40, maximum: 200, description: 'Most groups to return, largest first' } } },
  },
  {
    name: 'list_localities',
    description: 'Every sector or locality in a city with its number of societies and its centre point. Use to find the exact locality names.',
    inputSchema: { type: 'object', properties: { city: { type: 'string', default: 'bangalore' }, contains: { type: 'string' } } },
  },
  {
    name: 'get_society',
    description: 'Full details for one society by name: unit types and bedroom sizes with sources, buy and rent prices per BHK, resident ratings by category, review snippets, description, nearby places, amenities and links.',
    inputSchema: { type: 'object', properties: { city: { type: 'string', default: 'bangalore' }, name: { type: 'string' } }, required: ['name'] },
  },
  {
    name: 'compare_societies',
    description: 'Side-by-side comparison of up to 10 societies by name: per-BHK prices, rents, sizes, smallest bedrooms, score, rating, nearby, amenities.',
    inputSchema: { type: 'object', properties: { city: { type: 'string', default: 'bangalore' }, mode: { type: 'string', enum: ['buy', 'rent'], default: 'buy' }, names: { type: 'array', items: { type: 'string' }, maxItems: 10 } }, required: ['names'] },
  },
];

const KEY_AMENITIES = ['pool', 'gym', 'club', 'squash', 'tennis', 'badminton', 'jogging', 'kids'];
const norm = (t) => String(t ?? '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
const median = (xs) => { const v = xs.filter((x) => x != null).sort((a, b) => a - b); return v.length ? v[Math.floor((v.length - 1) / 2)] : null; };
const amenityKey = (a) => { const k = a.toLowerCase().trim(); return KEY_AMENITIES.includes(k) ? k : `n:${k}`; };

function km(a, b) {
  const r = Math.PI / 180, dLat = (b.lat - a.lat) * r, dLng = (b.lng - a.lng) * r;
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(a.lat * r) * Math.cos(b.lat * r) * Math.sin(dLng / 2) ** 2;
  return 12742 * Math.asin(Math.sqrt(h));
}

function inLocality(s, wanted) {
  const loc = norm(s.locality);
  return wanted.some((w) => loc === w || loc.startsWith(`${w} `));
}

function criteria(args) {
  return {
    ...structuredClone(DEFAULT_CRITERIA), mode: args.mode || 'buy', bhk: args.bhk || [],
    kinds: args.types?.includes('any') ? [] : args.types || ['apartment'], q: args.name_contains || '',
    room: args.min_bedroom_ft ? { a: args.min_bedroom_ft[0], b: args.min_bedroom_ft[1] } : null, roomArea: args.min_bedroom_sqft || null,
    minSqft: args.min_home_sqft || 0, maxSqft: args.max_home_sqft || null,
    minPrice: args.min_price_inr || null, maxPrice: args.max_price_inr || null, minRent: args.min_rent_inr || null, maxRent: args.max_rent_inr || null,
    amenities: (args.amenities || []).map(amenityKey), near: args.nearby || [], ready: !!args.ready_to_move, estimates: args.include_estimates !== false,
  };
}

const RANK_OUT = { match: 3, likely: 2, probable: 1 };

// Societies that pass every filter, as [society, verdict, distance_km].
function filtered(data, args, crit) {
  const locs = (args.localities || []).map((l) => { const n = norm(l); return /^\d+[a-z]?$/.test(n) ? `sector ${n}` : n; });
  const near = Object.entries(args.nearby_within_m || {});
  const at = args.within_km_of;
  const out = [];
  for (const s of data.societies) {
    if (locs.length && !inLocality(s, locs)) continue;
    if (args.min_rating && !(s.rating >= args.min_rating)) continue;
    if (near.some(([k, m]) => !((k === 'metro' ? Math.min(s.nearby?.metro?.m ?? Infinity, s.nearby?.rail?.m ?? Infinity) : s.nearby?.[k]?.m ?? Infinity) <= m))) continue;
    let d = null;
    if (at) { if (s.lat == null) continue; d = km(at, s); if (d > at.km) continue; }
    const st = matchSociety(s, crit);
    if (RANK_OUT[st]) out.push([s, st, d]);
  }
  return out;
}

function perBhk(s, bhk) {
  const out = {};
  const want = (b) => !bhk.length || bhk.includes(b);
  for (const u of s.unit_types) {
    if (u.bhk == null || !want(u.bhk)) continue;
    const e = (out[u.bhk] ||= { sqft: [], rooms: [] });
    const sz = unitSize(u); if (sz) e.sqft.push(sz);
    e.rooms.push(...(u.bedrooms || []));
  }
  for (const [b, p] of Object.entries(s.prices || {})) if (want(+b)) out[b] ||= { sqft: [], rooms: [] };
  return Object.fromEntries(Object.entries(out).map(([b, e]) => {
    const p = s.prices?.[b] || {};
    const price = (m) => {
      const est = p[`${m}_est`]?.value ? { estimate: p[`${m}_est`].value } : null;
      if (p[m]?.median == null) return est;
      const real = { median: p[m].median, range: [p[m].min, p[m].max], listings: p[m].n, ...(p[m].n === 1 && { thin: 'only 1 listing' }), ...(p.flags?.[`${m}_range`] && { range_warning: p.flags[`${m}_range`] }) };
      return p.flags?.[m] ? { listed: real, flag: `Flat Finder check: ${p.flags[m]}. Not used for filtering.`, ...est } : real;
    };
    const small = e.rooms.length ? e.rooms.reduce((m, r) => (r[0] < m[0] ? r : m)) : null;
    return [b, { buy: price('buy'), rent: price('rent'), price_per_sqft: p.psf ?? null,
      sqft: e.sqft.length ? [Math.min(...e.sqft), Math.max(...e.sqft)] : null,
      smallest_bedroom_read: small ? `${feetLabel(small[0])} x ${feetLabel(small[1])}` : null }];
  }));
}

function nearbyOut(s) {
  return Object.fromEntries(Object.entries(s.nearby || {}).map(([k, v]) => [k, v?.m != null ? `${v.m} m${v.name ? ` (${v.name})` : ''}` : null]));
}

function summary(s, st, crit, d, allAmenities) {
  return {
    name: s.name, locality: s.locality, verdict: st, type: s.kind, status: s.status, possession: s.possession, developer: s.developer,
    rooms_checked: s.verified ? 'by hand' : s.ai_read ? 'AI-read floor plans' : 'no',
    ...(d != null && { distance_km: +d.toFixed(2) }),
    by_bhk: perBhk(s, crit.bhk),
    flat_finder_score: s.score, resident_rating: s.rating, listings_for_sale: s.sale_count, listings_for_rent: s.rent_count,
    nearby: nearbyOut(s),
    amenities: allAmenities ? s.amenities : KEY_AMENITIES.filter((k) => hasAmenity(s, k)),
    towers: s.towers, units: s.units, acres: s.acres,
    link: `${SITE}/?open=${s.id}`,
  };
}

const SORTS = {
  price: (s, c) => priceFor(s, 'buy', c.bhk)?.value ?? Infinity,
  rent: (s, c) => priceFor(s, 'rent', c.bhk)?.value ?? Infinity,
  rating: (s) => -(s.rating ?? -Infinity),
  score: (s) => -(s.score ?? -Infinity),
  size: (s, c) => Math.min(...s.unit_types.filter((u) => !c.bhk.length || c.bhk.includes(u.bhk)).map((u) => unitSize(u) ?? Infinity), Infinity),
  metro: (s) => Math.min(s.nearby?.metro?.m ?? Infinity, s.nearby?.rail?.m ?? Infinity),
};

function band(v, steps, fmt) {
  if (v == null) return 'unknown';
  const i = steps.findIndex((x) => v < x);
  return i === -1 ? `${fmt(steps.at(-1))}+` : i === 0 ? `under ${fmt(steps[0])}` : `${fmt(steps[i - 1])} to ${fmt(steps[i])}`;
}

function groupKeys(s, by, crit) {
  switch (by) {
    case 'locality': return [s.locality || 'unknown'];
    case 'bhk': return [...new Set(s.unit_types.map((u) => u.bhk).concat(Object.keys(s.prices || {}).map(Number)))].filter((b) => b != null && (!crit.bhk.length || crit.bhk.includes(b))).map((b) => `${b} BHK`);
    case 'type': return [s.kind || 'unknown'];
    case 'status': return [s.status || 'unknown'];
    case 'developer': return [s.developer || 'unknown'];
    case 'amenity': return KEY_AMENITIES.filter((k) => hasAmenity(s, k)).concat('(all societies)');
    case 'metro_distance': return [band(SORTS.metro(s), [500, 1000, 1500, 2500, 5000], (m) => `${m / 1000} km`)];
    case 'rent_band': return [band(priceFor(s, 'rent', crit.bhk)?.value, [25e3, 40e3, 60e3, 80e3, 1e5, 15e4], formatINR)];
    case 'price_band': return [band(priceFor(s, 'buy', crit.bhk)?.value, [5e6, 1e7, 2e7, 3e7, 5e7, 1e8], formatINR)];
  }
  return ['all'];
}

let detailsCache = null;
async function details(env, origin, id, sid) {
  if (!detailsCache || detailsCache.id !== id) {
    const res = await env.ASSETS.fetch(new Request(`${origin}/data/${id}-details.json`));
    detailsCache = { id, data: res.ok ? await res.json() : {} };
  }
  return detailsCache.data[sid] || null;
}

function detail(s, extra) {
  return {
    name: s.name, developer: s.developer, locality: s.locality, lat: s.lat, lng: s.lng, type: s.kind, status: s.status, possession: s.possession, rera: s.rera_id,
    towers: s.towers, units: s.units, acres: s.acres, verified: s.verified, note: s.note,
    unit_types: s.unit_types.map((u) => ({ unit: u.label, bhk: u.bhk, sqft: unitSize(u),
      bedrooms: (u.bedrooms || []).map((r) => `${feetLabel(r[0])} x ${feetLabel(r[1])}`), all_bedrooms_read: u.rooms_complete,
      estimated_smallest_bedroom: u.est_short ? `at least ${feetLabel(u.est_short)} wide, ~${u.est_area} sq ft (estimate)` : null,
      read_by_ai_from_plan: u.ai ? { narrowest_bedroom: u.ai.min_short != null ? feetLabel(u.ai.min_short) : null,
        every_bedroom_long_side_at_least: u.ai.long_lb != null ? feetLabel(u.ai.long_lb) : null, every_bedroom_area_at_least_sqft: u.ai.area_lb } : null,
      source: u.source, page: u.page })),
    prices: s.prices, score: s.score, score_parts: s.score_parts, resident_rating: s.rating, rating_count: s.rating_count,
    ratings_by_category: extra?.ratings || null,
    reviews: (extra?.reviews || []).slice(0, 8).map((r) => ({ title: r.title, text: r.text, date: r.date, by: r.by })),
    description: extra?.description || null,
    nearby: s.nearby, amenities: s.amenities, brochure: s.brochure_url, magicbricks: s.url, google_maps: s.gmaps, flat_finder: `${SITE}/?open=${s.id}`,
  };
}

async function callTool(name, args, env, origin) {
  const id = args.city || 'bangalore';
  const data = await city(env, origin, id);
  if (name === 'search_societies' || name === 'breakdown') {
    const crit = criteria(args);
    const hits = filtered(data, args, crit);
    const counts = hits.reduce((c, [, st]) => ((c[st] = (c[st] || 0) + 1), c), {});
    if (name === 'breakdown') {
      const by = args.group_by || 'locality';
      const groups = new Map();
      for (const [s, st] of hits) for (const k of groupKeys(s, by, crit)) {
        if (!groups.has(k)) groups.set(k, []);
        groups.get(k).push(s);
      }
      const bhkFor = (k) => (by === 'bhk' ? [parseInt(k, 10)] : crit.bhk);
      const rows = [...groups].map(([k, ss]) => ({
        group: k, societies: ss.length,
        median_buy_inr: median(ss.map((s) => priceFor(s, 'buy', bhkFor(k))?.value)),
        median_rent_inr: median(ss.map((s) => priceFor(s, 'rent', bhkFor(k))?.value)),
        median_home_sqft: median(ss.flatMap((s) => s.unit_types.filter((u) => !bhkFor(k).length || bhkFor(k).includes(u.bhk)).map(unitSize))),
        median_rating: median(ss.map((s) => s.rating)),
        with_room_sizes_read: ss.filter((s) => s.verified || s.ai_read).length,
        examples: ss.slice().sort((a, b) => (b.score || 0) - (a.score || 0)).slice(0, 5).map((s) => s.name),
      })).sort((a, b) => b.societies - a.societies);
      return { city: data.city.name, group_by: by, total_societies: hits.length, counts, groups_total: rows.length,
        note: 'Prices are medians across societies of each society\'s cheapest matching listing median (or our estimate where a society has no listings).',
        groups: rows.slice(0, Math.min(args.top || 40, 200)) };
    }
    const sortBy = args.sort_by || (args.within_km_of ? 'distance' : 'best');
    const key = sortBy === 'distance' ? (h) => h[2] ?? Infinity : SORTS[sortBy] ? (h) => SORTS[sortBy](h[0], crit) : null;
    hits.sort(key ? (a, b) => key(a) - key(b) || a[0].name.localeCompare(b[0].name)
      : sortBy === 'name' ? (a, b) => a[0].name.localeCompare(b[0].name)
        : (a, b) => RANK_OUT[b[1]] - RANK_OUT[a[1]] || b[0].verified - a[0].verified || (b[0].score || 0) - (a[0].score || 0));
    const offset = Math.max(0, args.offset || 0), limit = Math.min(args.limit || 25, 200);
    return { city: data.city.name, total: hits.length, counts, offset, returned: Math.min(limit, Math.max(0, hits.length - offset)), has_more: offset + limit < hits.length,
      how_to_read: 'verdict: match = bedrooms read from floor plans and all pass, or no room filter was used; likely = rooms read so far pass; probable = plans unread, estimated from unit size. Societies without room data are left out under room filters. by_bhk prices: median of live listings with range and count, or "estimate" when there are none. A price with "flag" is what the listing says but our checks think it is a typo: say so, and prefer the estimate. nearby: distance to the closest place of each kind.',
      results: hits.slice(offset, offset + limit).map(([s, st, d]) => summary(s, st, crit, d, args.include_all_amenities)) };
  }
  if (name === 'list_localities') {
    const m = new Map();
    for (const s of data.societies) {
      const k = s.locality || 'unknown';
      if (args.contains && !norm(k).includes(norm(args.contains))) continue;
      const e = m.get(k) || { locality: k, societies: 0, lat: 0, lng: 0, n: 0 };
      e.societies++; if (s.lat != null) { e.lat += s.lat; e.lng += s.lng; e.n++; }
      m.set(k, e);
    }
    const rows = [...m.values()].map(({ n, lat, lng, ...e }) => ({ ...e, centre: n ? [+(lat / n).toFixed(4), +(lng / n).toFixed(4)] : null }))
      .sort((a, b) => b.societies - a.societies);
    return { city: data.city.name, localities: rows.length, rows };
  }
  const find = (n) => searchSocieties(data.societies, n, 1)[0];
  if (name === 'get_society') {
    const s = find(args.name);
    return s ? detail(s, await details(env, origin, id, s.id)) : { error: `No society found for "${args.name}"` };
  }
  if (name === 'compare_societies') {
    const crit = { ...structuredClone(DEFAULT_CRITERIA), mode: args.mode || 'buy' };
    return { societies: (args.names || []).slice(0, 10).map((n) => { const s = find(n); return s ? summary(s, s.verified ? 'verified' : 'portal data', crit, null, true) : { name: n, error: 'not found' }; }) };
  }
  throw new Error(`Unknown tool ${name}`);
}

const json = (body, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json', 'access-control-allow-origin': '*' } });

export async function onRequest({ request, env }) {
  if (request.method === 'OPTIONS') return new Response(null, { headers: { 'access-control-allow-origin': '*', 'access-control-allow-headers': '*', 'access-control-allow-methods': 'POST, GET, OPTIONS' } });
  if (request.method === 'GET') return json({ name: 'Flat Finder', mcp: 'POST JSON-RPC here', tools: TOOLS.map((t) => t.name) });
  const origin = new URL(request.url).origin;
  const msg = await request.json().catch(() => null);
  if (!msg) return json({ jsonrpc: '2.0', id: null, error: { code: -32700, message: 'Parse error' } }, 400);
  const reply = (result) => json({ jsonrpc: '2.0', id: msg.id, result });
  try {
    switch (msg.method) {
      case 'initialize':
        return reply({ protocolVersion: msg.params?.protocolVersion || PROTOCOL, capabilities: { tools: {} },
          serverInfo: { name: 'flat-finder', version: '0.2.0' },
          instructions: 'Search Indian housing societies by sector, real bedroom sizes, buy or rent budget, amenities and what is nearby. search_societies lists every match (paginate with offset, up to 200 per call); breakdown groups them by locality, BHK, amenity, metro distance or rent/price band; list_localities gives exact sector names. Always say which results are verified, likely or estimated, and share the Flat Finder link for each society.' });
      case 'notifications/initialized':
        return new Response(null, { status: 202 });
      case 'ping':
        return reply({});
      case 'tools/list':
        return reply({ tools: TOOLS });
      case 'tools/call': {
        const out = await callTool(msg.params.name, msg.params.arguments || {}, env, origin);
        return reply({ content: [{ type: 'text', text: JSON.stringify(out, (k, v) => (v === null ? undefined : v)) }] });
      }
      default:
        return json({ jsonrpc: '2.0', id: msg.id, error: { code: -32601, message: `Method not found: ${msg.method}` } });
    }
  } catch (e) {
    return reply({ content: [{ type: 'text', text: `Error: ${e.message}` }], isError: true });
  }
}
