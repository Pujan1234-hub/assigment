from pathlib import Path
import subprocess,sys

root=Path(__file__).resolve().parent
subprocess.run([sys.executable,str(root/'run_patch_native_v0876.py')],check=True)

p=root/'patch_native_v0877_full_station_observation_parity.py'
code=p.read_text(encoding='utf-8')

# Accept methods that declare `throws Exception` in the patcher's method finder.
old="r'\\s*\\([^\\n]*\\)\\s*\\{',text)"
new="r'\\s*\\([^\\n]*\\)\\s*(?:throws\\s+[^{]+)?\\{',text)"
if old not in code:
    raise SystemExit('v0.8.77 matcher normalization anchor missing')
code=code.replace(old,new,1)

# v0.8.76's refreshRiverUi no longer carries the historical V0869 comment.
# Replace that brittle anchor with the actual feedFresh.setText(...) statement.
old_headline=r"ui=re.sub(r'feedFresh\.setText\(t\(.*?\);\s*// V0869_GAUGE_COUNT_UI',"
new_headline=r"ui=re.sub(r'feedFresh\.setText\(t\(.*?\)\);(?:\s*//[^\n]*)?',"
if old_headline not in code:
    raise SystemExit('v0.8.77 original feedFresh matcher anchor missing')
code=code.replace(old_headline,new_headline,1)

# The shared strDeep helper accepts (row, fields, keys...). v0.8.77 added three
# nested-object calls using the old two-argument shape; normalize them before exec.
compile_repairs={
    'strDeep(s,"index","id","stationIndex","station_index","stationId","station_id","code")':
        'strDeep(s,s.optJSONObject("fields"),"index","id","stationIndex","station_index","stationId","station_id","code")',
    'strDeep(s,"station_name","stationName","name","title","location")':
        'strDeep(s,s.optJSONObject("fields"),"station_name","stationName","name","title","location")',
    'strDeep((JSONObject)rv,"name","title","river_name","riverName")':
        'strDeep((JSONObject)rv,((JSONObject)rv).optJSONObject("fields"),"name","title","river_name","riverName")',
}
for bad,good in compile_repairs.items():
    if bad not in code:
        raise SystemExit('v0.8.77 nested strDeep compile anchor missing: '+bad)
    code=code.replace(bad,good,1)

exec(compile(code,str(p),'exec'),{'__file__':str(p),'__name__':'__main__'})
print('FloodSafe v0.8.77 complete: v0.8.76 truth + full BIPAD river/river-trimed observation parity + stable station identity + honest inventory/live/latest status')
