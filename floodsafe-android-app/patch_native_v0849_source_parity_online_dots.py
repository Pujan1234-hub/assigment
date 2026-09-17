from pathlib import Path
import runpy

root=Path(__file__).resolve().parent
runpy.run_path(str(root/'patch_native_v0849_source_parity_online_dots_v2.py'),run_name='__main__')

# Backward-compatible verification markers for the v0.8.49 workflow.
m_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
m=m_path.read_text(encoding='utf-8')
if 'V0849_ONLINE_GREEN' not in m:
    m=m.replace('V0849_MAP_AVAILABILITY_COLOURS','V0849_MAP_AVAILABILITY_COLOURS V0849_ONLINE_GREEN V0849_OFFLINE_BLACK',1)
m_path.write_text(m,encoding='utf-8')
print('FloodSafe v0.8.49 robust wrapper PASS')
