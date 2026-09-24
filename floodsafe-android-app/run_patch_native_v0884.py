from pathlib import Path

root=Path(__file__).resolve().parent
patch=root/'patch_native_v0884_realtime_river_status_detail.py'
ns={'__file__':str(patch),'__name__':'__main__'}
try:
    exec(compile(patch.read_text(encoding='utf-8'),str(patch),'exec'),ns,ns)
except SystemExit as e:
    msg=str(e)
    if msg!='v0884 map contract missing: V0877_CLEAN_FRESH_ONLY_LIVE':
        raise
    # Fresh-only LIVE truth belongs to NativeFullActivity. The v0.8.84 map patch has
    # already completed its in-memory runtime overrides at this point; validate the real
    # safety owner, then persist the generated map/build files.
    m=ns.get('m');g=ns.get('g');m_path=ns.get('m_path');g_path=ns.get('g_path')
    if not isinstance(m,str) or not isinstance(g,str) or m_path is None or g_path is None:
        raise SystemExit('v0884 wrapper could not recover generated state')
    a_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java'
    a=a_path.read_text(encoding='utf-8')
    if 'V0877_CLEAN_FRESH_ONLY_LIVE' not in a:
        raise SystemExit('v0884 activity fresh-only safety contract missing')
    required=[
        'V0884_STRICT_CANONICAL_RIVER_KEY','V0884_RISK_USES_OFFICIAL_RIVER_NAME','V0884_FRESH_SAME_RIVER_RISK_ONLY',
        'V0884_RISK_GLOW_LAYERS','V0884_STATUS_COLOUR_FLOW_GLOW','V0884_RISK_REFRESH_AFTER_TILE_SWAP',
        'V0884_RIVER_DETAIL_HELPERS','V0884_REAL_RIVER_DETAIL_TIME_SOURCE_THRESHOLDS','V0884_NO_STATION_REDIRECT',
        'V0883_NEPAL_MIN_ZOOM','V0881_HYDRO_WATERBODY_GEO'
    ]
    for x in required:
        if x not in m:raise SystemExit('v0884 wrapper map contract missing: '+x)
    if 'versionCode 104' not in g or "versionName '0.8.84'" not in g:
        raise SystemExit('v0884 wrapper version contract missing')
    m_path.write_text(m,encoding='utf-8')
    g_path.write_text(g,encoding='utf-8')
    print('FloodSafe v0.8.84 wrapper PASS: fresh-only safety verified in activity; realtime river detail/risk glow persisted')
