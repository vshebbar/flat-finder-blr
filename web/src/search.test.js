import { expect, it } from 'vitest';
import { buildAreaIndex, normText, searchAreas, searchSocieties } from './search.js';

const S = [
  { name: 'M3M Golf Estate', developer: 'M3M India', locality: 'Sector 65' },
  { name: 'M3M Heights', developer: 'M3M India', locality: 'Sector 65' },
  { name: 'Conscient Heritage One', developer: 'Conscient', locality: 'Sector 62', verified: true },
  { name: 'Heritage Max', developer: 'Heritage', locality: 'Sector 102' },
];

const BLR = [
  { name: 'Purva Seasons', developer: 'Puravankara', locality: 'CV Raman Nagar, Indiranagar' },
  { name: 'Prestige Leela Residences', developer: 'Prestige Group', locality: 'HAL Old Airport Road, Indiranagar' },
  { name: 'SNN Raj Etternia', developer: 'SNN Estates', locality: 'HSR Layout Sector 2' },
  { name: 'Purva Westend', developer: 'Puravankara', locality: 'HSR Layout Sector 1' },
  { name: 'Ajmera Infinity', developer: 'Ajmera Group', locality: 'Electronic City Phase 1' },
  { name: 'Prestige Acropolis', developer: 'Prestige Group', locality: 'Koramangala 3rd Block' },
];

it('finds by partial name, ignoring case and punctuation', () => {
  expect(searchSocieties(S, 'heritage one')[0].name).toBe('Conscient Heritage One');
  expect(searchSocieties(S, 'GOLF').map((s) => s.name)).toEqual(['M3M Golf Estate']);
});

it('matches developer and sector words together', () => {
  expect(searchSocieties(S, 'm3m 65').length).toBe(2);
  expect(searchSocieties(S, 'sector 62').map((s) => s.name)).toEqual(['Conscient Heritage One']);
});

it('ranks names that start with the query first', () => {
  expect(searchSocieties(S, 'heritage')[0].name).toBe('Heritage Max');
});

it('empty query returns nothing', () => {
  expect(searchSocieties(S, '  ')).toEqual([]);
});

it('normalizes common Bengaluru spellings and abbreviations', () => {
  expect(normText('Kormangala')).toBe('koramangala');
  expect(normText('E-City')).toBe('electronic city');
  expect(normText('J P Nagar')).toBe('jp nagar');
  expect(normText('Rajarajeshwari Nagar')).toBe('rr nagar');
  expect(searchSocieties(BLR, 'kormangala').map((s) => s.name)).toEqual(['Prestige Acropolis']);
  expect(searchSocieties(BLR, 'ecity').map((s) => s.name)).toEqual(['Ajmera Infinity']);
});

it('builds canonical area index and searches areas by alias', () => {
  const areas = buildAreaIndex(BLR);
  expect(areas.find((a) => a.name === 'HSR Layout')?.n).toBe(2);
  expect(areas.find((a) => a.name === 'Indiranagar')?.n).toBe(2);
  expect(searchAreas(areas, 'indranagar')[0]?.name).toBe('Indiranagar');
  expect(searchAreas(areas, 'ecity')[0]?.name).toBe('Electronic City');
});

