from pathlib import Path

P = Path("floodsafe-android-app/app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java")
s = P.read_text(encoding="utf-8")


def repl(old: str, new: str) -> None:
    global s
    count = s.count(old)
    if count != 1:
        raise SystemExit(f"expected exactly one match, got {count}: {old[:120]!r}")
    s = s.replace(old, new, 1)

# Language toggle: rebuild the Activity so every t(ne,en) label created in card/nav/dialog
# construction is refreshed together, without changing any map/data implementation.
repl(
    'langBtn.setOnClickListener(v->{english=!english;getSharedPreferences(PREFS,MODE_PRIVATE).edit().putBoolean(KEY_LANG,english).apply();applyLanguage();refreshRiverUi();});',
    'langBtn.setOnClickListener(v->{english=!english;getSharedPreferences(PREFS,MODE_PRIVATE).edit().putBoolean(KEY_LANG,english).apply();applyTtsLanguage();recreate();});'
)

# Reverse geocoding follows the in-app language instead of the phone default locale.
repl(
    'new Geocoder(this,Locale.getDefault())',
    'new Geocoder(this,english?Locale.UK:Locale.forLanguageTag("ne-NP"))'
)

# User-facing station fallback follows the selected language. Parsing/risk semantics stay unchanged.
repl(
    'if(name.isEmpty())name=!riverName.isEmpty()?riverName:"Official river station";',
    'if(name.isEmpty())name=!riverName.isEmpty()?riverName:t("आधिकारिक नदी स्टेशन","Official river station");'
)

# Fully localize freshness summary while preserving values/status logic.
repl(
    'feedFresh.setText(t("Fresh: 🔴 "+d+"  🟠 "+w+"  🟡 "+a+"  🔵 "+n+" • stale/unknown "+stale,"Fresh: 🔴 "+d+"  🟠 "+w+"  🟡 "+a+"  🔵 "+n+" • stale/unknown "+stale));',
    'feedFresh.setText(t("ताजा: 🔴 "+d+"  🟠 "+w+"  🟡 "+a+"  🔵 "+n+" • पुरानो/अज्ञात "+stale,"Fresh: 🔴 "+d+"  🟠 "+w+"  🟡 "+a+"  🔵 "+n+" • stale/unknown "+stale));'
)

# Risk banner text.
repl(
    'alarmText.setText(best.name+" • river geometry "+String.format(Locale.US,"%.1f km",emergencyRiverKm)+" • "+stationLine(best));',
    'alarmText.setText(best.name+t(" • प्रभावित नदीसम्म "," • to affected river ")+String.format(Locale.US,"%.1f km",emergencyRiverKm)+" • "+stationLine(best));'
)

# Relative time and station distance labels.
repl(
    'else if(ageMs<60L*60L*1000L)age=(ageMs/60000L)+" min ago";',
    'else if(ageMs<60L*60L*1000L)age=t((ageMs/60000L)+" मिनेट अघि",(ageMs/60000L)+" min ago");'
)
repl(
    'else if(ageMs<48L*60L*60L*1000L)age=(ageMs/(60L*60L*1000L))+" hr ago";',
    'else if(ageMs<48L*60L*60L*1000L)age=t((ageMs/(60L*60L*1000L))+" घण्टा अघि",(ageMs/(60L*60L*1000L))+" hr ago");'
)
repl(
    'else age=(ageMs/(24L*60L*60L*1000L))+" days ago";',
    'else age=t((ageMs/(24L*60L*60L*1000L))+" दिन अघि",(ageMs/(24L*60L*60L*1000L))+" days ago");'
)
repl(
    'String lev=Double.isFinite(s.level)?String.format(Locale.US,"%.2f m",s.level):"level —";',
    'String lev=Double.isFinite(s.level)?String.format(Locale.US,"%.2f m",s.level):t("सतह —","level —");'
)
repl(
    'return freshness+" • "+lev+" • "+age+(Double.isFinite(d)?String.format(Locale.US," • station %.1f km",d):"");',
    'return freshness+" • "+lev+" • "+age+(Double.isFinite(d)?t(String.format(Locale.US," • स्टेशन %.1f km",d),String.format(Locale.US," • station %.1f km",d)):"");'
)

