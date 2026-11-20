// Society search: every query word must appear in name, developer or locality.
const norm = (s) => (s || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();

export function searchSocieties(societies, query, limit = 8) {
  const words = norm(query).split(' ').filter(Boolean);
  if (!words.length) return [];
  const out = [];
  for (const s of societies) {
    const name = norm(s.name);
    const hay = `${name} ${norm(s.developer)} ${norm(s.locality)}`;
    if (!words.every((w) => hay.includes(w))) continue;
    const q = words.join(' ');
    const score = (name.startsWith(q) ? 4 : 0) + (name.includes(q) ? 2 : 0) + (words.every((w) => name.includes(w)) ? 1 : 0) + (s.verified ? 0.5 : 0);
    out.push({ s, score });
  }
  return out.sort((a, b) => b.score - a.score || a.s.name.length - b.s.name.length).slice(0, limit).map((r) => r.s);
}
