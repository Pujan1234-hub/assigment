from pathlib import Path
import re
p=Path('floodsafe-android-app/app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java')
s=p.read_text(encoding='utf-8')
name='loadTrustedRiverStationsV862'
pos=s.find(name+'(')
if pos<0: raise SystemExit('preflight: river loader name missing')
line=s.rfind('\n',0,pos)+1
brace=s.find('{',pos)
if brace<0 or brace-pos>500: raise SystemExit('preflight: river loader brace missing')
old=s[line:brace+1]
# preserve only method body; normalize signature for late patch chain matchers.
new='    private List<RiverStation> loadTrustedRiverStationsV862(long now) throws Exception{'
s=s[:line]+new+s[brace+1:]
p.write_text(s,encoding='utf-8')
print('V0894_LOADER_SIGNATURE_PREFLIGHT PASS old=',old.strip())
