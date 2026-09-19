from pathlib import Path
import re

root=Path(__file__).resolve().parent
a_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java'
g_path=root/'app/build.gradle'
a=a_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# v0.8.65: news language must follow the selected app language immediately.
# - English UI shows English-script Nepal news only.
# - Nepali UI shows Nepali/Devanagari Nepal news only.
# - language toggle refreshes news so old-language cards never remain on screen.
# - localized news age labels.
# Station inventory restoration, 20-minute river safety, 2 km alert radius and river-tap truth stay unchanged.

def method_span(text,name):
    q=re.search(r'(?m)^\s*private\s+[^\n{]+\b'+re.escape(name)+r'\s*\([^\n]*\)\s*\{',text)
    if not q:return None
    op=text.find('{',q.start());depth=0;quote=None;esc=False;i=op
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
                if depth==0:return q.start(),i+1
        i+=1
    return None

# Language button previously changed labels but left already-rendered news cards untouched.
old_toggle='applyLanguage();refreshRiverUi();});'
new_toggle='applyLanguage();refreshRiverUi();refreshNews();}); // V0865_LANGUAGE_REFRESHES_NEWS'
if old_toggle in a:
    a=a.replace(old_toggle,new_toggle,1)
elif 'V0865_LANGUAGE_REFRESHES_NEWS' not in a:
    raise SystemExit('v0865 language toggle anchor missing')

news=r'''    private void refreshNews(){
        if(newsList==null)return;
        final boolean wantEnglish=english;
        newsList.removeAllViews();
        newsList.addView(empty(wantEnglish?"Checking latest English Nepal news…":"नयाँ नेपाली समाचार जाँच हुँदैछ…"));
        io.execute(()->{
            try{
                JSONObject j=getJson(NEWS_ENDPOINT+"?_native="+System.currentTimeMillis());
                JSONArray arr=j.optJSONArray("items");if(arr==null)arr=j.optJSONArray("results");if(arr==null)arr=j.optJSONArray("news");if(arr==null)arr=new JSONArray();
                final List<NewsItem> out=new ArrayList<>();long now=System.currentTimeMillis();
                for(int i=0;i<arr.length()&&out.size()<12;i++){
                    JSONObject o=arr.optJSONObject(i);if(o==null)continue;
                    String source=str(o,"source"),title=v865NewsTitle(o,wantEnglish),url=str(o,"url","link");
                    long at=parseTime(str(o,"published_at","publishedAt","date"));
                    if(title.isEmpty()||url.isEmpty()||!(source.equals("RONB Post")||source.equals("Radio Nepal")||source.equals("News24 Nepal")))continue;
                    if(at>0&&now-at>30L*60L*1000L)continue;
                    if(!v865NewsLanguageMatches(title,wantEnglish))continue;
                    out.add(new NewsItem(title,source,url,at));
                }
                runOnUiThread(()->{
                    // A slower request from the old language must never repaint the new UI.
                    if(wantEnglish!=english){refreshNews();return;}
                    renderNews(out);
                });
            }catch(Exception e){runOnUiThread(()->{
                if(wantEnglish!=english){refreshNews();return;}
                newsList.removeAllViews();
                newsList.addView(empty(wantEnglish?"Live English Nepal news is currently unavailable.":"प्रत्यक्ष नेपाली समाचार अहिले उपलब्ध छैन।"));
            });}
        });
    } // V0865_NEWS_LANGUAGE_SYNC

    private static String v865NewsTitle(JSONObject o,boolean wantEnglish){
        if(o==null)return "";
        String preferred=wantEnglish
                ?str(o,"title_en","titleEnglish","english_title","headline_en")
                :str(o,"title_ne","title_np","titleNepali","nepali_title","headline_ne");
        if(!preferred.isEmpty())return preferred;
        return str(o,"title","headline");
    }

    private static boolean v865NewsLanguageMatches(String title,boolean wantEnglish){
        if(title==null||title.trim().isEmpty())return false;
        int dev=0,latin=0;
        for(int i=0;i<title.length();i++){
            char c=title.charAt(i);
            if(c>='\u0900'&&c<='\u097F'&&Character.isLetter(c))dev++;
            else if((c>='A'&&c<='Z')||(c>='a'&&c<='z'))latin++;
        }
        // A Nepali headline can contain English proper nouns, so require meaningful
        // Devanagari presence rather than rejecting it for a few Latin characters.
        boolean nepali=dev>=4 && dev*2>=latin;
        return wantEnglish?!nepali:nepali;
    } // V0865_NEWS_SCRIPT_FILTER

'''
span=method_span(a,'refreshNews')
if not span:raise SystemExit('v0865 refreshNews method missing')
a=a[:span[0]]+news+a[span[1]:]

render=r'''    private void renderNews(List<NewsItem> out){
        newsList.removeAllViews();
        if(out.isEmpty()){
            newsList.addView(empty(english?"No fresh English Nepal stories found.":"ताजा नेपाली समाचार भेटिएन।"));
            return;
        }
        for(NewsItem n:out){
            LinearLayout c=new LinearLayout(this);c.setOrientation(LinearLayout.VERTICAL);c.setPadding(dp(12),dp(11),dp(12),dp(11));c.setBackground(round(Color.rgb(248,252,254),17,Color.rgb(216,234,243),1));
            TextView title=text(n.title,15,true,Color.rgb(16,39,70));
            String age="";if(n.at>0){long min=Math.max(0,(System.currentTimeMillis()-n.at)/60000);age=english?min+" min ago":min+" मिनेटअघि";}
            TextView meta=text(n.source+(age.isEmpty()?"":" • "+age),11,false,Color.rgb(102,131,153));
            TextView open=text(t("खोल्नुहोस् ↗","Open ↗"),12,true,Color.rgb(20,119,184));open.setPadding(0,dp(5),0,0);open.setOnClickListener(v->{try{startActivity(new Intent(Intent.ACTION_VIEW,Uri.parse(n.url)));}catch(Exception ignored){}});
            c.addView(title);c.addView(meta);c.addView(open);LinearLayout.LayoutParams p=lp(-1,-2,0,0,0,dp(8));newsList.addView(c,p);
        }
    } // V0865_LOCALIZED_NEWS_RENDER

'''
span=method_span(a,'renderNews')
if not span:raise SystemExit('v0865 renderNews method missing')
a=a[:span[0]]+render+a[span[1]:]

# Version bump after v0.8.64 station inventory restoration.
if 'versionCode 84' in g:g=g.replace('versionCode 84','versionCode 85',1)
elif 'versionCode 85' not in g:raise SystemExit('v0865 versionCode anchor missing')
if "versionName '0.8.64'" in g:g=g.replace("versionName '0.8.64'","versionName '0.8.65'",1)
elif "versionName '0.8.65'" not in g:raise SystemExit('v0865 versionName anchor missing')

a_path.write_text(a,encoding='utf-8');g_path.write_text(g,encoding='utf-8')

for x in ['V0865_LANGUAGE_REFRESHES_NEWS','V0865_NEWS_LANGUAGE_SYNC','V0865_NEWS_SCRIPT_FILTER','V0865_LOCALIZED_NEWS_RENDER','V0864_NEVER_CLEAR_STATION_INVENTORY','V0863_RIVER_TAP_TRUTH','RIVER_FRESH_MS=20L*60L*1000L']:
    if x not in a:raise SystemExit('v0865 verification failed: '+x)
for x in ['versionCode 85',"versionName '0.8.65'"]:
    if x not in g:raise SystemExit('v0865 version verification failed: '+x)
print('FloodSafe v0.8.65 PASS: news follows selected language immediately; station inventory + 20m river safety preserved')
