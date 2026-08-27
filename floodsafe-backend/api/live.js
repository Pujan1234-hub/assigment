const SOURCES = {
  rivers: 'https://bipadportal.gov.np/api/v1/river-stations/?limit=650',
  rain: 'https://bipadportal.gov.np/api/v1/rain-stations/?limit=650',
  alerts: 'https://bipadportal.gov.np/api/v1/alert/?limit=250&ordering=-createdOn',
  roads: 'https://bipadportal.gov.np/api/v1/highway/?limit=500',
  incidents: 'https://bipadportal.gov.np/api/v1/incident/?limit=500&ordering=-incidentOn'
};

const memory = globalThis.__floodsafeCache || (globalThis.__floodsafeCache = { value: null, expires: 0, pending: null });
const TTL_MS = 2000;

async function readJson(url) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 8000);
  try {
    const r = await fetch(url, { headers: { accept: 'application/json', 'user-agent': 'FloodSafe-Nepal/1.0' }, signal: ctrl.signal });
    if (!r.ok) throw new Error(`upstream ${r.status}`);
    return await r.json();
  } finally { clearTimeout(timer); }
}

async function buildSnapshot() {
  const started = Date.now();
  const entries = await Promise.allSettled(Object.entries(SOURCES).map(async ([key, url]) => [key, await readJson(url)]));
  const data = {}, source_status = {};
  for (const item of entries) {
    if (item.status === 'fulfilled') {
      const [key, value] = item.value;
      data[key] = value;
      source_status[key] = 'ok';
    }
  }
  for (const key of Object.keys(SOURCES)) if (!(key in source_status)) source_status[key] = 'unavailable';
  return {
    ok: true,
    generated_at: new Date().toISOString(),
    generated_ms: Date.now() - started,
    cache_ttl_ms: TTL_MS,
    source_status,
    data
  };
}

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Cache-Control', 'public, s-maxage=2, stale-while-revalidate=30');
  if (req.method === 'OPTIONS') return res.status(204).end();
  if (req.method !== 'GET') return res.status(405).json({ ok: false, error: 'GET only' });

  const now = Date.now();
  if (memory.value && memory.expires > now) {
    res.setHeader('X-FloodSafe-Cache', 'HIT');
    return res.status(200).json(memory.value);
  }

  try {
    if (!memory.pending) memory.pending = buildSnapshot();
    const snapshot = await memory.pending;
    memory.value = snapshot;
    memory.expires = Date.now() + TTL_MS;
    memory.pending = null;
    res.setHeader('X-FloodSafe-Cache', 'MISS');
    return res.status(200).json(snapshot);
  } catch (e) {
    memory.pending = null;
    if (memory.value) {
      res.setHeader('X-FloodSafe-Cache', 'STALE');
      return res.status(200).json({ ...memory.value, stale: true, stale_reason: String(e?.message || e) });
    }
    return res.status(503).json({ ok: false, error: 'Upstream data temporarily unavailable' });
  }
}
