// Society and locality search: normalizes common Bengaluru spellings & abbreviations.
const ALIASES = [
  [/\bbangalore\b/g, 'bengaluru'],
  [/\b(?:e\s*city|ecity|electroniccity)\b/g, 'electronic city'],
  [/\bkormangala\b/g, 'koramangala'],
  [/\bindranagar\b/g, 'indiranagar'],
  [/\bmarathal+i\b/g, 'marathahalli'],
  [/\bsarjapura\b/g, 'sarjapur'],
  [/\byelhanka\b/g, 'yelahanka'],
  [/\bmalleswaram\b/g, 'malleshwaram'],
  [/\brajaji\s+nagar\b/g, 'rajajinagar'],
  [/\byeshwantpur\b/g, 'yeshwanthpur'],
  [/\b(?:j\s*p\s*nagar|jpnagar)\b/g, 'jp nagar'],
  [/\b(?:r\s*r\s*nagar|rrnagar|rajarajeshwari\s*nagar)\b/g, 'rr nagar'],
  [/\b(?:r\s*t\s*nagar|rtnagar)\b/g, 'rt nagar'],
  [/\b(?:k\s*r\s*puram|krpuram|krishnarajapuram)\b/g, 'kr puram'],
  [/\bc\s*v\s*raman\s*nagar\b/g, 'cv raman nagar'],
  [/\bh\s*s\s*r\b/g, 'hsr'],
  [/\bb\s*t\s*m\b/g, 'btm'],
  [/\bm\s*g\s*road\b/g, 'mg road'],
  [/\bouter\s+ring\s+road\b/g, 'orr'],
  [/\brd\b/g, 'road'],
];

export function normText(s) {
  let t = (s || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
  for (const [rx, rep] of ALIASES) t = t.replace(rx, rep);
  return t.replace(/\s+/g, ' ').trim();
}

// Collapse sub-block / phase / stage suffixes to a clean neighbourhood label for the Area filter.
export function canonicalArea(loc) {
  const raw = (loc || '').trim();
  if (!raw) return [];
  const parts = raw.split(',').map((p) => p.trim()).filter(Boolean);
  const out = new Set();
  for (let p of parts) {
    p = p.replace(/\s*\([^)]*\)\s*/g, ' ').trim();
    p = p.replace(/\s+(?:sector\s+\d+[a-z]?|phase\s+\d+|stage\s+\d+|\d+(?:st|nd|rd|th)\s+(?:block|stage|phase))$/i, '').trim();
    if (/^(?:north|south|east|west|central)\s+bengaluru$/i.test(p)) continue;
    if (p.length >= 2) out.add(p);
  }
  return [...out];
}

export function buildAreaIndex(societies) {
  const counts = new Map();
  for (const s of societies) {
    const seen = new Set();
    for (const area of canonicalArea(s.locality)) {
      const k = normText(area);
      if (seen.has(k)) continue;
      seen.add(k);
      const cur = counts.get(k);
      if (cur) cur.n += 1;
      else counts.set(k, { name: area, key: k, n: 1 });
    }
  }
  return [...counts.values()].sort((a, b) => b.n - a.n || a.name.localeCompare(b.name));
}

export function searchAreas(areas, query, limit = 5) {
  const words = normText(query).split(' ').filter(Boolean);
  if (!words.length) return [];
  const q = words.join(' ');
  const out = [];
  for (const a of areas) {
    if (!words.every((w) => a.key.includes(w))) continue;
    const score = (a.key === q ? 10 : 0) + (a.key.startsWith(q) ? 4 : 0) + Math.min(3, a.n / 10);
    out.push({ a, score });
  }
  return out.sort((x, y) => y.score - x.score || y.a.n - x.a.n).slice(0, limit).map((r) => r.a);
}

export function searchSocieties(societies, query, limit = 8) {
  const words = normText(query).split(' ').filter(Boolean);
  if (!words.length) return [];
  const out = [];
  for (const s of societies) {
    const name = normText(s.name);
    const loc = normText(s.locality);
    const hay = `${name} ${normText(s.developer)} ${loc}`;
    if (!words.every((w) => hay.includes(w))) continue;
    const q = words.join(' ');
    const score = (name.startsWith(q) ? 4 : 0) + (name.includes(q) ? 2 : 0) + (loc.includes(q) ? 1.5 : 0) + (words.every((w) => name.includes(w)) ? 1 : 0) + (s.verified ? 0.5 : 0);
    out.push({ s, score });
  }
  return out.sort((a, b) => b.score - a.score || a.s.name.length - b.s.name.length).slice(0, limit).map((r) => r.s);
}
