import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

const COLORS = { match: '#ffd9a0', likely: '#c99a5c', probable: '#9a8463', unknown: '#55545c', no: '#1b1b1e' };
export const OVERVIEW = { center: [77.60, 12.97], zoom: 11.4, pitch: 50, bearing: 0 };

const stateColor = (fallback) => ['case',
  ['boolean', ['feature-state', 'sel'], false], '#ffffff',
  ['match', ['feature-state', 'st'], 'match', COLORS.match, 'likely', COLORS.likely, 'probable', COLORS.probable, 'unknown', COLORS.unknown, 'no', COLORS.no, fallback]];

export function createMap(container, { mobile }) {
  const map = new maplibregl.Map({
    container,
    attributionControl: { compact: true },
    center: mobile ? OVERVIEW.center : [78.5, 22.5],
    zoom: mobile ? 11.6 : 2.2,
    pitch: mobile ? 45 : 0,
    bearing: 0,
    maxPitch: 70,
    dragRotate: false,      // north stays up, like Google Maps
    pitchWithRotate: false,
    touchPitch: false,
    style: {
      version: 8,
      projection: { type: 'globe' },
      glyphs: 'https://tiles.openfreemap.org/fonts/{fontstack}/{range}.pbf',
      sky: { 'sky-color': '#07080b', 'horizon-color': '#1a1712', 'fog-color': '#07080b', 'sky-horizon-blend': 0.6,
        'horizon-fog-blend': 0.6, 'fog-ground-blend': 0.2, 'atmosphere-blend': ['interpolate', ['linear'], ['zoom'], 0, 1, 10, 0] },
      sources: {
        sat: { type: 'raster', tileSize: 256, maxzoom: 18, attribution: 'Imagery © Esri',
          tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'] },
        omt: { type: 'vector', url: 'https://tiles.openfreemap.org/planet', attribution: '© OpenStreetMap contributors · OpenFreeMap' },
      },
      layers: [
        { id: 'bg', type: 'background', paint: { 'background-color': '#050506' } },
        { id: 'sat', type: 'raster', source: 'sat', paint: { 'raster-brightness-max': 0.3, 'raster-saturation': -0.75, 'raster-contrast': 0.15, 'raster-hue-rotate': 200 } },
        { id: 'roads', type: 'line', source: 'omt', 'source-layer': 'transportation',
          filter: ['in', ['get', 'class'], ['literal', ['motorway', 'trunk', 'primary', 'secondary']]],
          paint: { 'line-color': '#ffcf8a', 'line-opacity': 0.2, 'line-width': ['interpolate', ['linear'], ['zoom'], 10, 0.5, 16, 2.5], 'line-blur': 1 } },
        { id: 'city', type: 'fill-extrusion', source: 'omt', 'source-layer': 'building', minzoom: 13,
          paint: { 'fill-extrusion-color': '#17171a', 'fill-extrusion-height': ['coalesce', ['get', 'render_height'], 8],
            'fill-extrusion-base': ['coalesce', ['get', 'render_min_height'], 0], 'fill-extrusion-opacity': 0.85 } },
      ],
    },
  });
  map.touchZoomRotate.disableRotation();
  map.keyboard.disableRotation();
  map.addControl(new maplibregl.ScaleControl({ unit: 'metric', maxWidth: 90 }), 'bottom-right');
  return map;
}

export function addSocietyLayers(map, shapes, points) {
  map.addSource('shapes', { type: 'geojson', data: shapes, promoteId: 'sid' });
  map.addSource('pts', { type: 'geojson', data: points, promoteId: 'sid' });
  map.addLayer({ id: 'site-fill', type: 'fill', source: 'shapes', filter: ['==', ['get', 'role'], 'site'],
    paint: { 'fill-color': stateColor(COLORS.match),
      'fill-opacity': ['match', ['feature-state', 'st'], 'match', 0.13, 'likely', 0.1, 'probable', 0.1, 'unknown', 0.05, 'no', 0, 0.08] } });
  map.addLayer({ id: 'site-line', type: 'line', source: 'shapes', filter: ['==', ['get', 'role'], 'site'],
    paint: { 'line-color': stateColor(COLORS.match), 'line-blur': 1.5,
      'line-width': ['interpolate', ['linear'], ['zoom'], 11, 0.6, 16, 2],
      'line-opacity': ['match', ['feature-state', 'st'], 'match', 0.9, 'likely', 0.7, 'probable', 0.7, 'unknown', 0.5, 'no', 0.05, 0.5] } });
  map.addLayer({ id: 'glow', type: 'circle', source: 'pts', maxzoom: 15.5,
    paint: { 'circle-color': stateColor(COLORS.match), 'circle-blur': 1,
      'circle-radius': ['interpolate', ['linear'], ['zoom'], 9, 2, 12, 6, 15, 24],
      'circle-opacity': ['match', ['feature-state', 'st'], 'match', 0.5, 'likely', 0.35, 'probable', 0.35, 'unknown', 0.14, 'no', 0, 0.25] } });
  map.addLayer({ id: 'bld', type: 'fill-extrusion', source: 'shapes', minzoom: 11.5, filter: ['==', ['get', 'role'], 'bld'],
    paint: { 'fill-extrusion-color': stateColor(COLORS.match), 'fill-extrusion-height': ['get', 'h'], 'fill-extrusion-opacity': 0.95,
      'fill-extrusion-vertical-gradient': true } });
  map.addLayer({ id: 'labels', type: 'symbol', source: 'pts', minzoom: 13.2,
    filter: ['==', ['get', 'show'], 1],
    layout: { 'text-field': ['get', 'name'], 'text-font': ['Noto Sans Regular'], 'text-size': 11.5, 'text-offset': [0, -2.2],
      'text-letter-spacing': 0.04, 'text-optional': true },
    paint: { 'text-color': '#f2f0ec', 'text-halo-color': 'rgba(0,0,0,.85)', 'text-halo-width': 1.4,
      'text-opacity': ['match', ['feature-state', 'st'], 'match', 1, 'likely', 0.85, 'probable', 0.85, 'unknown', 0.35, 'no', 0, 0.7] } });
}

// Pulse the glow of matches. Cheap: one paint property on ~2,700 circles.
export function startPulse(map) {
  setInterval(() => {
    if (!map.getLayer('glow')) return;
    const k = 1 + 0.35 * Math.sin(performance.now() / 420);
    map.setPaintProperty('glow', 'circle-radius', ['interpolate', ['linear'], ['zoom'], 9, 2 * k, 12, 6 * k, 15, 24 * k]);
  }, 80);
}

export function setStates(map, entries) {
  for (const [sid, st] of entries) {
    map.setFeatureState({ source: 'shapes', id: sid }, { st });
    map.setFeatureState({ source: 'pts', id: sid }, { st });
  }
}

export function setSelected(map, sid, prev) {
  if (prev) for (const src of ['shapes', 'pts']) map.setFeatureState({ source: src, id: prev }, { sel: false });
  if (sid) for (const src of ['shapes', 'pts']) map.setFeatureState({ source: src, id: sid }, { sel: true });
}

// ---------- Streets view: a dark street map with road and area names, from OpenFreeMap vector tiles ----------
const ROAD_W = (major, minor) => ['interpolate', ['exponential', 1.5], ['zoom'], 10, ['match', ['get', 'class'], ['motorway', 'trunk'], major * 0.4, ['primary', 'secondary'], minor * 0.5, 0.3],
  17, ['match', ['get', 'class'], ['motorway', 'trunk'], major * 5, ['primary', 'secondary'], minor * 5, ['tertiary', 'minor'], 8, 4]];
const STREET_LAYERS = [
  { id: 'st-bg', type: 'background', paint: { 'background-color': '#202124' } },
  { id: 'st-green', type: 'fill', source: 'omt', 'source-layer': 'landcover', filter: ['in', ['get', 'class'], ['literal', ['grass', 'wood', 'farmland']]], paint: { 'fill-color': '#1f2a22', 'fill-opacity': 0.8 } },
  { id: 'st-park', type: 'fill', source: 'omt', 'source-layer': 'park', paint: { 'fill-color': '#22311f', 'fill-opacity': 0.9 } },
  { id: 'st-water', type: 'fill', source: 'omt', 'source-layer': 'water', paint: { 'fill-color': '#15233a' } },
  { id: 'st-casing', type: 'line', source: 'omt', 'source-layer': 'transportation',
    filter: ['in', ['get', 'class'], ['literal', ['motorway', 'trunk', 'primary', 'secondary', 'tertiary', 'minor']]],
    layout: { 'line-cap': 'round', 'line-join': 'round' }, paint: { 'line-color': '#0f0f11', 'line-width': ROAD_W(5.5, 4.5), 'line-gap-width': 0 } },
  { id: 'st-road', type: 'line', source: 'omt', 'source-layer': 'transportation',
    filter: ['in', ['get', 'class'], ['literal', ['motorway', 'trunk', 'primary', 'secondary', 'tertiary', 'minor', 'service']]],
    layout: { 'line-cap': 'round', 'line-join': 'round' },
    paint: { 'line-color': ['match', ['get', 'class'], ['motorway', 'trunk'], '#a08a66', ['primary', 'secondary'], '#646a75', ['tertiary'], '#4d5159', '#3d4047'], 'line-width': ROAD_W(4.5, 3.5) } },
  { id: 'st-rail', type: 'line', source: 'omt', 'source-layer': 'transportation', filter: ['==', ['get', 'class'], 'rail'],
    paint: { 'line-color': '#5b5b66', 'line-width': 1.2, 'line-dasharray': [3, 2] } },
];
// Names: shown in both views so people can tell which road is which.
const LABEL_LAYERS = [
  { id: 'lbl-road', type: 'symbol', source: 'omt', 'source-layer': 'transportation_name', minzoom: 12.5,
    filter: ['in', ['get', 'class'], ['literal', ['motorway', 'trunk', 'primary', 'secondary', 'tertiary']]],
    layout: { 'symbol-placement': 'line', 'text-field': ['coalesce', ['get', 'name:en'], ['get', 'name']], 'text-font': ['Noto Sans Regular'],
      'text-size': ['interpolate', ['linear'], ['zoom'], 12.5, 10, 17, 13], 'text-letter-spacing': 0.04, 'text-max-angle': 30 },
    paint: { 'text-color': '#e4dfd5', 'text-halo-color': 'rgba(0,0,0,.9)', 'text-halo-width': 1.5 } },
  { id: 'lbl-place', type: 'symbol', source: 'omt', 'source-layer': 'place', minzoom: 10,
    filter: ['in', ['get', 'class'], ['literal', ['suburb', 'neighbourhood', 'quarter', 'village', 'town', 'city']]],
    layout: { 'text-field': ['coalesce', ['get', 'name:en'], ['get', 'name']], 'text-font': ['Noto Sans Bold'],
      'text-size': ['match', ['get', 'class'], ['city', 'town'], 15, 11.5], 'text-transform': 'uppercase', 'text-letter-spacing': 0.12 },
    paint: { 'text-color': '#9d988e', 'text-halo-color': 'rgba(0,0,0,.85)', 'text-halo-width': 1.2 } },
  { id: 'lbl-metro', type: 'symbol', source: 'omt', 'source-layer': 'poi', minzoom: 12.5,
    filter: ['in', ['get', 'class'], ['literal', ['railway']]],
    layout: { 'text-field': ['coalesce', ['get', 'name:en'], ['get', 'name']], 'text-font': ['Noto Sans Regular'], 'text-size': 11, 'text-offset': [0, 0.8] },
    paint: { 'text-color': '#8fb4ff', 'text-halo-color': 'rgba(0,0,0,.85)', 'text-halo-width': 1.2 } },
];

export function addBaseLayers(map) {
  for (const l of STREET_LAYERS) map.addLayer({ ...l, layout: { ...(l.layout || {}), visibility: 'none' } }, 'city');
  for (const l of LABEL_LAYERS) map.addLayer(l); // above everything, including societies
}

// Building colours per base map. Light needs darker "match" colours and pale "no" colours.
const PALETTES = {
  night: { match: '#ffd9a0', likely: '#c99a5c', probable: '#9a8463', unknown: '#55545c', no: '#1b1b1e', sel: '#ffffff', city: '#17171a', label: '#f2f0ec', halo: 'rgba(0,0,0,.85)' },
  streets: { match: '#ffd9a0', likely: '#c99a5c', probable: '#9a8463', unknown: '#5d5c64', no: '#2c2d31', sel: '#ffffff', city: '#2a2b30', label: '#f2f0ec', halo: 'rgba(0,0,0,.85)' },
  light: { match: '#e8710a', likely: '#f2a93b', probable: '#f6c896', unknown: '#a9a6a0', no: '#e4e1db', sel: '#1a73e8', city: '#e8e5df', label: '#202124', halo: 'rgba(255,255,255,.95)' },
};
const LIGHT = { // Google-like day map
  'st-bg': { 'background-color': '#f5f3ef' }, 'st-green': { 'fill-color': '#d8ead2' }, 'st-park': { 'fill-color': '#c8e6c4' },
  'st-water': { 'fill-color': '#aadaff' }, 'st-casing': { 'line-color': '#d6d3cd' },
  'st-road': { 'line-color': ['match', ['get', 'class'], ['motorway', 'trunk'], '#fbd277', ['primary', 'secondary'], '#ffffff', '#ffffff'] },
  'st-rail': { 'line-color': '#b0aeb8' },
  'lbl-road': { 'text-color': '#4d5156', 'text-halo-color': '#ffffff' }, 'lbl-place': { 'text-color': '#5f6368', 'text-halo-color': '#ffffff' },
  'lbl-metro': { 'text-color': '#1a73e8', 'text-halo-color': '#ffffff' },
};
const DARK = {
  'st-bg': { 'background-color': '#202124' }, 'st-green': { 'fill-color': '#1f2a22' }, 'st-park': { 'fill-color': '#22311f' },
  'st-water': { 'fill-color': '#15233a' }, 'st-casing': { 'line-color': '#0f0f11' },
  'st-road': { 'line-color': ['match', ['get', 'class'], ['motorway', 'trunk'], '#a08a66', ['primary', 'secondary'], '#646a75', ['tertiary'], '#4d5159', '#3d4047'] },
  'st-rail': { 'line-color': '#5b5b66' },
  'lbl-road': { 'text-color': '#e4dfd5', 'text-halo-color': 'rgba(0,0,0,.9)' }, 'lbl-place': { 'text-color': '#9d988e', 'text-halo-color': 'rgba(0,0,0,.85)' },
  'lbl-metro': { 'text-color': '#8fb4ff', 'text-halo-color': 'rgba(0,0,0,.85)' },
};

const colorBy = (c) => ['case', ['boolean', ['feature-state', 'sel'], false], c.sel,
  ['match', ['feature-state', 'st'], 'match', c.match, 'likely', c.likely, 'probable', c.probable, 'unknown', c.unknown, 'no', c.no, c.match]];

export const BASE_MODES = ['night', 'streets', 'light'];

export function setBaseMode(map, mode) {
  const streetsLike = mode !== 'night';
  for (const l of STREET_LAYERS) map.setLayoutProperty(l.id, 'visibility', streetsLike ? 'visible' : 'none');
  map.setLayoutProperty('sat', 'visibility', streetsLike ? 'none' : 'visible');
  map.setLayoutProperty('roads', 'visibility', streetsLike ? 'none' : 'visible');
  map.setLayoutProperty('lbl-metro', 'visibility', streetsLike ? 'visible' : 'none');
  for (const [id, props] of Object.entries(mode === 'light' ? LIGHT : DARK)) for (const [k, v] of Object.entries(props)) map.setPaintProperty(id, k, v);
  const c = PALETTES[mode];
  map.setPaintProperty('city', 'fill-extrusion-color', c.city);
  for (const [id, prop] of [['bld', 'fill-extrusion-color'], ['site-fill', 'fill-color'], ['site-line', 'line-color'], ['glow', 'circle-color']]) map.setPaintProperty(id, prop, colorBy(c));
  map.setPaintProperty('labels', 'text-color', c.label);
  map.setPaintProperty('labels', 'text-halo-color', c.halo);
  map.setPaintProperty('glow', 'circle-opacity', ['match', ['feature-state', 'st'], 'match', mode === 'light' ? 0.28 : 0.5, 'likely', mode === 'light' ? 0.2 : 0.35, 'probable', mode === 'light' ? 0.2 : 0.35, 'unknown', mode === 'light' ? 0.06 : 0.14, 'no', 0, 0.2]);
  map.setPaintProperty('site-fill', 'fill-opacity', ['match', ['feature-state', 'st'], 'match', mode === 'light' ? 0.22 : 0.13, 'likely', 0.12, 'probable', 0.12, 'unknown', 0.06, 'no', 0, 0.08]);
  map.setSky(mode === 'light'
    ? { 'sky-color': '#cfe3f5', 'horizon-color': '#eef3f7', 'fog-color': '#f5f3ef', 'sky-horizon-blend': 0.6, 'horizon-fog-blend': 0.6, 'fog-ground-blend': 0.2, 'atmosphere-blend': ['interpolate', ['linear'], ['zoom'], 0, 1, 10, 0] }
    : { 'sky-color': '#07080b', 'horizon-color': '#1a1712', 'fog-color': '#07080b', 'sky-horizon-blend': 0.6, 'horizon-fog-blend': 0.6, 'fog-ground-blend': 0.2, 'atmosphere-blend': ['interpolate', ['linear'], ['zoom'], 0, 1, 10, 0] });
}

// Let people switch off the glow, the society boundaries or the name labels when they get too busy.
export function setHighlights(map, { glow = true, bounds = true, labels = true } = {}) {
  if (!map.getLayer('glow')) return;
  map.setLayoutProperty('glow', 'visibility', glow ? 'visible' : 'none');
  map.setLayoutProperty('site-fill', 'visibility', bounds ? 'visible' : 'none');
  map.setLayoutProperty('site-line', 'visibility', bounds ? 'visible' : 'none');
  map.setLayoutProperty('labels', 'visibility', labels ? 'visible' : 'none');
}
