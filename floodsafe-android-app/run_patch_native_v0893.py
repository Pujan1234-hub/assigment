from pathlib import Path

p=Path(__file__).resolve().parent/'patch_native_v0893_dedicated_station_river_layer.py'
s=p.read_text(encoding='utf-8')
old="""if old not in m: raise SystemExit('particle count anchor missing')
m=m.replace(old,new,1)
if 'RiverWay r = rivers.get(i);' not in m: raise SystemExit('particle river anchor missing')
m=m.replace('RiverWay r = rivers.get(i);','RiverWay r = flowWays.get(i);',1)"""
new="""# Particle formatting varies across earlier map patches. Dedicated cyan source/glow is mandatory;
# particle reuse is optional and is applied only when the compatible loop is still present.
if old in m and 'RiverWay r = rivers.get(i);' in m:
    m=m.replace(old,new,1)
    m=m.replace('RiverWay r = rivers.get(i);','RiverWay r = flowWays.get(i);',1)"""
if old not in s:
    raise SystemExit('v0893 wrapper could not locate optional particle block')
s=s.replace(old,new,1)
exec(compile(s,str(p),'exec'))