# Station detail dialog.
repl('b.append("\\nStation ID: ").append(s.stationId);', 'b.append(t("\\nस्टेशन ID: ","\\nStation ID: ")).append(s.stationId);')
repl('b.append("\\nRiver: ").append(s.riverName);', 'b.append(t("\\nनदी: ","\\nRiver: ")).append(s.riverName);')
repl('b.append("\\nWarning: ").append(String.format(Locale.US,"%.2f m",s.warning));', 'b.append(t("\\nचेतावनी स्तर: ","\\nWarning: ")).append(String.format(Locale.US,"%.2f m",s.warning));')
repl('b.append("\\nDanger: ").append(String.format(Locale.US,"%.2f m",s.danger));', 'b.append(t("\\nखतरा स्तर: ","\\nDanger: ")).append(String.format(Locale.US,"%.2f m",s.danger));')
repl('t("Official observation: ","Official observation: ")', 't("आधिकारिक मापन समय: ","Official observation: ")')
repl(
    't("Rainfall: सुरक्षित रूपमा match भएको fresh DHM rainfall reading उपलब्ध छैन।","Rainfall: no safely matched fresh DHM rainfall reading is available.")',
    't("वर्षा: सुरक्षित रूपमा मिलेको ताजा DHM वर्षा मापन उपलब्ध छैन।","Rainfall: no safely matched fresh DHM rainfall reading is available.")'
)
repl('b.append("\\n\\nSource: BIPAD / DHM");', 'b.append("\\n\\n").append(t("स्रोत: BIPAD / DHM","Source: BIPAD / DHM"));')

# News timestamps.
repl(
    'TextView meta=text(n.source+(n.at>0?" • "+Math.max(0,(System.currentTimeMillis()-n.at)/60000)+" min ago":""),11,false,Color.rgb(102,131,153));',
    'TextView meta=text(n.source+(n.at>0?" • "+Math.max(0,(System.currentTimeMillis()-n.at)/60000)+t(" मिनेट अघि"," min ago"):""),11,false,Color.rgb(102,131,153));'
)

# SATHI transcript prefix.
repl(
    'out.setText("तपाईं: "+q+"\\n\\nSATHI: "+a);',
    'out.setText(t("तपाईं: ","You: ")+q+"\\n\\nSATHI: "+a);'
)

# TTS follows selected UI language.
repl(
    'private void initTts(){tts=new TextToSpeech(getApplicationContext(),s->{if(s==TextToSpeech.SUCCESS&&tts!=null){int r=tts.setLanguage(Locale.forLanguageTag("ne-NP"));if(r==TextToSpeech.LANG_MISSING_DATA||r==TextToSpeech.LANG_NOT_SUPPORTED)tts.setLanguage(new Locale("ne"));tts.setSpeechRate(.92f);}});}private void speak(String s){if(tts!=null&&s!=null&&!s.isEmpty())tts.speak(s,TextToSpeech.QUEUE_FLUSH,null,"sathi-native-full");}',
    'private void initTts(){tts=new TextToSpeech(getApplicationContext(),s->{if(s==TextToSpeech.SUCCESS&&tts!=null){applyTtsLanguage();tts.setSpeechRate(.92f);}});}private void applyTtsLanguage(){if(tts==null)return;Locale target=english?Locale.UK:Locale.forLanguageTag("ne-NP");int r=tts.setLanguage(target);if(r==TextToSpeech.LANG_MISSING_DATA||r==TextToSpeech.LANG_NOT_SUPPORTED)tts.setLanguage(english?Locale.ENGLISH:new Locale("ne"));}private void speak(String s){if(tts!=null&&s!=null&&!s.isEmpty())tts.speak(s,TextToSpeech.QUEUE_FLUSH,null,"sathi-native-full");}'
)

P.write_text(s, encoding="utf-8")
print("LANGUAGE_SAFE_PATCH PASS")
