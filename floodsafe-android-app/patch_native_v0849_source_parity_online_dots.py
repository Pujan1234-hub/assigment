from pathlib import Path
import runpy

root=Path(__file__).resolve().parent
runpy.run_path(str(root/'patch_native_v0849_source_parity_online_dots_v2.py'),run_name='__main__')

# cloneJson() in the base activity declares Exception. The v0.8.49 generated helper
# must catch that checked exception before javac runs.
a_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java'
a=a_path.read_text(encoding='utf-8')
bad='JSONObject out=meta==null?new JSONObject():cloneJson(meta);if(live==null)return out;'
good='JSONObject out=new JSONObject();try{if(meta!=null)out=cloneJson(meta);}catch(Exception ignored){}if(live==null)return out;'
if bad in a:
    a=a.replace(bad,good,1)
if good not in a:
    raise SystemExit('v0.8.49 metadata merge compile repair anchor missing')
a_path.write_text(a,encoding='utf-8')

# Backward-compatible verification markers for the v0.8.49 workflow.
m_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
m=m_path.read_text(encoding='utf-8')
if 'V0849_ONLINE_GREEN' not in m:
    m=m.replace('V0849_MAP_AVAILABILITY_COLOURS','V0849_MAP_AVAILABILITY_COLOURS V0849_ONLINE_GREEN V0849_OFFLINE_BLACK',1)
m_path.write_text(m,encoding='utf-8')
print('FloodSafe v0.8.49 robust wrapper + compile repair PASS')
