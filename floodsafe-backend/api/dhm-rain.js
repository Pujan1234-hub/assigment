const DHM_RAINFALL_URL = 'https://www.dhm.gov.np/hydrology/getRainfallData';

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Cache-Control', 'public, s-maxage=20, stale-while-revalidate=60');

  if (req.method === 'OPTIONS') return res.status(204).end();
  if (req.method !== 'GET') return res.status(405).json({ ok: false, error: 'GET only' });

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 12000);
  try {
    const upstream = await fetch(DHM_RAINFALL_URL, {
      headers: {
        accept: 'text/html,application/json;q=0.9,*/*;q=0.8',
        'user-agent': 'FloodSafe-Nepal/1.0'
      },
      signal: controller.signal
    });
    if (!upstream.ok) throw new Error(`DHM upstream ${upstream.status}`);
    const html = await upstream.text();
    return res.status(200).json({
      ok: true,
      authority: 'DHM',
      source_url: DHM_RAINFALL_URL,
      fetched_at: new Date().toISOString(),
      html
    });
  } catch (error) {
    return res.status(503).json({
      ok: false,
      authority: 'DHM',
      source_url: DHM_RAINFALL_URL,
      error: String(error?.message || error)
    });
  } finally {
    clearTimeout(timeout);
  }
}
