from pathlib import Path

root = Path(__file__).resolve().parent
src = root / 'app/src/main/java/io/github/pujan1234hub/floodsafe/app'
activity_path = src / 'NativeFullActivity.java'
helper_path = src / 'FloodSafeNativeMapView.java'
gradle_path = root / 'app/build.gradle'

activity = activity_path.read_text(encoding='utf-8')
helper = helper_path.read_text(encoding='utf-8')
gradle = gradle_path.read_text(encoding='utf-8')

# -----------------------------------------------------------------------------
# v0.8.5 MAP: preserve continuous Nepal river geometry instead of deleting every
# individual point outside a district polygon. The v0.8.4 point-by-point filter
# fragmented many lines into <2 point pieces, which made glow/flow disappear.
# -----------------------------------------------------------------------------
strict = 'if (Double.isFinite(la) && Double.isFinite(lo) && isNepalish(la, lo) && (nepalDistricts == null || insideDistricts(lo, la, nepalDistricts))) rw.points.add(new double[]{lo, la});'
restored = 'if (Double.isFinite(la) && Double.isFinite(lo) && isNepalish(la, lo)) rw.points.add(new double[]{lo, la});'
if strict in helper:
    helper = helper.replace(strict, restored, 1)
elif restored not in helper:
    raise SystemExit('v0.8.4 river point filter anchor missing')

add_anchor = '                        if (rw.points.size() >= 2) all.add(rw);'
add_new = '                        if (nepalDistricts != null && rw.points.size() >= 2) trimRiverToNepal(rw, nepalDistricts);\n                        if (rw.points.size() >= 2) all.add(rw);'
if add_anchor in helper and 'trimRiverToNepal(rw, nepalDistricts)' not in helper:
    helper = helper.replace(add_anchor, add_new, 1)

# Add a tolerant continuous trim. It keeps a one-point margin around the first
# and last point touching Nepal, so a line stays continuous and particles can
# travel through it. Small tolerance protects border rivers from geometry gaps.
trim_anchor = '    private static boolean insideDistricts(double lo, double la, JSONObject districtRoot) {'
trim_helpers = r'''    private static boolean insideNepalSoft(double lo,double la,JSONObject districtRoot) {
        if (insideDistricts(lo,la,districtRoot)) return true;
        final double e=0.035;
        return insideDistricts(lo+e,la,districtRoot)||insideDistricts(lo-e,la,districtRoot)||
               insideDistricts(lo,la+e,districtRoot)||insideDistricts(lo,la-e,districtRoot)||
               insideDistricts(lo+e,la+e,districtRoot)||insideDistricts(lo-e,la+e,districtRoot)||
               insideDistricts(lo+e,la-e,districtRoot)||insideDistricts(lo-e,la-e,districtRoot);
    }

    private static void trimRiverToNepal(RiverWay r,JSONObject districtRoot) {
        if (r==null||r.points.size()<2||districtRoot==null) return;
        int first=-1,last=-1;
        for(int i=0;i<r.points.size();i++){
            double[] p=r.points.get(i);
            if(insideNepalSoft(p[0],p[1],districtRoot)){if(first<0)first=i;last=i;}
        }
        if(first<0||last<0){r.points.clear();return;}
        first=Math.max(0,first-1);last=Math.min(r.points.size()-1,last+1);
        if(first==0&&last==r.points.size()-1)return;
        List<double[]> keep=new ArrayList<>(r.points.subList(first,last+1));
        r.points.clear();r.points.addAll(keep);
    }

'''
if 'private static boolean insideNepalSoft' not in helper:
    if trim_anchor not in helper:
        raise SystemExit('insideDistricts anchor missing')
    helper = helper.replace(trim_anchor, trim_helpers + trim_anchor, 1)

# Make the original web-like cyan hierarchy obvious on satellite imagery.
helper = helper.replace('lineColor("#008fc7"), lineWidth(6.2f), lineOpacity(0.42f)',
                        'lineColor("#00bde9"), lineWidth(7.4f), lineOpacity(0.58f)')
helper = helper.replace('lineColor("#54e7ff"), lineWidth(2.15f), lineOpacity(1.0f)',
                        'lineColor("#7ceeff"), lineWidth(2.65f), lineOpacity(1.0f)')

# Flow beads need to be visible at city zoom too, not only on 36 national ways.
helper = helper.replace('ensurePointSource("fs-flow-particles", "fs-flow-particles-layer", "#d6fbff", 2.7f, 0.90f);',
                        'ensurePointSource("fs-flow-particles", "fs-flow-particles-layer", "#ffffff", 3.4f, 1.0f);')
