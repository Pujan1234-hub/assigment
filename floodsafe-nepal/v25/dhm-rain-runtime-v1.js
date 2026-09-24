(() => {
  'use strict';
  if (window.__fsDhmRainRuntimeV1) return;
  window.__fsDhmRainRuntimeV1 = true;

  const DHM_PAGE = 'https://www.dhm.gov.np/hydrology/getRainfallData';
  const MIRROR = '/api/dhm-rain';
  const LIMITS = { 1: 60, 3: 80, 6: 100, 12: 120, 24: 140 };
  let rows = [];
  let baseRain = null;
  let timer = 0;

  const numberFrom = (value) => {
    const match = String(value || '').replace(/,/g, '').match(/-?\d+(?:\.\d+)?/);
    return match ? Number(match[0]) : null;
  };

  const normalize = (value) => String(value || '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, ' ')
    .replace(/\b(river|khola|nadi|station|rainfall|at)\b/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();

  const distanceKm = (a, b, c, d) => {
    const rad = (x) => x * Math.PI / 180;
    const q = Math.sin(rad(c - a) / 2) ** 2 + Math.cos(rad(a)) * Math.cos(rad(c)) * Math.sin(rad(d - b) / 2) ** 2;
    return 12742 * Math.asin(Math.sqrt(q));
  };

  function rememberBaseRain() {
    const current = window.FloodSafeRainRealtime;
    if (current && current !== api) baseRain = current;
    return baseRain;
  }

  function unpack(text) {
    try {
      const json = JSON.parse(text);
      if (typeof json === 'string') return json;
      if (typeof json?.html === 'string') return json.html;
    } catch {}
    return text;
  }

  function parseDhm(html) {
    const doc = new DOMParser().parseFromString(html, 'text/html');
    const parsed = [];
    for (const tr of doc.querySelectorAll('tbody tr')) {
      const cells = [...tr.querySelectorAll('td')].map((td) => td.textContent.replace(/\s+/g, ' ').trim());
      if (cells.length < 10) continue;
      const start = cells.length >= 11 ? 0 : Math.max(0, cells.length - 10);
      const values = {
        1: numberFrom(cells[start + 5]),
        3: numberFrom(cells[start + 6]),
        6: numberFrom(cells[start + 7]),
        12: numberFrom(cells[start + 8]),
        24: numberFrom(cells[start + 9])
      };
      const name = cells[start + 3] || '';
      if (!name || Object.values(values).every((v) => v === null)) continue;
      const statusText = cells[start + 10] || '';
      let risk = /danger|red/i.test(statusText) ? 'danger' : /warning|orange/i.test(statusText) ? 'warning' : 'normal';
      if (risk === 'normal' && Object.entries(values).some(([hours, value]) => value !== null && value >= LIMITS[hours])) risk = 'warning';
      parsed.push({
        stationId: cells[start + 2] || '',
        name,
        basin: cells[start + 1] || '',
        district: cells[start + 4] || '',
        values,
        riskStatus: risk,
        officialStatus: statusText,
        source: 'DHM',
        sourceUrl: 'https://www.dhm.gov.np/hydrology/rainfall-watch-map'
      });
    }
    return parsed;
  }

  function attachCoordinates(dhmRows) {
    const base = rememberBaseRain();
    const catalogue = base ? base.latest : [];
    return dhmRows.map((row) => {
      const id = String(row.stationId).trim();
      const wanted = normalize(row.name);
      let match = catalogue.find((item) => id && String(item.stationId || '').trim() === id) || null;
      if (!match) match = catalogue.find((item) => normalize(item.name) === wanted) || null;
      if (!match) match = catalogue.find((item) => {
        const candidate = normalize(item.name);
        return wanted && candidate && (wanted.includes(candidate) || candidate.includes(wanted));
      }) || null;
      const lat = Number(match?.lat);
      const lon = Number(match?.lon);
      const averages = Object.entries(row.values)
        .filter(([, value]) => value !== null)
        .map(([interval, value]) => ({ interval: Number(interval), value, warning: value >= LIMITS[interval], danger: false }));
      return {
        ...row,
        lat: Number.isFinite(lat) ? lat : null,
        lon: Number.isFinite(lon) ? lon : null,
        rainfall1h: row.values[1],
        averages,
        time: new Date().toISOString(),
        isCurrent: true,
        coordinateSource: match ? 'BIPAD station catalogue metadata' : null
      };
    });
  }

  function nearby(lat, lon, maxKm = 80, limit = 30) {
    return rows
      .filter((row) => Number.isFinite(row.lat) && Number.isFinite(row.lon))
      .map((row) => ({ ...row, distanceKm: distanceKm(lat, lon, row.lat, row.lon) }))
      .filter((row) => row.distanceKm <= maxKm)
      .sort((a, b) => a.distanceKm - b.distanceKm)
      .slice(0, limit);
  }

  const api = {
    poll: () => poll(),
    nearby,
    forPoint: (lat, lon, maxKm = 80) => nearby(lat, lon, maxKm, 1)[0] || null,
    averageRows: (row) => row?.averages || [],
    rainAt: (row, interval = 1) => row?.averages?.find((x) => x.interval === Number(interval))?.value ?? null,
    riskStage: (row) => row?.riskStatus || 'normal',
    isCurrent: () => true,
    get latest() { return rows.slice(); },
    get current() { return rows.slice(); },
    get state() { return window.__fsDhmRainState || null; },
    AUTHORITY: 'DHM'
  };

  function showSource(ok) {
    let node = document.getElementById('fsOfficialSourceStatus');
    if (!node) {
      const anchor = document.getElementById('weatherSupport');
      if (!anchor) return;
      node = document.createElement('div');
      node.id = 'fsOfficialSourceStatus';
      node.className = 'muted';
      node.style.cssText = 'margin-top:5px;font-size:.76rem;font-weight:700';
      anchor.insertAdjacentElement('afterend', node);
    }
    node.textContent = ok
      ? `नदी: BIPAD official realtime • वर्षा: DHM official mirror • ${rows.length} rainfall stations`
      : 'नदी: BIPAD official realtime • वर्षा: DHM mirror reconnect हुँदैछ…';
  }

  async function fetchText(url) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 12000);
    try {
      const response = await fetch(`${url}${url.includes('?') ? '&' : '?'}_fs=${Date.now()}`, { cache: 'no-store', signal: controller.signal });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return unpack(await response.text());
    } finally {
      clearTimeout(timeout);
    }
  }

  async function poll() {
    rememberBaseRain();
    let parsed = [];
    let mode = '';
    let error = '';
    for (const url of [MIRROR, DHM_PAGE]) {
      try {
        parsed = parseDhm(await fetchText(url));
        if (parsed.length) {
          mode = url === MIRROR ? 'dhm-mirror' : 'dhm-direct';
          break;
        }
      } catch (e) {
        error = String(e?.message || e);
      }
    }
    if (parsed.length) {
      rows = attachCoordinates(parsed);
      if (rows.some((row) => Number.isFinite(row.lat) && Number.isFinite(row.lon))) window.FloodSafeRainRealtime = api;
      window.__fsDhmRainState = { ok: true, authority: 'DHM', mode, count: rows.length, updatedAt: new Date().toISOString() };
      showSource(true);
      window.dispatchEvent(new CustomEvent('fsdhmrainupdate', { detail: window.__fsDhmRainState }));
    } else {
      window.__fsDhmRainState = { ok: false, authority: 'DHM', mode: 'retry', error, updatedAt: new Date().toISOString() };
      showSource(false);
    }
    clearTimeout(timer);
    timer = setTimeout(poll, document.hidden ? 120000 : 30000);
  }

  function boot() {
    rememberBaseRain();
    window.FloodSafeDhmRain = api;
    poll();
    window.addEventListener('online', poll);
    window.addEventListener('focus', poll);
    document.addEventListener('visibilitychange', () => {
      clearTimeout(timer);
      timer = setTimeout(poll, document.hidden ? 120000 : 1000);
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot, { once: true });
  else boot();
})();
