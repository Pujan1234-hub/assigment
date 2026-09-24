from pathlib import Path

p=Path('.github/scripts/patch_floodsafe_v0894_true_realtime_map_stability.py')
s=p.read_text(encoding='utf-8')
old="""def replace_method(text,name,block):
    s=span(text,name)
    if not s:raise SystemExit('v0894 method missing: '+name)
    return text[:s[0]]+block+text[s[1]:]
"""
new="""def replace_method(text,name,block):
    s=span(text,name)
    if not s and name=='loadTrustedRiverStationsV862':
        # Late native patches can rename/reformat the canonical river loader. Locate the
        # method that owns the official river-stations request instead of depending on its name.
        anchors=[]
        for token in ('V0877_CLEAN_FULL_INVENTORY_TRUTH','river-stations/?limit=5000','V0867_LATEST_OFFICIAL'):
            pos=text.find(token)
            if pos>=0: anchors.append(pos)
        for marker in anchors:
            methods=list(re.finditer(r'(?m)^\\s*private\\s+(?:java\\.util\\.)?List<RiverStation>\\s+\\w+\\s*\\(',text[:marker]))
            if not methods: continue
            start=methods[-1].start();op=text.find('{',methods[-1].end());d=0;quote=None;esc=False
            if op<0: continue
            for i in range(op,len(text)):
                ch=text[i]
                if quote:
                    if esc:esc=False
                    elif ch=='\\\\':esc=True
                    elif ch==quote:quote=None
                else:
                    if ch in ('\\\"',\"'\"):quote=ch
                    elif ch=='{':d+=1
                    elif ch=='}':
                        d-=1
                        if d==0:
                            s=(start,i+1);break
            if s:break
    if not s:
        names=re.findall(r'(?m)^\\s*private\\s+(?:java\\.util\\.)?List<RiverStation>\\s+(\\w+)\\s*\\(',text)
        raise SystemExit('v0894 method missing: '+name+' candidates='+','.join(names[-12:]))
    return text[:s[0]]+block+text[s[1]:]
"""
if old not in s:
    raise SystemExit('repair_v0894: replace_method anchor missing')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
print('repair_v0894 PASS: loader resolves by current official-source method ownership')
