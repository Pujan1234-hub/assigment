from pathlib import Path
import re
p=Path('floodsafe-android-app/patch_native_v0916_sathi_knowledge.py')
s=p.read_text(encoding='utf-8')
pattern=r'''# Current local weather string used by SATHI must contain actual condition \+ temperature, not only Rain/No rain\..*?# Conversational patch submit hooks: district weather is fetched asynchronously at the requested district centre\.'''
replacement=r'''# Current local weather string used by SATHI must contain actual generated v0.9.15 condition + metrics.
weather_anchor='String ws=weatherCodeText(code,pr);String timing=rainTiming(j);currentWeather=ws;'
weather_new='String ws=weatherCodeText(code,pr);String timing=rainTiming(j);currentWeather=t(ws+", तापक्रम "+(Double.isFinite(te)?Math.round(te)+"°C":"उपलब्ध छैन")+", वर्षा "+String.format(Locale.US,"%.1f",pr)+" mm, बादल "+(Double.isFinite(cloud)?Math.round(cloud)+"%":"उपलब्ध छैन")+(Double.isFinite(hu)?", आर्द्रता "+Math.round(hu)+"%":"")+(Double.isFinite(wi)?", हावा "+Math.round(wi)+" km/h":"")+"।",ws+", "+(Double.isFinite(te)?Math.round(te)+"°C":"temperature unavailable")+", rain "+String.format(Locale.US,"%.1f",pr)+" mm, cloud "+(Double.isFinite(cloud)?Math.round(cloud)+"%":"unavailable")+(Double.isFinite(hu)?", humidity "+Math.round(hu)+"%":"")+(Double.isFinite(wi)?", wind "+Math.round(wi)+" km/h":"")+".");'
s=once(s,weather_anchor,weather_new,'v0.9.15 currentWeather detail')

# Conversational patch submit hooks: district weather is fetched asynchronously at the requested district centre.'''
s2,n=re.subn(pattern,replacement,s,count=1,flags=re.S)
if n!=1: raise SystemExit(f'v0916 weather section replacement count={n}')
p.write_text(s2,encoding='utf-8')
print('V0916_WEATHER_ANCHOR_FIXED')
