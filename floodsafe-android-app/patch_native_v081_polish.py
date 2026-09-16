from pathlib import Path

root = Path(__file__).resolve().parent
src = root / 'app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java'
gradle_path = root / 'app/build.gradle'
text = src.read_text(encoding='utf-8')

# v0.8.1: keep the native map gesture inside the map. ScrollView must not steal pinch/drag.
old_touch = '''        @Override public boolean onTouchEvent(MotionEvent e){scaler.onTouchEvent(e);gestures.onTouchEvent(e);return true;}'''
new_touch = '''        @Override public boolean onTouchEvent(MotionEvent e){
            int action=e.getActionMasked();
            if(action==MotionEvent.ACTION_DOWN||action==MotionEvent.ACTION_POINTER_DOWN||action==MotionEvent.ACTION_MOVE){
                if(getParent()!=null)getParent().requestDisallowInterceptTouchEvent(true);
            }
            scaler.onTouchEvent(e);gestures.onTouchEvent(e);
            if(action==MotionEvent.ACTION_UP||action==MotionEvent.ACTION_CANCEL){
                if(getParent()!=null)getParent().requestDisallowInterceptTouchEvent(false);
            }
            return true;
        }'''
if old_touch not in text and 'requestDisallowInterceptTouchEvent(true)' not in text:
    raise SystemExit('native map touch marker missing')
text = text.replace(old_touch, new_touch, 1)

# The national overview bitmap was visually dominated by thousands of river segments.
# Keep every bundled river, but draw them lighter/thinner at the national overview.
text = text.replace('p.setAlpha(205);p.setStrokeWidth(2.2f);', 'p.setAlpha(118);p.setStrokeWidth(1.25f);', 1)

# Do not dump dozens/hundreds of stations into the main scroll. Show a compact overview and
# open a dedicated district picker when the user wants the complete station list.
old_card = '''    private View nationalCard(){LinearLayout c=card();nationalTitle=text("",20,true,Color.rgb(16,39,70));nationalSub=text("",12,true,Color.rgb(100,130,151));nationalFresh=text("",12,true,Color.rgb(100,130,151));c.addView(nationalTitle);c.addView(nationalSub);c.addView(nationalFresh);nationalList=new LinearLayout(this);nationalList.setOrientation(LinearLayout.VERTICAL);c.addView(nationalList,lp(-1,-2,0,dp(8),0,0));Button more=smallButton(t("सबै स्टेशन देखाउनुहोस्","Show all stations"));more.setOnClickListener(v->{showAllStations=!showAllStations;more.setText(showAllStations?t("कम देखाउनुहोस्","Show less"):t("सबै स्टेशन देखाउनुहोस्","Show all stations"));refreshRiverUi();});c.addView(more);return c;}'''
new_card = '''    private View nationalCard(){LinearLayout c=card();nationalTitle=text("",20,true,Color.rgb(16,39,70));nationalSub=text("",12,true,Color.rgb(100,130,151));nationalFresh=text("",12,true,Color.rgb(100,130,151));c.addView(nationalTitle);c.addView(nationalSub);c.addView(nationalFresh);nationalList=new LinearLayout(this);nationalList.setOrientation(LinearLayout.VERTICAL);c.addView(nationalList,lp(-1,-2,0,dp(8),0,0));Button districts=smallButton(t("जिल्ला छान्नुहोस्","Choose district"));districts.setOnClickListener(v->showDistrictPicker());c.addView(districts);return c;}'''
if old_card not in text and 'districts.setOnClickListener(v->showDistrictPicker())' not in text:
    raise SystemExit('national card marker missing')
text = text.replace(old_card, new_card, 1)

old_national = '''nationalList.removeAllViews();int max=showAllStations?copy.size():Math.min(24,copy.size());for(int i=0;i<max;i++)nationalList.addView(stationRow(copy.get(i)));}'''
new_national = '''nationalList.removeAllViews();int max=Math.min(6,copy.size());for(int i=0;i<max;i++)nationalList.addView(stationRow(copy.get(i)));if(copy.size()>max)nationalList.addView(empty(t("मुख्य/जोखिमयुक्त station मात्र यहाँ देखाइएको छ। पूरा सूची जिल्ला छानेर हेर्नुहोस्।","Only key/risk-priority stations are shown here. Choose a district for the full list.")));}'''
if old_national not in text and 'Only key/risk-priority stations are shown here.' not in text:
    raise SystemExit('national station render marker missing')
