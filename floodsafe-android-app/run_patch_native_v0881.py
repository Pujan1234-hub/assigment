from pathlib import Path

root=Path(__file__).resolve().parent
patch=root/'patch_native_v0881_river_lake_hydro_details.py'
ns={'__file__':str(patch),'__name__':'__main__'}
try:
    exec(compile(patch.read_text(encoding='utf-8'),str(patch),'exec'),ns,ns)
except SystemExit as e:
    msg=str(e)
    if msg!='v0881 map contract missing: V0877_CLEAN_FRESH_ONLY_LIVE':
        raise
    # The v0.8.77 fresh-only marker lives in NativeFullActivity, not the map class.
    # The v0.8.81 patch has already produced its intended in-memory map/build changes;
    # validate the actual owner of the safety contract and persist those changes.
    m=ns.get('m'); g=ns.get('g'); m_path=ns.get('m_path'); g_path=ns.get('g_path')
    if not isinstance(m,str) or not isinstance(g,str) or m_path is None or g_path is None:
        raise SystemExit('v0881 wrapper could not recover patch state')
    required=[
        'V0881_WATERBODY_DOT_FIELDS','V0881_RAW_OFFICIAL_METADATA_HELPERS','V0881_READ_WATERBODY_METADATA',
        'V0881_HYDRO_WATERBODY_GEO','V0881_PUBLISH_HYDRO_WATERBODY_LAYERS','V0881_WATERBODY_DETAIL_POPUP',
        'V0881_WATERBODY_TAP_PRIORITY','V0881_RIVER_FIRST_CLASS_DETAIL','V0881_NO_STATION_REDIRECT',
        'V0880_VISIBLE_REGION_ALL_TILES','V0880_EXACT_SAME_RIVER_ONLY'
    ]
    for x in required:
        if x not in m: raise SystemExit('v0881 wrapper map contract missing: '+x)
    a_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java'
    a=a_path.read_text(encoding='utf-8')
    if 'V0877_CLEAN_FRESH_ONLY_LIVE' not in a:
        raise SystemExit('v0881 wrapper activity fresh-only safety contract missing')
    if 'stationTapListener.onStationTap(gauge.original)' in m[m.find('private void showRiver'):m.find('private void showRiver')+5000]:
        raise SystemExit('v0881 wrapper river popup still redirects to station detail')
    m_path.write_text(m,encoding='utf-8')
    g_path.write_text(g,encoding='utf-8')
    print('FloodSafe v0.8.81 wrapper PASS: river/lake/hydro detail persisted; fresh-only safety verified in NativeFullActivity')
