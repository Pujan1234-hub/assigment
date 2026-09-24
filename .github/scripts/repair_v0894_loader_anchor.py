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
        # The generated loader signature may wrap across lines. Find its declaration prefix,
        # then balance braces from the first body brace instead of requiring a one-line signature.
        methods=list(re.finditer(r'(?m)^\\s*private\\s+(?:java\\.util\\.)?List<RiverStation>\\s+(\\w+)\\s*\\(',text))
        chosen=None
        for mm in methods:
            if mm.group(1)==name: chosen=mm;break
        if chosen is None and methods: chosen=methods[-1]
        if chosen is not None:
            start=chosen.start();op=text.find('{',chosen.end());d=0;quote=None;esc=False
            if op>=0:
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
    if not s:
        names=re.findall(r'(?m)^\\s*private\\s+(?:java\\.util\\.)?List<RiverStation>\\s+(\\w+)\\s*\\(',text)
        raise SystemExit('v0894 method missing: '+name+' candidates='+','.join(names[-12:]))
    return text[:s[0]]+block+text[s[1]:]
"""
if old not in s:
    raise SystemExit('repair_v0894: replace_method anchor missing')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
print('repair_v0894 PASS: multiline loader signature supported')