helper = helper.replace('int n = Math.min(36, rivers.size());', 'int n = Math.min(96, rivers.size());')
helper = helper.replace('main.postDelayed(this, 160L);', 'main.postDelayed(this, 180L);')

helper_path.write_text(helper, encoding='utf-8')

# -----------------------------------------------------------------------------
# v0.8.5 SATHI: typo-tolerant Romanized Nepali, app-context follow-ups and more
# human conversation, while staying grounded in data already used by FloodSafe.
# -----------------------------------------------------------------------------
if 'private String lastSathiPlaceName=' not in activity:
    activity = activity.replace('private String lastSathiQuestion="",lastSathiAnswer="";',
                                'private String lastSathiQuestion="",lastSathiAnswer="";\n    private String lastSathiPlaceName="";\n    private double lastSathiPlaceLat=Double.NaN,lastSathiPlaceLon=Double.NaN;')

old_norm = '    private static String sathiNorm(String s){return s==null?"":s.toLowerCase(Locale.ROOT).replaceAll("[^\\\\p{L}\\\\p{N}]+"," ").trim();}'
new_norm = r'''    private static String sathiNorm(String s){
        String x=s==null?"":s.toLowerCase(Locale.ROOT).replaceAll("[^\\p{L}\\p{N}]+"," ").trim();
        x=x.replaceAll("\\b(tatkram|tapkarm|taapkram|tapkramm|tempreature|temprature)\\b","tapkram");
        x=x.replaceAll("\\b(mosam|mousam|mausam)\\b","mausam");
        x=x.replaceAll("\\b(barsa|barsaa|barsha|varsa|varsha)\\b","rain");
        x=x.replaceAll("\\b(kathmadu|kathmandu|ktm)\\b","ktm");
        x=x.replaceAll("\\b(chha|xa)\\b","cha");
        return x.replaceAll("\\s+"," ").trim();
    }'''
if old_norm in activity:
    activity = activity.replace(old_norm, new_norm, 1)
elif 'tatkram|tapkarm|taapkram' not in activity:
    raise SystemExit('SATHI normalization anchor missing')

# Explicit weather helper makes common Romanized questions resilient instead of
# depending on a brittle exact keyword list.
has_anchor = '    private static boolean hasAny(String x,String...a){for(String s:a)if(x.contains(s))return true;return false;}'
weather_helpers = r'''    private static boolean sathiWeatherIntent(String x){
        if(hasAny(x,"weather","mausam","tapkram","temperature","temp","garmi","chiso","rain","bholi","forecast","मौसम","तापक्रम","वर्षा","भोलि"))return true;
        for(String tok:x.split(" ")){if(tok.length()>=5&&(editDistance(tok,"tapkram")<=2||editDistance(tok,"mausam")<=2))return true;}
        return false;
    }
    private static int editDistance(String a,String b){
        if(a==null)a="";if(b==null)b="";int[] p=new int[b.length()+1];for(int j=0;j<=b.length();j++)p[j]=j;
        for(int i=1;i<=a.length();i++){int prev=p[0];p[0]=i;for(int j=1;j<=b.length();j++){int old=p[j],cost=a.charAt(i-1)==b.charAt(j-1)?0:1;p[j]=Math.min(Math.min(p[j]+1,p[j-1]+1),prev+cost);prev=old;}}return p[b.length()];
    }
'''
if 'private static boolean sathiWeatherIntent' not in activity:
    if has_anchor not in activity:
        raise SystemExit('hasAny anchor missing')
    activity = activity.replace(has_anchor, has_anchor + '\n' + weather_helpers, 1)

# Replace brittle weather checks in the generated v0.8.4 brain.
activity = activity.replace('hasAny(nq,"weather","mausam","temp","temperature","tapkram","तापक्रम","मौसम","वर्षा","rain","bholi","भोलि")', 'sathiWeatherIntent(nq)')
activity = activity.replace('hasAny(x,"weather","mausam","tapkram","temperature","temp","मौसम","तापक्रम","rain","barsaa","varsha","वर्षा")', 'sathiWeatherIntent(x)')

# Remember an explicit place and reuse it for natural follow-ups such as
# "ani bholi?" or "temperature kati?".
place_start = '    private PlacePoint sathiPlace(String q,String x){'
if place_start not in activity:
    raise SystemExit('sathiPlace anchor missing')
activity = activity.replace('if(hasAny(x,"ktm","kathmandu","काठमाडौं","काठमाण्डौ"))return new PlacePoint("Kathmandu",27.7172,85.3240);',
                            'if(hasAny(x,"ktm","kathmandu","काठमाडौं","काठमाण्डौ"))return rememberSathiPlace(new PlacePoint("Kathmandu",27.7172,85.3240));')
