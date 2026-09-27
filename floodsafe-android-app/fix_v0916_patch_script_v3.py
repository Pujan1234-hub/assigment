from pathlib import Path
import re

p=Path('floodsafe-android-app/patch_native_v0916_sathi_knowledge.py')
s=p.read_text(encoding='utf-8')
pattern=r'''old_lang='privacySub\.setText\(t\("Location, microphone र alert data कसरी प्रयोग हुन्छ हेर्नुहोस्।","See how location, microphone and alert data are used\."\)\);updateOutsideNotice\(\);}'\nnew_lang='privacySub\.setText\(t\("Location, microphone र alert data कसरी प्रयोग हुन्छ हेर्नुहोस्।","See how location, microphone and alert data are used\."\)\);if\(newsList!=null&&"knowledge"\.equals\(newsList\.getTag\(\)\)\)renderKnowledgeFallback\(false\);updateOutsideNotice\(\);}'\ns=once\(s,old_lang,new_lang,'knowledge language refresh'\)'''
replacement='''lang_anchor='updateWeatherLayerUi();updateOutsideNotice();}'
if s.count(lang_anchor)!=1: raise SystemExit(f'knowledge language generated anchor expected 1, got {s.count(lang_anchor)}')
s=s.replace(lang_anchor,'updateWeatherLayerUi();if(newsList!=null&&"knowledge".equals(newsList.getTag()))renderKnowledgeFallback(false);updateOutsideNotice();}',1)'''
s2,n=re.subn(pattern,replacement,s,count=1)
if n!=1: raise SystemExit(f'v0916 language patch-source replacement count={n}')
p.write_text(s2,encoding='utf-8')
print('V0916_LANGUAGE_ANCHOR_FIXED')
