from pathlib import Path
import re

root=Path(__file__).resolve().parent
p=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java'
s=p.read_text(encoding='utf-8')

def method_span(text,name):
    q=re.search(r'(?m)^\s*(?:private|public|protected)\s+[^\n{]+\b'+re.escape(name)+r'\s*\([^\n]*\)\s*\{',text)
    if not q:return None
    op=text.find('{',q.start());depth=0;quote=None;esc=False;i=op
    while i<len(text):
        ch=text[i]
        if quote:
            if esc:esc=False
            elif ch=='\\':esc=True
            elif ch==quote:quote=None
        else:
            if ch in ('"',"'"):quote=ch
            elif ch=='{':depth+=1
            elif ch=='}':
                depth-=1
                if depth==0:return q.start(),i+1
        i+=1
    return None

sp=method_span(s,'refreshRiverUi')
if not sp:raise SystemExit('v0876 preflight refreshRiverUi missing')
b=s[sp[0]:sp[1]]
# Normalize all source-presence counters to the Station.fresh flag. v0.8.76 later
# restores fresh to a true <=20-minute timestamp gate; stale rows remain in inventory.
b=re.sub(r's\.online\s*&&\s*Double\.isFinite\(s\.level\)\s*&&\s*s\.at\s*>\s*0L',
         's.fresh&&Double.isFinite(s.level)&&s.at>0L',b)
if 'V0876_CURRENT_COUNT_FRESH_ONLY' not in b:
    op=b.find('{')
    b=b[:op+1]+'\n        // V0876_CURRENT_COUNT_FRESH_ONLY: visible current counts use s.fresh, stale rows stay inspectable.'+b[op+1:]
s=s[:sp[0]]+b+s[sp[1]:]
p.write_text(s,encoding='utf-8')
print('FloodSafe v0.8.76 preflight PASS: current-count freshness anchor normalized')
