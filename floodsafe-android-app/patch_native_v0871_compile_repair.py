from pathlib import Path

root=Path(__file__).resolve().parent
p=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java'
a=p.read_text(encoding='utf-8')

# 1) The 1-second scheduler lives on a legacy one-line Runnable, so use a block comment.
old='main.postDelayed(this,1_000L); // V0871_ONE_SECOND_SOURCE_RECHECK'
new='main.postDelayed(this,1_000L); /* V0871_ONE_SECOND_SOURCE_RECHECK */'
if old in a:
    a=a.replace(old,new,1)
elif new not in a:
    raise SystemExit('v0871 inline 1s poll marker missing')

# 2) RiverStation has no `raw` field. Read the exact official status from the cached
# source JSONObject instead, and make the refresh fingerprint include the whole source row
# so discharge/trend/status/threshold metadata changes can refresh an already-open popup.
a=a.replace('private static String v862FinalFingerprint(List<RiverStation> rows)',
            'private String v862FinalFingerprint(List<RiverStation> rows)',1)
old_fp="b.append(s.name).append('|').append(s.online).append('|').append(s.at).append('|').append(s.stage).append('|').append(s.raw).append('|');"
new_fp="JSONObject v871fp=v871SourceRowsByName.get(v846Key(s.name)); b.append(s.name).append('|').append(s.online).append('|').append(s.at).append('|').append(s.stage).append('|').append(v871fp==null?0:v871fp.toString().hashCode()).append('|'); // V0871_SOURCE_ROW_FINGERPRINT"
if old_fp in a:
    a=a.replace(old_fp,new_fp,1)
elif 'V0871_SOURCE_ROW_FINGERPRINT' not in a:
    raise SystemExit('v0871 raw fingerprint anchor missing')

status_anchor='        String source=strDeep(row,f,"_floodsafeSource","source","dataSource","data_source");'
status_line='        String rawStatus=strDeep(row,f,"_officialStatus","status","status_name","alertStatus","alert_status","riskLevel","risk_level"); // V0871_RAW_SOURCE_STATUS\n'
if 'V0871_RAW_SOURCE_STATUS' not in a:
    if status_anchor not in a:raise SystemExit('v0871 source status anchor missing')
    a=a.replace(status_anchor,status_anchor+'\n'+status_line,1)
old_status='b.append("\\n").append(t("अवस्था: ","Status: ")).append(s.raw==null||s.raw.trim().isEmpty()?stageName(s.stage):s.raw);'
new_status='b.append("\\n").append(t("अवस्था: ","Status: ")).append(rawStatus.isEmpty()?stageName(s.stage):rawStatus); // V0871_DISPLAY_RAW_SOURCE_STATUS'
if old_status in a:
    a=a.replace(old_status,new_status,1)
elif 'V0871_DISPLAY_RAW_SOURCE_STATUS' not in a:
    raise SystemExit('v0871 raw status display anchor missing')

p.write_text(a,encoding='utf-8')

for x in ['main.postDelayed(this,1_000L); /* V0871_ONE_SECOND_SOURCE_RECHECK */','V0871_SOURCE_ROW_FINGERPRINT','V0871_RAW_SOURCE_STATUS','V0871_DISPLAY_RAW_SOURCE_STATUS']:
    if x not in a:raise SystemExit('v0871 compile repair missing: '+x)
if '.append(s.raw)' in a or 's.raw==' in a:
    raise SystemExit('v0871 invalid RiverStation.raw reference remains')
print('FloodSafe v0.8.71 compile repair PASS: 1s closure safe + exact source status + full-row live-detail fingerprint')
