from pathlib import Path

root=Path(__file__).resolve().parent
patch=root/'patch_native_v0885_dhm_river_parity.py'
text=patch.read_text(encoding='utf-8')
start=text.find('def method_span(text,name):')
end=text.find('\n# -----------------------------------------------------------------------------',start)
if start<0 or end<0:raise SystemExit('v0885 runner could not find method_span block')
robust=r'''def method_span(text,name):
    # Generated legacy methods do not consistently keep an access modifier after the long patch chain.
    # Locate the method name first, then scan braces safely.
    token=name+'('
    p=text.find(token)
    if p<0:
        p=text.find(name+' (')
    if p<0:return None
    line=text.rfind('\n',0,p)+1
    op=text.find('{',p)
    if op<0:return None
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
