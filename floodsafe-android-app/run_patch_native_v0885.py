from pathlib import Path

root=Path(__file__).resolve().parent
patch=root/'patch_native_v0885_dhm_river_parity.py'
text=patch.read_text(encoding='utf-8')
start=text.find('def method_span(text,name):')
end=text.find('\n# -----------------------------------------------------------------------------',start)
if start<0 or end<0:raise SystemExit('v0885 runner could not find method_span block')
robust=r'''def method_span(text,name):
    # Pick an actual method DECLARATION, never an earlier call site.
    p=-1;line=-1;op=-1
    needle=name+'('
    search=0
    while True:
        q=text.find(needle,search)
        if q<0:break
        ls=text.rfind('\n',0,q)+1
        prefix=text[ls:q]
        close=text.find(')',q+len(needle))
        brace=text.find('{',close+1 if close>=0 else q)
        semi=text.find(';',q,brace if brace>=0 else len(text))
        declaration=('=' not in prefix and ('RiverStation' in prefix or 'void ' in prefix or 'String ' in prefix or 'boolean ' in prefix or 'int ' in prefix or 'double ' in prefix or 'JSONObject ' in prefix or 'JSONArray ' in prefix))
        short_tail=(close>=0 and brace>=0 and brace-close<180 and (semi<0 or semi>brace))
        if declaration and short_tail:
            p=q;line=ls;op=brace;break
        search=q+len(needle)
    if p<0:return None
    depth=0;quote=None;esc=False;i=op
    while i<len(text):
        ch=text[i]
        if quote:
            if esc:esc=False
            elif ch=='\\':esc=True
            elif ch==quote:quote=None
        else:
            if ch in ('\"',"'"):quote=ch
            elif ch=='{':depth+=1
            elif ch=='}':
                depth-=1
                if depth==0:return line,i+1
        i+=1
    return None
'''
code=text[:start]+robust+text[end:]
ns={'__file__':str(patch),'__name__':'__main__'}
exec(compile(code,str(patch),'exec'),ns,ns)