text = text.replace(old_national, new_national, 1)

picker_methods = '''    private void showDistrictPicker(){
        List<String> districts=new ArrayList<>();
        synchronized(stations){for(RiverStation s:stations){String d=s.district==null?"":s.district.trim();if(!d.isEmpty()&&!districts.contains(d))districts.add(d);}}
        districts.sort(String::compareToIgnoreCase);
        if(districts.isEmpty()){new AlertDialog.Builder(this).setTitle(t("जिल्ला","District")).setMessage(t("Official station मा जिल्ला data अहिले उपलब्ध छैन।","District data is currently unavailable for official stations.")).setPositiveButton("OK",null).show();return;}
        String[] items=districts.toArray(new String[0]);
        new AlertDialog.Builder(this).setTitle(t("जिल्ला छान्नुहोस्","Choose district")).setItems(items,(dialog,which)->showDistrictStations(items[which])).setNegativeButton(t("बन्द","Close"),null).show();
    }
    private void showDistrictStations(String district){
        List<RiverStation> matches=new ArrayList<>();
        synchronized(stations){for(RiverStation s:stations)if(district.equalsIgnoreCase(s.district==null?"":s.district.trim()))matches.add(s);}
        matches.sort(Comparator.comparingInt((RiverStation s)->s.rank).thenComparingDouble(s->distanceKm(s.lat,s.lon)));
        if(matches.isEmpty()){new AlertDialog.Builder(this).setTitle(district).setMessage(t("यो जिल्लाको station reading भेटिएन।","No station reading found for this district.")).setPositiveButton("OK",null).show();return;}
        String[] rows=new String[matches.size()];
        for(int i=0;i<matches.size();i++){RiverStation s=matches.get(i);rows[i]=stageDot(s.stage)+" "+s.name+"\n"+stationLine(s);}
        new AlertDialog.Builder(this).setTitle(district+" • "+matches.size()+" "+t("स्टेशन","stations")).setItems(rows,(dialog,which)->showStation(matches.get(which))).setNegativeButton(t("फर्कनुहोस्","Back"),(d,w)->showDistrictPicker()).show();
    }
'''
station_anchor = '    private View stationRow(RiverStation s){'
if 'private void showDistrictPicker()' not in text:
    if station_anchor not in text:
        raise SystemExit('station row anchor missing')
    text = text.replace(station_anchor, picker_methods + station_anchor, 1)

# Wording now matches the compact district picker rather than a giant 77-district dump.
text = text.replace('nationalTitle.setText(t("🌊 ७७ जिल्ला — सबै official नदी स्टेशन","🌊 77 districts — official river stations"));nationalSub.setText(t("Latest official reading; stale data लाई live खतरा मानिँदैन।","Latest official readings; stale data is not treated as a live threat."));',
                    'nationalTitle.setText(t("🌊 नेपालभरि official नदी अवस्था","🌊 Nepal-wide official river status"));nationalSub.setText(t("मुख्य station यहाँ; पूरा सूची जिल्ला छानेर हेर्नुहोस्। Stale data live खतरा होइन।","Key stations here; choose a district for the full list. Stale data is not a live threat."));', 1)
text = text.replace('mapSub.setText(t("नदी/स्टेशन थिचेर पानीको तह, चेतावनी र official time हेर्नुहोस्।","Tap a river station for level, warning and official time."));mapHint.setText(t("🇳🇵 official नदी स्टेशन र नदी geometry","🇳🇵 official stations and river geometry"));',
                    'mapSub.setText(t("नक्साभित्र pinch/drag/zoom गर्नुहोस्; station थिचेर पानीको तह र official time हेर्नुहोस्।","Pinch, drag and zoom inside the map; tap a station for level and official time."));mapHint.setText(t("🇳🇵 नक्सा चलाउँदा screen होइन, नक्सा मात्र चल्छ","🇳🇵 Map gestures stay inside the map"));', 1)

