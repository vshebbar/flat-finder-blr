import { expect, it } from 'vitest';
import { searchSocieties } from './search.js';

const S = [
  { name: 'M3M Golf Estate', developer: 'M3M India', locality: 'Sector 65' },
  { name: 'M3M Heights', developer: 'M3M India', locality: 'Sector 65' },
  { name: 'Conscient Heritage One', developer: 'Conscient', locality: 'Sector 62', verified: true },
  { name: 'Heritage Max', developer: 'Heritage', locality: 'Sector 102' },
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
