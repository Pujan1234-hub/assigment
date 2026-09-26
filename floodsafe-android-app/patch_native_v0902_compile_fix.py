from pathlib import Path
p=Path(__file__).resolve().parent/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/OfficialRiverData.java'
s=p.read_text(encoding='utf-8')
old='''                overlay(base, live);\n                base.put("_fsDirectBipad", true);\n                base.put("_fsDirectObservationAt", liveAt);'''
new='''                overlay(base, live);\n                try {\n                    base.put("_fsDirectBipad", true);\n                    base.put("_fsDirectObservationAt", liveAt);\n                } catch (Exception ignored) {}'''
if old in s:
    s=s.replace(old,new,1)
elif 'base.put("_fsDirectBipad", true);' in s and 'catch (Exception ignored)' not in s[s.find('base.put("_fsDirectBipad"')-80:s.find('base.put("_fsDirectBipad"')+240]:
    raise SystemExit('compile fix anchor changed')
p.write_text(s,encoding='utf-8')
print('v0.9.02 compile fix PASS: JSONObject metadata writes safely guarded')
