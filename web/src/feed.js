// Research log: replays real provenance events. Never invents steps.
const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

export function createFeed(el, modeEl, { events, byId }) {
  let timer = null;
  const verifiedEvents = events.filter((e) => e.verified);
  const ambientPool = verifiedEvents.length ? verifiedEvents : events;

  function push(e, { onEach } = {}) {
    const s = byId.get(e.sid);
    const d = document.createElement('div');
    if (e.verified) d.className = 'v';
    const link = e.url ? `<a href="${esc(e.url)}" target="_blank" rel="noopener">${esc(e.step)}</a>` : esc(e.step);
    d.innerHTML = `${link} · <em>${esc(s?.name)}</em><br><b>${esc(e.finding)}</b>`;
    el.prepend(d);
    requestAnimationFrame(() => d.classList.add('on'));
    while (el.children.length > 14) el.lastChild.remove();
    onEach?.(e);
  }

  function stop() { clearInterval(timer); timer = null; }

  function ambient() {
    stop();
    modeEl.textContent = 'replay';
    let i = Math.floor(Math.random() * ambientPool.length);
    timer = setInterval(() => push(ambientPool[i++ % ambientPool.length]), 1900);
  }

  function play(sid, onEach) {
    stop();
    el.innerHTML = '';
    modeEl.textContent = 'this society';
    const list = events.filter((e) => e.sid === sid);
    let i = 0;
    timer = setInterval(() => {
      if (i >= list.length) { stop(); return; }
      push(list[i++], { onEach });
    }, 650);
  }

  // Intro: a fast sweep that names real societies as they are indexed.
  function sweep(societies, ms) {
    stop();
    modeEl.textContent = 'indexing';
    const pick = societies.filter((s) => s.units || s.verified).sort(() => Math.random() - 0.5).slice(0, 18);
    let i = 0;
    timer = setInterval(() => {
      if (i >= pick.length) { ambient(); return; }
      const s = pick[i++];
      push({ sid: s.id, step: 'Indexed', finding: [s.locality, s.towers && `${s.towers} towers`, s.units && `${s.units} units`].filter(Boolean).join(' · '), url: s.url });
    }, ms / pick.length);
  }

  return { ambient, play, sweep, stop };
}
