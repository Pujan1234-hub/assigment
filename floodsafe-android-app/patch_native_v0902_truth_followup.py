from pathlib import Path

root=Path(__file__).resolve().parent
src=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app'

# Keep the mirror's official station inventory bounded. The raw BIPAD /river endpoint can
# contain many historical observations; those may update a known station only when newer,
# but must not create hundreds of duplicate/historical catalog entries.
p=src/'OfficialRiverData.java'
s=p.read_text(encoding='utf-8')
if 'V0902_CATALOG_BOUND_DIRECT_CURRENT' not in s:
    s=s.replace('''        final int directBipadCount;\n        final boolean directBipadOk;''','''        final int directBipadCount;\n        final int directBipadCurrentCount;\n        final boolean directBipadOk;''',1)
    s=s.replace('''        Snapshot(JSONArray rows, int catalogCount, int directBipadCount,\n                 boolean directBipadOk, long newestObservationAt, String source) {''','''        Snapshot(JSONArray rows, int catalogCount, int directBipadCount, int directBipadCurrentCount,\n                 boolean directBipadOk, long newestObservationAt, String source) {''',1)
    s=s.replace('''            this.directBipadCount = directBipadCount;\n            this.directBipadOk = directBipadOk;''','''            this.directBipadCount = directBipadCount;\n            this.directBipadCurrentCount = directBipadCurrentCount;\n            this.directBipadOk = directBipadOk;''',1)
    s=s.replace('''        boolean directOk = direct.length() > 0;\n        if (catalog.length() == 0 && direct.length() == 0) {''','''        boolean directOk = direct.length() > 0;\n        int directCurrent = 0;\n        long directNow = System.currentTimeMillis();\n        for (int i=0;i<direct.length();i++) if (isCurrent(direct.optJSONObject(i), directNow)) directCurrent++;\n        if (catalog.length() == 0 && direct.length() == 0) {''',1)
    s=s.replace('''        String source = directOk ? "BIPAD direct + inventory mirror" : "inventory mirror fallback";\n        return new Snapshot(merged,\n                catalog.length() > 0 ? catalog.length() : merged.length(),\n                direct.length(), directOk, newest, source);''','''        String source = directCurrent > 0\n                ? "BIPAD direct current + official inventory mirror"\n                : (directOk ? "BIPAD direct checked; newer official mirror observations retained" : "official mirror fallback");\n        return new Snapshot(merged,\n                catalog.length() > 0 ? catalog.length() : merged.length(),\n                direct.length(), directCurrent, directOk, newest, source);''',1)
    s=s.replace('''        LinkedHashMap<String, JSONObject> merged = new LinkedHashMap<>();\n        int anonymous = 0;''','''        LinkedHashMap<String, JSONObject> merged = new LinkedHashMap<>();\n        final boolean catalogBacked = catalog != null && catalog.length() > 0;\n        int anonymous = 0;''',1)
    old='''            if (base == null) {\n                base = cloneJson(live);\n                key = key.isEmpty() ? "bipad#" + (anonymous++) : key;\n                merged.put(key, base);\n            }'''
    new='''            if (base == null) {\n                // When the official inventory is present, unmatched raw /river rows are\n                // historical observations, not new catalog stations. Do not inflate the map.\n                if (catalogBacked) continue;\n                base = cloneJson(live);\n                key = key.isEmpty() ? "bipad#" + (anonymous++) : key;\n                merged.put(key, base);\n            }'''
    if old not in s: raise SystemExit('OfficialRiverData unmatched-direct anchor missing')
    s=s.replace(old,new,1)
    s=s.replace('final class OfficialRiverData {','final class OfficialRiverData {\n    // V0902_CATALOG_BOUND_DIRECT_CURRENT',1)
    p.write_text(s,encoding='utf-8')

# This file is patched after patch_native_v0902_activity_truth_ui.py has generated the
# v0.9.02 activity. Keep the user-facing count honest: raw API rows checked are not active rows.
p=src/'NativeFullActivity.java'
s=p.read_text(encoding='utf-8')
if 'V0902_DIRECT_CURRENT_TRUTH_UI' not in s:
    s=s.replace('''private int catalogCount=0,directBipadCount=0,latestReadingCount=0,currentReadingCount=0;''','''private int catalogCount=0,directBipadCount=0,directBipadCurrentCount=0,latestReadingCount=0,currentReadingCount=0;''',1)
    s=s.replace('''                directBipadCount=snap.directBipadCount;\n                directBipadOk=snap.directBipadOk;''','''                directBipadCount=snap.directBipadCount;\n                directBipadCurrentCount=snap.directBipadCurrentCount;\n                directBipadOk=snap.directBipadOk;''',1)
    s=s.replace('''android.util.Log.i("FloodSafeTruth","catalog="+catalogCount+" merged="+out.size()+" bipad_rows="+directBipadCount\n                        +" latest_readings="+latestReadingCount+" current="+currentReadingCount+" source="+riverTruthSource);''','''android.util.Log.i("FloodSafeTruth","catalog="+catalogCount+" merged="+out.size()+" bipad_rows_checked="+directBipadCount+" bipad_direct_current="+directBipadCurrentCount\n                        +" latest_readings="+latestReadingCount+" current="+currentReadingCount+" source="+riverTruthSource);''',1)
    s=s.replace('''String parity=(directBipadOk?" • BIPAD rows "+directBipadCount:" • BIPAD direct unavailable, safe cache fallback");''','''String parity=(directBipadOk?" • BIPAD API checked "+directBipadCount+" • direct-current "+directBipadCurrentCount:" • BIPAD direct unavailable • official mirror fallback");''',1)
    s=s.replace('// V0902_BIPAD_TRUTH_DISTRICT_POPUP','// V0902_BIPAD_TRUTH_DISTRICT_POPUP\n// V0902_DIRECT_CURRENT_TRUTH_UI',1)
    p.write_text(s,encoding='utf-8')

print('v0.9.02 truth follow-up PASS: bounded catalog + direct-current count + honest UI parity')