# Fresh news remains first priority. When there is no fresh story, show a persisted rotating
# safety/knowledge card. Each render advances to the next tip, so reopening does not repeat it.
text = text.replace('private boolean showAllStations=false;', 'private boolean showAllStations=false;\n    private final Runnable knowledgeRotate=()->{if(!isFinishing()&&!isDestroyed())refreshNews();};', 1)
old_catch = '''}catch(Exception e){runOnUiThread(()->{newsList.removeAllViews();newsList.addView(empty(t("Live news अहिले उपलब्ध छैन।","Live news is currently unavailable.")));});}});}'''
new_catch = '''}catch(Exception e){runOnUiThread(this::renderKnowledgeTip);}});}'''
if old_catch not in text and 'runOnUiThread(this::renderKnowledgeTip)' not in text:
    raise SystemExit('news catch marker missing')
text = text.replace(old_catch, new_catch, 1)
old_render = '''    private void renderNews(List<NewsItem> out){newsList.removeAllViews();if(out.isEmpty()){newsList.addView(empty(t("नयाँ live समाचार भेटिएन।","No fresh live stories found.")));return;}for(NewsItem n:out){'''
new_render = '''    private void renderNews(List<NewsItem> out){newsList.removeAllViews();if(out.isEmpty()){renderKnowledgeTip();return;}main.removeCallbacks(knowledgeRotate);for(NewsItem n:out){'''
if old_render not in text and 'if(out.isEmpty()){renderKnowledgeTip();return;}' not in text:
    raise SystemExit('news render marker missing')
text = text.replace(old_render, new_render, 1)

