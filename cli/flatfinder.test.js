import { expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { parseArgs, parseFeet, parsePrice, search } from './flatfinder.mjs';

it('reads feet and prices', () => {
  expect(parseFeet("11'3")).toBe(11.25);
  expect(parseFeet('11.25')).toBe(11.25);
  expect(parsePrice('3cr')).toBe(3e7);
  expect(parsePrice('90L')).toBe(9e6);
});

it("Divy's search finds Araya and Presidia as matches", () => {
  const city = JSON.parse(readFileSync(new URL('../web/public/data/gurgaon.json', import.meta.url)));
  const o = parseArgs(['--bhk', '2,3,4', '--min-bedroom', "11'3x12'3", '--min-sqft', '1620', '--amenity', 'squash']);
  const names = search(city, o).map((r) => r.s.name);
  expect(names).toContain('Pioneer Araya');
  expect(names).toContain('Pioneer Presidia');
  expect(names).not.toContain('Emaar Amaris');
});

it('reads monthly rent', () => {
  expect(parsePrice('80k')).toBe(80000);
  expect(parseArgs(['--max-rent', '80k']).crit).toMatchObject({ mode: 'rent', maxRent: 80000 });
});

it('defaults to bangalore and finds verified Bengaluru societies', () => {
  const city = JSON.parse(readFileSync(new URL('../web/public/data/bangalore.json', import.meta.url)));
  const o = parseArgs(['--bhk', '3,4', '--min-bedroom', "11'0x12'0", '--min-sqft', '1650', '--amenity', 'squash']);
  expect(o.city).toBe('bangalore');
  const names = search(city, o).map((r) => r.s.name);
  expect(names).toContain('Prestige Shantiniketan');
  expect(names).toContain('Sobha Royal Pavilion');
  expect(names).toContain('Brigade Gateway');
});