activity = activity.replace('if(hasAny(x,"pokhara","पोखरा"))return new PlacePoint("Pokhara",28.2096,83.9856);',
                            'if(hasAny(x,"pokhara","पोखरा"))return rememberSathiPlace(new PlacePoint("Pokhara",28.2096,83.9856));')
activity = activity.replace('if(hasAny(x,"biratnagar","विराटनगर"))return new PlacePoint("Biratnagar",26.4525,87.2718);',
                            'if(hasAny(x,"biratnagar","विराटनगर"))return rememberSathiPlace(new PlacePoint("Biratnagar",26.4525,87.2718));')

# Add remember/follow-up helper just before sathiPlace.
remember_method = r'''    private PlacePoint rememberSathiPlace(PlacePoint p){if(p!=null){lastSathiPlaceName=p.name;lastSathiPlaceLat=p.lat;lastSathiPlaceLon=p.lon;}return p;}
    private PlacePoint sathiFollowupPlace(String x){
        if(!lastSathiPlaceName.isEmpty()&&Double.isFinite(lastSathiPlaceLat)&&Double.isFinite(lastSathiPlaceLon)&&
           (sathiWeatherIntent(x)||hasAny(x,"ani","अनि","aile","ahile","aahele","bholi","भोलि","kati","kasto")))
            return new PlacePoint(lastSathiPlaceName,lastSathiPlaceLat,lastSathiPlaceLon);
        return null;
    }
'''
if 'private PlacePoint rememberSathiPlace' not in activity:
    activity = activity.replace(place_start, remember_method + '\n' + place_start, 1)

# Add follow-up fallback immediately before final null return in sathiPlace if a
# clear anchor exists. This keeps app-grounded conversation continuous.
place_end_candidates = [
    '        return null;\n    }\n\n    private static final class PlacePoint',
    '        return null;\n    }\n    private static final class PlacePoint'
]
for pe in place_end_candidates:
    if pe in activity:
        activity = activity.replace(pe, '        PlacePoint follow=sathiFollowupPlace(x);if(follow!=null)return follow;\n        return null;\n    }\n\n    private static final class PlacePoint', 1)
        break

# If user gives a place plus "k cha" and a temperature typo, normalization now
# routes it to live weather. Also make the generic app-domain fallback feel like
# a useful friend rather than repeating a capability disclaimer.
generic = 'म FloodSafe Nepal को SATHI हुँ 🙂 म app भित्रको live मौसम, नदी/खोला station, water level, Warning/Danger, तपाईंको नजिकको risk, Human Status, समाचार र notification बारे मात्र verified app data बाट उत्तर दिन्छु। त्यो दायराभित्र जे सोध्नुभयो म बुझेर भन्न खोज्छु।'
friendlier = 'बुझेँ 🙂 यो FloodSafe कै कुरा हो भने म सँगै हेर्छु। ठाउँको मौसम/तापक्रम, नदी वा station को नाम, नजिकको flood risk, Warning/Danger, Human Status, समाचार वा notification मध्ये जे जान्न चाहनुहुन्छ सीधै सोध्नुहोस्। नाम अलि typo भए पनि म मिलाएर खोज्ने प्रयास गर्छु।'
activity = activity.replace(generic, friendlier)

activity_path.write_text(activity, encoding='utf-8')

# Version bump.
if "versionName '0.8.5'" not in gradle:
    gradle = gradle.replace('versionCode 24', 'versionCode 25', 1)
    gradle = gradle.replace("versionName '0.8.4'", "versionName '0.8.5'", 1)
if 'versionCode 25' not in gradle or "versionName '0.8.5'" not in gradle:
    raise SystemExit('v0.8.5 version bump failed')
gradle_path.write_text(gradle, encoding='utf-8')

index_path = root.parent / 'floodsafe-nepal/v25/index.html'
if index_path.is_file():
    index=index_path.read_text(encoding='utf-8').replace('<span class="badge green">v0.8.4</span>','<span class="badge green">v0.8.5</span>')
    index_path.write_text(index,encoding='utf-8')

# Build-time assertions.
h = helper_path.read_text(encoding='utf-8')
a = activity_path.read_text(encoding='utf-8')
for marker in ['trimRiverToNepal(rw, nepalDistricts)','insideNepalSoft','lineWidth(7.4f)','Math.min(96, rivers.size())','fs-flow-particles-layer']:
    if marker not in h: raise SystemExit('v0.8.5 map marker missing: '+marker)
for marker in ['tatkram|tapkarm|taapkram','sathiWeatherIntent','editDistance','rememberSathiPlace','findSathiStation']:
    if marker not in a: raise SystemExit('v0.8.5 SATHI marker missing: '+marker)
print('FloodSafe v0.8.5 river flow + typo-tolerant conversational SATHI patch PASS')