knowledge = '''    private void renderKnowledgeTip(){
        if(newsList==null)return;
        newsList.removeAllViews();
        String[][] tips={
            {"बाढीको पानी देख्दा पैदल, बाइक वा गाडीबाट तर्न नखोज्नुहोस्। पानीको गहिराइ र बहाव बाहिरबाट ठ्याक्कै थाहा हुँदैन।","Never walk, ride or drive through floodwater. Depth and current can be deceptive."},
            {"नागरिकता, पासपोर्ट, औषधिको सूची र महत्वपूर्ण कागजात पानी नछिर्ने झोलामा राख्नुहोस्।","Keep identity documents, medicine lists and essential papers in a waterproof pouch."},
            {"घरको मुख्य बिजुली switch र gas बन्द गर्ने सुरक्षित तरिका परिवारका वयस्क सदस्यले पहिल्यै जान्नु राम्रो हुन्छ।","Adults in the household should know how to safely isolate electricity and gas before an emergency."},
            {"आपत्कालीन झोलामा टर्च, power bank, पानी, सुक्खा खाना र आवश्यक औषधि तयार राख्नुहोस्।","Keep a torch, power bank, water, shelf-stable food and essential medicines in an emergency bag."},
            {"बाढी वा पहिरोको बेला बन्द गरिएको सडक वा barrier छल्दै अगाडि नजानुहोस्।","Do not bypass road closures or barriers during floods or landslides."},
            {"परिवार छुट्टिएमा कहाँ भेट्ने र कसलाई फोन गर्ने भनेर पहिल्यै दुईवटा सम्पर्क योजना बनाउनुहोस्।","Agree two contact/reunion plans in case family members are separated."},
            {"फोनमा मात्र भर नपर्नुहोस्—महत्वपूर्ण सम्पर्क नम्बर कागजमा पनि लेखेर आपत्कालीन झोलामा राख्नुहोस्।","Keep important contact numbers on paper as well as on your phone."},
            {"नदी किनारमा पानीको रंग, आवाज वा बहाव अचानक बदलियो भने तुरुन्त अग्लो सुरक्षित ठाउँतर्फ जानुहोस्।","If river colour, sound or flow changes suddenly, move to higher safe ground immediately."},
            {"बच्चा, ज्येष्ठ नागरिक, अपाङ्गता भएका व्यक्ति र घरपालुवा जनावरका लागि छुट्टै evacuation आवश्यकता योजना बनाउनुहोस्।","Plan evacuation needs for children, older adults, disabled people and pets."},
            {"बाढीपछि घर फर्कँदा भिजेको बिजुली उपकरण वा खुला तार नछुनुहोस्।","After flooding, do not touch wet electrical equipment or exposed wiring."},
            {"पिउने पानी दूषित भएको शंका भए सुरक्षित bottled/treated water मात्र प्रयोग गर्नुहोस्।","If drinking water may be contaminated, use safe bottled or properly treated water."},
            {"घर नजिकको सुरक्षित अग्लो स्थान र त्यहाँ पुग्ने कम्तीमा दुईवटा बाटो पहिल्यै चिन्नुहोस्।","Know a nearby safe high place and at least two routes to reach it."},
            {"मौसम सामान्य देखिए पनि माथिल्लो भूभागमा परेको भारी वर्षाले तलको नदी अचानक बढ्न सक्छ।","A river can rise suddenly from heavy rain upstream even when local weather looks calm."},
            {"Official चेतावनीको screenshot मात्र होइन, समय र source पनि हेर्नुहोस्—पुरानो alert लाई अहिलेको अवस्था नमान्नुहोस्।","Check the time and source of an official warning; do not treat an old alert as current."},
            {"सुत्नुअघि phone charge, notification permission र volume जाँच्नु बाढी season मा उपयोगी बानी हो।","During flood season, checking phone charge, notification permission and volume before sleep is useful."},
            {"स्थानीय निकाय वा सुरक्षाकर्मीले evacuation भनेमा सामान बचाउन ढिलो नगरी सुरक्षित ठाउँमा जानुहोस्।","If authorities advise evacuation, move to safety promptly rather than delaying to save belongings."},
            {"पहिरो जोखिम भएको भीरमुनि पानीको नयाँ मुहान, चिरा वा ढुंगा खस्न थालेको देखिए क्षेत्र छोड्नुहोस्।","Near landslide-prone slopes, leave if you notice new seepage, cracks or falling rocks."},
            {"Emergency kit को खाना, battery र औषधिको expiry नियमित जाँच्नुहोस्।","Regularly check expiry dates of emergency food, batteries and medicines."}
        };
        SharedPreferences pref=getSharedPreferences(PREFS,MODE_PRIVATE);
        int prev=pref.getInt("knowledge_tip_index",-1),idx=(prev+1)%tips.length;
        pref.edit().putInt("knowledge_tip_index",idx).apply();
        LinearLayout c=new LinearLayout(this);c.setOrientation(LinearLayout.VERTICAL);c.setPadding(dp(14),dp(13),dp(14),dp(13));c.setBackground(round(Color.rgb(255,251,232),17,Color.rgb(235,213,143),1));
        TextView title=text(t("💡 ज्ञानको कुरा","💡 Safety knowledge"),16,true,Color.rgb(112,76,16));
        TextView body=text(t(tips[idx][0],tips[idx][1]),13,false,Color.rgb(70,66,50));body.setPadding(0,dp(7),0,dp(6));
        TextView meta=text(t("Fresh news नभएको बेला नयाँ safety tip • अर्को check मा अर्को tip","A new safety tip when there is no fresh news • the next check shows another tip"),10,true,Color.rgb(130,112,67));
        c.addView(title);c.addView(body);c.addView(meta);newsList.addView(c);
        main.removeCallbacks(knowledgeRotate);main.postDelayed(knowledgeRotate,10L*60L*1000L);
    }

'''
privacy_anchor = '    private void showPrivacy(){'
if 'private void renderKnowledgeTip()' not in text:
    if privacy_anchor not in text:
        raise SystemExit('privacy anchor missing')
    text = text.replace(privacy_anchor, knowledge + privacy_anchor, 1)

src.write_text(text, encoding='utf-8')

# Distinct field-test build.
gradle = gradle_path.read_text(encoding='utf-8')
gradle = gradle.replace('versionCode 20', 'versionCode 21', 1)
gradle = gradle.replace("versionName '0.8.0'", "versionName '0.8.1'", 1)
if 'versionCode 21' not in gradle or "versionName '0.8.1'" not in gradle:
    raise SystemExit('v0.8.1 version bump failed')
gradle_path.write_text(gradle, encoding='utf-8')

check=src.read_text(encoding='utf-8')
for marker in [
    'requestDisallowInterceptTouchEvent(true)',
    'private void showDistrictPicker()',
    'Only key/risk-priority stations are shown here.',
    'private void renderKnowledgeTip()',
    'knowledge_tip_index',
    'p.setAlpha(118);p.setStrokeWidth(1.25f);'
]:
    if marker not in check:
        raise SystemExit('v0.8.1 marker missing: '+marker)
print('FloodSafe native v0.8.1 polish PASS')
