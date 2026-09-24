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
        # Late native patches can rename/reformat the loader while retaining the v0.8.77
        # canonical truth marker. Resolve the owning method by that stable marker instead.
        marker=text.find('V0877_CLEAN_FULL_INVENTORY_TRUTH')
        if marker>=0:
            start=text.rfind('private List<RiverStation>',0,marker)
            if start>=0:
                op=text.find('{',start);d=0;quote=None;esc=False
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
    if not s:raise SystemExit('v0894 method missing: '+name)
    return text[:s[0]]+block+text[s[1]:]
"""
if old not in s:
    raise SystemExit('repair_v0894: replace_method anchor missing')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
print('repair_v0894 PASS: loader can be resolved by canonical truth marker')
