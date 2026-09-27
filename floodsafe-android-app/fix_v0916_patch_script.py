from pathlib import Path

p=Path('floodsafe-android-app/patch_native_v0916_sathi_knowledge.py')
s=p.read_text(encoding='utf-8')
old='''s=once(s,'    private String currentWeather="";\\n    private boolean showAllStations=false;', ''' + "'''" + '''    private String currentWeather="";
    private boolean showAllStations=false;
    private int knowledgeTipIndex=-1;
    private final Runnable newsKnowledgeTick=new Runnable(){@Override public void run(){refreshNews();main.postDelayed(this,10L*60L*1000L);}}; // V0916_KNOWLEDGE_ROTATION
''' + "'''" + ''','knowledge fields')'''
new='''field_anchor='    private String currentWeather="";'
if s.count(field_anchor)!=1: raise SystemExit(f'knowledge field anchor expected 1, got {s.count(field_anchor)}')
s=s.replace(field_anchor,field_anchor+'\\n    private int knowledgeTipIndex=-1;\\n    private final Runnable newsKnowledgeTick=new Runnable(){@Override public void run(){refreshNews();main.postDelayed(this,10L*60L*1000L);}}; // V0916_KNOWLEDGE_ROTATION',1)'''
if old not in s:
    raise SystemExit('v0916 old field-anchor block missing')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
print('V0916_FIELD_ANCHOR_FIXED')
