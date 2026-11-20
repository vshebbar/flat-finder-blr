import { describe, expect, it } from 'vitest';
import { DEFAULT_CRITERIA, feetLabel, matchSociety, roomPasses } from './filters.js';

const ROOM = { a: 11.25, b: 12.25 }; // 11'3" x 12'3"
const soc = (over = {}) => ({ kind: 'apartment', status: 'Ready To Move', amenities: [], amen_facts: {}, unit_types: [], ...over });
const crit = (over = {}) => ({ ...DEFAULT_CRITERIA, ...over });

describe('rooms', () => {
  it('11\'7" x 16\'0" passes, orientation-free', () => {
    expect(roomPasses([11.583, 16], ROOM)).toBe(true);
    expect(roomPasses([11.583, 16], { a: 12.25, b: 11.25 })).toBe(true);
  });
  it('10\'0" x 14\'0" fails even though the area is larger', () => {
    expect(roomPasses([10, 14], ROOM)).toBe(false);
  });
});

describe('matchSociety', () => {
  const unit = (bedrooms, complete, bhk = 3) => ({ bhk, super_sqft: 2000, bedrooms, rooms_complete: complete });

  it('no room data gives "unknown", never pass or fail', () => {
    const s = soc({ unit_types: [{ bhk: 3, size_sqft: 2000, bedrooms: [], rooms_complete: false }] });
    expect(matchSociety(s, crit({ room: ROOM }))).toBe('unknown');
  });
  it('incomplete rooms that pass give "likely"', () => {
    expect(matchSociety(soc({ unit_types: [unit([[12, 13]], false)] }), crit({ room: ROOM }))).toBe('likely');
  });
  it('complete rooms that pass give "match"', () => {
    expect(matchSociety(soc({ unit_types: [unit([[11.25, 12.25], [12, 14], [13, 15]], true)] }), crit({ room: ROOM }))).toBe('match');
  });
  it('one failing room fails the unit; another unit can still pass', () => {
    const s = soc({ unit_types: [unit([[11, 13]], true), unit([[12, 13], [12, 14], [13, 15], [14, 16]], true, 4)] });
    expect(matchSociety(s, crit({ room: ROOM, bhk: [3] }))).toBe('no');
    expect(matchSociety(s, crit({ room: ROOM }))).toBe('match');
  });
  it('a society with no unit data is "unknown" under a BHK filter', () => {
    expect(matchSociety(soc(), crit({ bhk: [3] }))).toBe('unknown');
  });
  it('verified amenity facts beat the portal list', () => {
    const s = soc({ amenities: ['Swimming Pool'], amen_facts: { squash: { value: 'yes' } } });
    expect(matchSociety(s, crit({ amenities: ['squash', 'pool'] }))).toBe('match');
    expect(matchSociety(soc({ amenities: ['Gymnasium'] }), crit({ amenities: ['squash'] }))).toBe('no');
  });
  it('plots are hidden by the default apartment filter', () => {
    expect(matchSociety(soc({ kind: 'plot' }), crit())).toBe('no');
  });
  it('minimum size uses super area, then portal size', () => {
    const s = soc({ unit_types: [{ bhk: 3, size_sqft: 1500, bedrooms: [] }] });
    expect(matchSociety(s, crit({ minSqft: 1620 }))).toBe('no');
    expect(matchSociety(s, crit({ minSqft: 1400 }))).toBe('match');
  });
});

it('feetLabel', () => {
  expect(feetLabel(11.25)).toBe('11\'3"');
  expect(feetLabel(12.833)).toBe('12\'10"');
});

import { formatINR, priceFor } from './filters.js';

describe('buy and rent', () => {
  const s = soc({ prices: { 3: { buy: { median: 3e7, n: 4 }, rent: { median: 70000 } }, 4: { buy_est: { value: 4e7, basis: 'x' }, rent_est: { value: 80000, basis: 'y' } } } });
  it('uses listing medians before estimates, cheapest BHK first', () => {
    expect(priceFor(s, 'rent', [])).toMatchObject({ value: 70000, estimated: false, bhk: 3 });
    expect(priceFor(s, 'buy', [4])).toMatchObject({ value: 4e7, estimated: true, basis: 'x' });
  });
  it('rent budget filters on monthly rent; unknown price never excludes', () => {
    expect(matchSociety(s, crit({ mode: 'rent', maxRent: 60000 }))).toBe('no');
    expect(matchSociety(s, crit({ mode: 'rent', maxRent: 75000 }))).toBe('match');
    expect(matchSociety(soc(), crit({ mode: 'rent', maxRent: 10000 }))).toBe('match');
  });
  it('formats rupees', () => {
    expect(formatINR(41500000)).toBe('₹4.15 Cr');
    expect(formatINR(70000)).toBe('₹70k');
    expect(formatINR(250000)).toBe('₹2.5 L');
  });
});

