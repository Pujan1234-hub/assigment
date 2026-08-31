(() => {
  'use strict';

  if (window.__fsGaugeBridgeV24) return;
  window.__fsGaugeBridgeV24 = true;

  const SAME_RIVER_LOCAL_KM = 50;
  const REGIONAL_KM = 70;
  const LINE_EXACT_KM = 4.5;
  const UNNAMED_LINE_KM = 2.5;

  const num = v => {
    const n = Number(String(v ?? '').replace(/[^0-9.+-]/g, ''));
    return Number.isFinite(n) ? n : null;
  };

  const val = (o, keys) => {
    for (const k of keys) {
      const v = o?.[k];
      if (v !== undefined && v !== null && v !== '') return v;
    }
    return null;
  };

  const flat = o =>
    o &&
    typeof o === 'object' &&
    o.fields &&
    typeof o.fields === 'object'
      ? Object.assign({}, o.fields, o)
      : o;

  function coord(o) {
    o = flat(o);

    const rt = window.FloodSafeRiverRealtime?.coords?.(o);

    if (Array.isArray(rt) && rt.length >= 2) {
      return [+rt[1], +rt[0]];
    }

    const c =
      o?._stationCoordinate ||
      o?.point?.coordinates ||
      o?.location?.coordinates ||
      o?.geometry?.coordinates;

    if (
      Array.isArray(c) &&
      c.length >= 2 &&
      Number.isFinite(+c[0]) &&
      Number.isFinite(+c[1])
    ) {
      const a = +c[0];
      const b = +c[1];

      if (a >= 79.5 && a <= 89 && b >= 26 && b <= 31) {
        return [b, a];
      }

      if (b >= 79.5 && b <= 89 && a >= 26 && a <= 31) {
        return [a, b];
      }
    }

    const la = num(
      val(o, [
        'latitude',
        'lat',
        'stationLatitude',
        'station_latitude'
      ])
    );

    const lo = num(
      val(o, [
        'longitude',
        'lon',
        'lng',
        'stationLongitude',
        'station_longitude'
      ])
    );

    return la !== null && lo !== null
      ? [la, lo]
      : null;
  }

  const name = o =>
    String(
      val(flat(o), [
        'river_name',
        'riverName',
        'station_name',
        'stationName',
        'title',
        'name'
      ]) ||
        flat(o)?.station?.name ||
        'River station'
    );

  const basin = o =>
    String(
      val(flat(o), [
        'basin',
        'basin_name',
        'basinName'
      ]) || ''
    );

  const district = o =>
    String(
      val(flat(o), [
        'districtName',
        'district_name',
        'district'
      ]) || ''
    );

  const stationId = o =>
    String(
      val(flat(o), [
        'stationSeriesId',
        'station_series_id',
        'stationId',
        'station_id',
        'stationIndex',
        'station_index',
        'id'
      ]) || ''
    );

  const stamp = o =>
    val(flat(o), [
      '_measurementTime',
      'waterLevelOn',
      'water_level_on',
      'measuredOn',
      'measured_on',
      'measurementTime',
      'observationTime'
    ]);

  const level = o =>
    num(
      val(flat(o), [
        'waterLevel',
        'water_level',
        'currentWaterLevel',
        'current_water_level',
        'currentLevel',
        'current_level',
        'level',
        '_lastWaterLevel'
      ])
    );

  const warning = o =>
    num(
      val(flat(o), [
        'warningLevel',
        'warning_level',
        'warningThreshold',
        'warning_threshold',
        '_lastWarningLevel'
      ])
    );

  const danger = o =>
    num(
      val(flat(o), [
        'dangerLevel',
        'danger_level',
        'dangerThreshold',
        'danger_threshold',
        '_lastDangerLevel'
      ])
    );

  const discharge = o =>
    num(
      val(flat(o), [
        'discharge',
        'currentDischarge',
        'current_discharge',
        'flow',
        'flowRate',
        'flow_rate',
        '_lastDischarge'
      ])
    );

  const km = (a, b, c, d) => {
    const R = 6371;
    const rad = x => (x * Math.PI) / 180;

    const q =
      Math.sin(rad(c - a) / 2) ** 2 +
      Math.cos(rad(a)) *
        Math.cos(rad(c)) *
        Math.sin(rad(d - b) / 2) ** 2;

    return 2 * R * Math.asin(Math.sqrt(q));
  };

  function hasObservation(o) {
    return (
      level(o) !== null &&
      !!stamp(o)
    );
  }

  function clean(s) {
    return String(s || '')
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/\s+(?:at|near)\s+.*/i, ' ')
      .replace(/(?:नदी|नदि|खोला)/g, ' ')
      .replace(
        /\b(river|khola|nadi|stream|station|gauge|bridge|rls|hs)\b/g,
        ' '
      )
      .replace(/[^\p{L}\p{N}]+/gu, ' ')
      .replace(/\s+/g, ' ')
      .trim();
  }

  const ALIAS = new Map([
    ['भोटेकोशी', 'bhotekoshi'],
    ['भोटेकोसी', 'bhotekoshi'],
    ['bhote koshi', 'bhotekoshi'],
    ['bhote kosi', 'bhotekoshi'],
    ['सुनकोशी', 'sunkoshi'],
    ['sun koshi', 'sunkoshi'],
    ['सप्तकोशी', 'saptakoshi'],
    ['sapta koshi', 'saptakoshi'],
    ['कालीगण्डकी', 'kaligandaki'],
    ['kali gandaki', 'kaligandaki'],
    ['बुढीगण्डकी', 'budhigandaki'],
    ['बूढीगण्डकी', 'budhigandaki'],
    ['budi gandaki', 'budhigandaki'],
    ['मर्स्याङ्दी', 'marsyangdi'],
    ['marsyangdi', 'marsyangdi'],
    ['त्रिशूली', 'trishuli'],
    ['त्रिशुली', 'trishuli'],
    ['नारायणी', 'narayani'],
    ['कर्णाली', 'karnali'],
    ['महाकाली', 'mahakali'],
    ['बागमती', 'bagmati'],
    ['बबई', 'babai'],
    ['अरुण', 'arun'],
    ['तमोर', 'tamor'],
    ['कन्काई', 'kankai'],
    ['कमला', 'kamala'],
    ['मेची', 'mechi'],
    ['तिनाउ', 'tinau'],
    ['सेती', 'seti']
  ]);

  function canonical(s) {
    const c = clean(s);
    return ALIAS.get(c) || c;
  }

  function variants(w) {
    const list = [
      w?.name_en,
      w?.name_raw,
      w?.name,
      w?.name_ne
    ]
      .map(x => String(x || '').trim())
      .filter(Boolean);

    const seen = new Set();

    return list.filter(x => {
      const k = canonical(x);

      if (!k || seen.has(k)) return false;

      seen.add(k);
      return true;
    });
  }

  function editDistance(a, b) {
    a = canonical(a);
    b = canonical(b);

    if (!a || !b) return 99;

    const n = b.length;
    const prev = Array.from(
      { length: n + 1 },
      (_, i) => i
    );

    const curr = new Array(n + 1);

    for (let i = 1; i <= a.length; i++) {
      curr[0] = i;

      for (let j = 1; j <= n; j++) {
        curr[j] = Math.min(
          curr[j - 1] + 1,
          prev[j] + 1,
          prev[j - 1] +
            (a[i - 1] === b[j - 1] ? 0 : 1)
        );
      }

      for (let j = 0; j <= n; j++) {
        prev[j] = curr[j];
      }
    }

    return prev[n];
  }

  function scoreName(a, b) {
    const A = canonical(a);
    const B = canonical(b);

    if (!A || !B) return 0;

    if (A === B) return 100;

    if (
      A.length >= 4 &&
      B.length >= 4 &&
      (A.includes(B) || B.includes(A))
    ) {
      return 96;
    }

    const aa = A.split(' ').filter(x => x.length >= 3);
    const bb = B.split(' ').filter(x => x.length >= 3);

    const common =
      aa.filter(x => bb.includes(x));

    if (common.length) {
      const ratio =
        common.length /
        Math.max(aa.length, bb.length);

      if (ratio >= 0.75) return 93;
      if (ratio >= 0.5) return 88;
    }

    const mx = Math.max(A.length, B.length);

    const ed =
      mx <= 24
        ? editDistance(A, B)
        : 99;

    if (mx >= 5 && ed <= 1) return 94;
    if (mx >= 7 && ed <= 2) return 91;

    return 0;
  }

  function stage(o) {
    o = flat(o);

    const wl = level(o);
    const w = warning(o);
    const d = danger(o);

    const raw = String(
      val(o, [
        '_officialStatus',
        'status',
        'status_name',
        'alertStatus',
        'alert_status',
        'riskLevel',
        'risk_level'
      ]) || ''
    )
      .trim()
      .toUpperCase();

    let status = 'normal';

    if (
      wl !== null &&
      d !== null &&
      d > 0 &&
      wl >= d
    ) {
      status = 'danger';
    } else if (
      wl !== null &&
      w !== null &&
      w > 0 &&
      wl >= w
    ) {
      status = 'warning';
    } else if (
      /DANGER|RED/.test(raw) &&
      !/BELOW\s+DANGER/.test(raw)
    ) {
      status = 'danger';
    } else if (
      /WARNING|ORANGE/.test(raw) &&
      !/BELOW\s+WARNING/.test(raw)
    ) {
      status = 'warning';
    } else if (
      /WATCH|RISING|INCREASING|YELLOW/.test(raw)
    ) {
      status = 'watch';
    }

    return {
      level: wl,
      warning: w,
      danger: d,
      status,
      raw
    };
  }

  function candidate(o, requireObservation = false) {
    o = flat(o);

    const c = coord(o);

    if (!c) return null;

    const has = hasObservation(o);

    if (requireObservation && !has) {
      return null;
    }

    const s = stage(o);

    return {
      o,

      name: name(o),
      basin: basin(o),
      district: district(o),
      stationId: stationId(o),

      lat: c[0],
      lon: c[1],

      time: stamp(o),

      hasObservation: has,
      hasLatest: has,

      status:
        has
          ? s.status
          : 'unknown',

      rawStatus: s.raw,

      level:
        has
          ? s.level
          : null,

      warning: s.warning,
      danger: s.danger,

      discharge:
        has
          ? discharge(o)
          : null,

      source:
        String(
          o?.dataSource ||
          o?.data_source ||
          o?._catalogueSource ||
          'DHM / BIPAD'
        ),

      sourceUrl:
        String(
          o?._officialLivePage ||
          o?.source_url ||
          o?.sourceUrl ||
          'https://bipadportal.gov.np/realtime/'
        )
    };
  }

  function allBase() {
    const S = window.FloodSafe?.state || {};

    const rows =
      S.latestRiverStations ||
      S.currentRiverStations ||
      S.stations ||
      [];

    return rows
      .map(x => candidate(x, true))
      .filter(Boolean);
  }

  function allCatalog() {
    const rows =
      window.FloodSafe?.state?.allRiverStations ||
      [];

    return rows
      .map(x => candidate(x, false))
      .filter(Boolean);
  }

  function points(w) {
    if (Array.isArray(w?.pts)) {
      return w.pts
        .filter(
          p =>
            Array.isArray(p) &&
            Number.isFinite(+p[0]) &&
            Number.isFinite(+p[1])
        )
        .map(p => [+p[0], +p[1]]);
    }

    if (Array.isArray(w?.geometry_points)) {
      return w.geometry_points;
    }

    return [];
  }

  function pointSegKm(la, lo, a, b) {
    const lat0 = (la * Math.PI) / 180;
    const sc = Math.cos(lat0);

    const x1 = (a[0] - lo) * 111.32 * sc;
    const y1 = (a[1] - la) * 110.574;

    const x2 = (b[0] - lo) * 111.32 * sc;
    const y2 = (b[1] - la) * 110.574;

    const dx = x2 - x1;
    const dy = y2 - y1;

    const den = dx * dx + dy * dy;

    const t = den
      ? Math.max(
          0,
          Math.min(
            1,
            -(x1 * dx + y1 * dy) / den
          )
        )
      : 0;

    const x = x1 + t * dx;
    const y = y1 + t * dy;

    return Math.sqrt(x * x + y * y);
  }

  function lineDistanceKm(
    la,
    lo,
    pts
  ) {
    if (
      !Array.isArray(pts) ||
      pts.length < 2
    ) {
      return Infinity;
    }

    let best = Infinity;

    for (
      let i = 1;
      i < pts.length;
      i++
    ) {
      best = Math.min(
        best,
        pointSegKm(
          la,
          lo,
          pts[i - 1],
          pts[i]
        )
      );
    }

    return best;
  }

  function match(
    rows,
    w,
    la,
    lo,
    regional = true
  ) {
    const names = variants(w);
    const pts = points(w);

    const named =
      names.length > 0;

    const geomLimit =
      named
        ? LINE_EXACT_KM
        : UNNAMED_LINE_KM;

    if (
      (!Number.isFinite(la) ||
        !Number.isFinite(lo)) &&
      pts.length
    ) {
      const p =
        pts[
          Math.floor(
            (pts.length - 1) / 2
          )
        ];

      lo = p[0];
      la = p[1];
    }

    if (
      !Number.isFinite(la) ||
      !Number.isFinite(lo)
    ) {
      return null;
    }

    const all = rows.map(c => {
      let ns = 0;

      for (const n of names) {
        ns = Math.max(
          ns,
          scoreName(n, c.name)
        );
      }

      return {
        ...c,

        distanceKm:
          km(
            la,
            lo,
            c.lat,
            c.lon
          ),

        lineDistanceKm:
          lineDistanceKm(
            c.lat,
            c.lon,
            pts
          ),

        nameScore: ns
      };
    });

    const local = [];

    for (const x of all) {
      const byName =
        named &&
        x.nameScore >= 91 &&
        x.distanceKm <=
          SAME_RIVER_LOCAL_KM;

      const byGeom =
        x.lineDistanceKm <=
        geomLimit;

      if (!byName && !byGeom) {
        continue;
      }

      const method =
        byName && byGeom
          ? 'name+geometry'
          : byGeom
            ? 'geometry'
            : 'name';

      local.push({
        ...x,

        sameRiver: true,
        local: true,
        reference: false,

        matchMethod: method,

        matchConfidence:
          x.nameScore >= 93 ||
          x.lineDistanceKm <= 1
            ? 'high'
            : 'medium'
      });
    }

    local.sort(
      (a, b) =>
        b.nameScore -
          a.nameScore ||
        a.lineDistanceKm -
          b.lineDistanceKm ||
        a.distanceKm -
          b.distanceKm
    );

    if (local[0]) {
      return local[0];
    }

    if (!regional) {
      return null;
    }

    const regionalNearest =
      all
        .filter(
          x =>
            x.distanceKm <=
            REGIONAL_KM
        )
        .sort(
          (a, b) =>
            a.distanceKm -
            b.distanceKm
        )[0];

    return regionalNearest
      ? {
          ...regionalNearest,

          sameRiver: false,
          local: false,
          reference: true,

          matchMethod:
            'regional-nearest',

          matchConfidence:
            'reference-only'
        }
      : null;
  }

  function forWaterway(
    w,
    la,
    lo
  ) {
    const x = match(
      allBase(),
      w,
      la,
      lo,
      true
    );

    if (!x) return null;

    return {
      ...x,

      coverage:
        x.sameRiver
          ? 'same-river-official-latest'
          : 'regional-reference'
    };
  }

  function forWaterwayCatalog(
    w,
    la,
    lo
  ) {
    const x = match(
      allCatalog(),
      w,
      la,
      lo,
      false
    );

    return x
      ? {
          ...x,

          coverage:
            x.local
              ? 'official-station-catalogue-local'
              : 'official-station-catalogue-same-river'
        }
      : null;
  }

  function nearby(
    la,
    lo,
    maxKm = 40,
    limit = 100
  ) {
    return allBase()
      .map(x => ({
        ...x,
        distanceKm:
          km(
            la,
            lo,
            x.lat,
            x.lon
          )
      }))
      .filter(
        x =>
          x.distanceKm <= maxKm
      )
      .sort(
        (a, b) =>
          a.distanceKm -
          b.distanceKm
      )
      .slice(0, limit);
  }

  function nearbyCatalog(
    la,
    lo,
    maxKm = 40,
    limit = 500
  ) {
    return allCatalog()
      .map(x => ({
        ...x,
        distanceKm:
          km(
            la,
            lo,
            x.lat,
            x.lon
          )
      }))
      .filter(
        x =>
          x.distanceKm <= maxKm
      )
      .sort(
        (a, b) =>
          a.distanceKm -
          b.distanceKm
      )
      .slice(0, limit);
  }

  window.FloodSafeGauge = {
    forWaterway,
    forWaterwayCatalog,
    nearby,
    nearbyCatalog,

    SAME_RIVER_LOCAL_KM,
    REGIONAL_KM,
    LINE_EXACT_KM,
    UNNAMED_LINE_KM,

    scoreName,
    canonical,
    variants,
    lineDistanceKm,

    allCatalog,
    allBase
  };

  console.log(
    '✅ FloodSafe Gauge Bridge V24 loaded'
  );
})();
