from pathlib import Path

p = Path('floodsafe-android-app/app/src/main/java/io/github/pujan1234hub/floodsafe/app/SathiNextLevelV0918.java')
s = p.read_text(encoding='utf-8')

old_lang = 's.equals("english")||s.equals("nepali")||s.contains(" english")||s.contains(" nepali")'
new_lang = 's.equals("english")||s.equals("nepali")||s.equals("en")||s.equals("ne")||s.equals("np")||s.contains("🌐 en")||s.contains("🌐 ne")||s.contains("🌐 np")||s.contains(" english")||s.contains(" nepali")'
if old_lang not in s:
    raise SystemExit('language de-dupe anchor not found')
s = s.replace(old_lang, new_lang, 1)

old_return = '        return en?"I couldn\'t match that river/station to a verified reading in the current app feed. Try the official station or river name; I won\'t answer with a different river.":"Current app feed मा त्यो नदी/खोलालाई verified reading सँग match गर्न सकिनँ। Official station/river name ले फेरि सोध्नुहोस्; म अर्को खोलाको data मिसाउँदिनँ।";\n'
if old_return not in s:
    raise SystemExit('SATHI river fallback anchor not found')

fallback = '''        // USERFIX: If the user asks for a Nepal place/district (for example "Kathmandu River status")\n        // and the feed does not expose a reliable district label, answer from the nearest official gauges\n        // around that place instead of returning a useless no-match message.\n        if(!target.isEmpty()){\n            try{\n                Geo g=geocode(target);\n                if(g!=null){\n                    List<Station>x=new ArrayList<>(rows);\n                    x.sort(Comparator.comparingDouble(s->km(g.lat,g.lon,s.lat,s.lon)));\n                    StringBuilder b=new StringBuilder(en?"Nearest official river stations to "+g.name+": ":g.name+" नजिकका official नदी स्टेशन: ");\n                    int shown=0;\n                    for(Station s:x){\n                        double dist=km(g.lat,g.lon,s.lat,s.lon);\n                        if(!Double.isFinite(dist)||dist>120d)continue;\n                        if(shown>0)b.append(" • ");\n                        b.append(s.name).append(" — ").append(stage(s.stage,en));\n                        if(Double.isFinite(s.level))b.append(String.format(Locale.US," %.2f m",s.level));\n                        b.append(String.format(Locale.US," (%.1f km)",dist));\n                        shown++;\n                        if(shown>=4)break;\n                    }\n                    if(shown>0){\n                        b.append(en?". These are the nearest verified official gauges to the place you asked about; stale/unknown readings are not treated as live.":"। यी तपाईंले सोधेको ठाउँ नजिकका verified official gauges हुन्; stale/unknown reading लाई live मानिएको छैन।");\n                        return b.toString();\n                    }\n                }\n            }catch(Exception ignored){}\n        }\n'''

s = s.replace(old_return, fallback + old_return, 1)

# Build-time markers used by CI to make sure both user-reported fixes are present.
if 's.contains("🌐 en")' not in s:
    raise SystemExit('duplicate language selector fix missing')
if 'Nearest official river stations to ' not in s:
    raise SystemExit('place river status fallback missing')

p.write_text(s, encoding='utf-8')
print('V0918_USER_REPORTED_TWO_FIXES_OK')
