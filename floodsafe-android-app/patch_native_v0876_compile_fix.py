from pathlib import Path

root=Path(__file__).resolve().parent
p=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java'
s=p.read_text(encoding='utf-8')

# v0.8.76 must not assume RiverStation has a raw field. The exact official raw/status
# text lives in the retained source JSONObject, while RiverStation stores normalized stage.
# Keep the freshness fingerprint compile-safe and read raw status directly from source row
# for the popup so no official source text is fabricated or lost.

old=".append(s.stage).append('|').append(s.raw).append('|');"
new=".append(s.stage).append('|'); // V0876_COMPILE_NO_RAW_FIELD"
if old in s:
    s=s.replace(old,new,1)
elif 'V0876_COMPILE_NO_RAW_FIELD' not in s:
    raise SystemExit('v0876 fingerprint raw-field anchor missing')

source_line='String source=strDeep(row,f,"_floodsafeSource","source","dataSource","data_source");'
raw_line='String rawStatus=strDeep(row,f,"status","status_name","alertStatus","alert_status","riskLevel","risk_level","_officialStatus"); // V0876_EXACT_RAW_STATUS_FROM_SOURCE'
if raw_line not in s:
    if source_line not in s:raise SystemExit('v0876 source status anchor missing')
    s=s.replace(source_line,source_line+'\n        '+raw_line,1)

old_expr='s.raw==null||s.raw.trim().isEmpty()?stageName(s.stage):s.raw'
new_expr='rawStatus==null||rawStatus.trim().isEmpty()?stageName(s.stage):rawStatus'
if old_expr in s:
    s=s.replace(old_expr,new_expr,1)
elif new_expr not in s:
    raise SystemExit('v0876 raw source popup expression missing')

if 's.raw' in s:raise SystemExit('v0876 invalid RiverStation raw field remains')
for marker in ['V0876_COMPILE_NO_RAW_FIELD','V0876_EXACT_RAW_STATUS_FROM_SOURCE','V0876_SOURCE_FRESHNESS_20M']:
    if marker not in s:raise SystemExit('v0876 compile contract missing: '+marker)

p.write_text(s,encoding='utf-8')
print('FloodSafe v0.8.76 compile repair PASS: normalized stage fingerprint + exact raw status from official source row')