describe('room estimates, area mode, nearby, lists', () => {
  const big = soc({ id: 'c', unit_types: [{ bhk: 4, size_sqft: 7400, bedrooms: [], est_short: 11.81, est_area: 190 }] });
  it('a big unread unit is "probable" only, and only when estimates are allowed', () => {
    expect(matchSociety(big, crit({ room: ROOM }))).toBe('probable');
    expect(matchSociety(big, crit({ room: ROOM, estimates: false }))).toBe('unknown');
    expect(matchSociety(big, crit({ room: { a: 12, b: 13 } }))).toBe('unknown');
  });
  it('area mode checks every bedroom area', () => {
    const s = soc({ unit_types: [{ bhk: 3, bedrooms: [[11, 13], [12, 14]], rooms_complete: true }] });
    expect(matchSociety(s, crit({ roomArea: 140 }))).toBe('match');
    expect(matchSociety(s, crit({ roomArea: 150 }))).toBe('no');
    expect(matchSociety(big, crit({ roomArea: 180 }))).toBe('probable');
  });
  it('nearby, name search and my list', () => {
    const s = soc({ id: 'x', name: 'M3M Golf Estate', nearby: { park: { m: 300 }, metro: { m: 4000 } } });
    expect(matchSociety(s, crit({ near: ['park'] }))).toBe('match');
    expect(matchSociety(s, crit({ near: ['metro'] }))).toBe('no');
    expect(matchSociety(s, crit({ q: 'golf' }))).toBe('match');
    expect(matchSociety(s, crit({ q: 'heritage' }))).toBe('no');
    expect(matchSociety(s, crit({ only: ['y'] }))).toBe('no');
  });
  it('custom amenity names from the full list', () => {
    expect(matchSociety(soc({ amenities: ['Banquet Hall'] }), crit({ amenities: ['n:banquet hall'] }))).toBe('match');
  });
});

describe('units read by Jev from floor plans', () => {
  const ai = (o) => soc({ unit_types: [{ bhk: 3, bedrooms: [], ai: { min_short: 11.5, long_lb: 12.5, long_ub: null, area_lb: 140, area_ub: 160, ...o } }] });
  it('passes only when every confirmed bound clears the need', () => {
    expect(matchSociety(ai(), crit({ room: ROOM }))).toBe('likely');
    expect(matchSociety(ai({ long_lb: 12 }), crit({ room: ROOM }))).toBe('unknown');
  });
  it('fails on a narrower read side or a denied step', () => {
    expect(matchSociety(ai({ min_short: 10.5 }), crit({ room: ROOM }))).toBe('no');
    expect(matchSociety(ai({ long_lb: null, long_ub: 12 }), crit({ room: ROOM }))).toBe('no');
  });
  it('area mode uses the confirmed area steps', () => {
    expect(matchSociety(ai(), crit({ roomArea: 135 }))).toBe('likely');
    expect(matchSociety(ai(), crit({ roomArea: 150 }))).toBe('unknown');
    expect(matchSociety(ai(), crit({ roomArea: 170 }))).toBe('no');
  });
});

describe('ranges', () => {
  const s = soc({ unit_types: [{ bhk: 3, size_sqft: 2000, bedrooms: [] }], prices: { 3: { buy: { median: 3e7 }, rent: { median: 70000 } } } });
  it('home size upper end', () => {
    expect(matchSociety(s, crit({ maxSqft: 1800 }))).toBe('no');
    expect(matchSociety(s, crit({ minSqft: 1500, maxSqft: 2500 }))).toBe('match');
  });
  it('price and rent lower end', () => {
    expect(matchSociety(s, crit({ minPrice: 4e7 }))).toBe('no');
    expect(matchSociety(s, crit({ mode: 'rent', minRent: 50000, maxRent: 80000 }))).toBe('match');
  });
});

describe('flagged prices', () => {
  it('skips a flagged listing median and falls back to the estimate', async () => {
    const { priceFor } = await import('./filters.js');
    const s = { prices: { 3: { rent: { median: 960000, n: 1 }, rent_est: { value: 90100, basis: 'yield' }, flags: { rent: 'typo' } } } };
    expect(priceFor(s, 'rent', [3])).toMatchObject({ value: 90100, estimated: true });
  });
});
