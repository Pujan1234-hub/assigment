from pathlib import Path
import re

UI = Path("floodsafe-android-app/app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java")
s = UI.read_text(encoding="utf-8")

pattern = r'    private void showSathiDialog\(String initial\)\{.*?    private void consumeSathiIntent\(Intent i\)\{'

replacement = r'''    private void showSathiDialog(String initial){
        LinearLayout box=new LinearLayout(this);box.setOrientation(LinearLayout.VERTICAL);box.setPadding(dp(18),dp(8),dp(18),0);
        TextView transcript=text(t("नमस्ते! म SATHI हुँ। मौसम, नदी, warning, nearby station वा app status बारे सोध्नुस् — म तपाईंलाई app को हालको data हेरेर जवाफ दिन्छु।","Hi! I'm SATHI. Ask me about weather, rivers, warnings, nearby stations or app status — I'll answer from the app's current data."),14,false,Color.rgb(30,52,72));
        transcript.setPadding(dp(12),dp(12),dp(12),dp(12));transcript.setBackground(round(Color.rgb(248,252,254),16,Color.rgb(200,223,234),1));
        ScrollView chatScroll=new ScrollView(this);chatScroll.setFillViewport(true);chatScroll.addView(transcript);box.addView(chatScroll,lp(-1,dp(230),0,0,0,dp(10)));
        EditText input=new EditText(this);input.setHint(t("जस्तै: आज पानी पर्छ?","For example: Will it rain today?"));input.setTextSize(14);input.setMinLines(2);input.setMaxLines(4);input.setSingleLine(false);input.setPadding(dp(12),dp(10),dp(12),dp(10));input.setBackground(round(Color.rgb(248,252,254),16,Color.rgb(200,223,234),1));box.addView(input,lp(-1,-2,0,0,0,dp(8)));
        LinearLayout actions=new LinearLayout(this);actions.setOrientation(LinearLayout.HORIZONTAL);
        Button ask=button(t("➤ सोध्नुहोस्","➤ Ask")),mic=button(t("🎙️ आवाज","🎙️ Voice"));actions.addView(ask,new LinearLayout.LayoutParams(0,dp(52),1f));LinearLayout.LayoutParams mp=new LinearLayout.LayoutParams(0,dp(52),1f);mp.setMargins(dp(6),0,0,0);actions.addView(mic,mp);box.addView(actions);
        AlertDialog d=new AlertDialog.Builder(this).setTitle("🤖 SATHI").setView(box).setNegativeButton(t("बन्द","Close"),null).create();
        Runnable submit=()->{String q=input.getText().toString().trim();if(q.isEmpty())return;String a=answerSathi(q);appendSathiTurn(transcript,chatScroll,q,a);input.setText("");speak(a);};
        ask.setOnClickListener(v->submit.run());mic.setOnClickListener(v->startVoice(transcript,chatScroll));d.show();
        if(initial!=null&&!initial.trim().isEmpty()){String q=initial.trim();String a=answerSathi(q);transcript.setText("");appendSathiTurn(transcript,chatScroll,q,a);speak(a);}
    } // V0910_SATHI_CONVERSATIONAL_CHAT

    private void appendSathiTurn(TextView out,ScrollView chatScroll,String q,String a){
        String before=String.valueOf(out.getText()).trim();String who=t("तपाईं","You");
        String turn=who+": "+q+"\n\nSATHI: "+a;out.setText(before.isEmpty()?turn:before+"\n\n"+turn);
        if(chatScroll!=null)chatScroll.post(()->chatScroll.fullScroll(View.FOCUS_DOWN));
    }

    private void startVoice(TextView out,ScrollView chatScroll){
        if(checkSelfPermission(Manifest.permission.RECORD_AUDIO)!=PackageManager.PERMISSION_GRANTED){requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO},REQ_MIC);return;}
        if(!SpeechRecognizer.isRecognitionAvailable(this)){String a=t("यो फोनमा voice recognition उपलब्ध छैन।","Voice recognition is unavailable on this phone.");appendSathiTurn(out,chatScroll,t("आवाज","Voice"),a);return;}
        if(speech!=null)try{speech.destroy();}catch(Exception ignored){}
        final String before=String.valueOf(out.getText());
        speech=SpeechRecognizer.createSpeechRecognizer(this);speech.setRecognitionListener(new RecognitionListener(){
            public void onReadyForSpeech(Bundle b){out.setText(before+(before.trim().isEmpty()?"":"\n\n")+t("🎙 सुन्दैछु…","🎙 Listening…"));if(chatScroll!=null)chatScroll.post(()->chatScroll.fullScroll(View.FOCUS_DOWN));}
            public void onBeginningOfSpeech(){}public void onRmsChanged(float x){}public void onBufferReceived(byte[]b){}public void onEndOfSpeech(){}
            public void onError(int e){out.setText(before);String a=t("माफ गर्नुहोस्, आवाज स्पष्ट बुझिनँ। फेरि भन्नुस् वा तल लेखेर सोध्नुस्।","Sorry, I couldn't understand that clearly. Please try again or type your question below.");String p=String.valueOf(out.getText()).trim();out.setText(p.isEmpty()?"SATHI: "+a:p+"\n\nSATHI: "+a);if(chatScroll!=null)chatScroll.post(()->chatScroll.fullScroll(View.FOCUS_DOWN));}
            public void onPartialResults(Bundle b){}public void onEvent(int t,Bundle b){}
            public void onResults(Bundle b){ArrayList<String> r=b.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);String q=r==null||r.isEmpty()?"":r.get(0).trim();out.setText(before);if(q.isEmpty()){String a=t("माफ गर्नुहोस्, प्रश्न सुनिनँ। फेरि प्रयास गर्नुस्।","Sorry, I didn't catch a question. Please try again.");String p=String.valueOf(out.getText()).trim();out.setText(p.isEmpty()?"SATHI: "+a:p+"\n\nSATHI: "+a);return;}String a=answerSathi(q);appendSathiTurn(out,chatScroll,q,a);speak(a);}
        });
        speech.startListening(new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL,RecognizerIntent.LANGUAGE_MODEL_FREE_FORM).putExtra(RecognizerIntent.EXTRA_LANGUAGE,english?"en-GB":"ne-NP").putExtra(RecognizerIntent.EXTRA_MAX_RESULTS,5));
    }

    private String answerSathi(String q){
        String x=q==null?"":q.toLowerCase(Locale.ROOT).trim();
        if(x.isEmpty())return t("म यहाँ छु 🙂 प्रश्न लेख्नुस् वा आवाजबाट सोध्नुस्।","I'm here 🙂 Type a question or ask by voice.");
        if(x.contains("thank")||x.contains("thanks")||x.contains("dhany")||x.contains("धन्यवाद"))return t("स्वागत छ 🙂 सुरक्षित रहनुस्। अरू केही जान्न मन लागे सोध्नुस्।","You're welcome 🙂 Stay safe. Ask me anything else about the app's safety data.");
        if(x.matches(".*\\b(hi|hello|hey|namaste|namaskar)\\b.*")||x.contains("नमस्ते")||x.contains("नमस्कार"))return t("नमस्ते 🙂 म SATHI हुँ। अहिलेको मौसम, नदीको अवस्था, warning/danger वा नजिकको station बारे सोध्नुस्।","Hi 🙂 I'm SATHI. You can ask me about current weather, river status, warnings/danger or nearby stations.");
        if(x.contains("how are you")||x.contains("kasto chau")||x.contains("kasto chhau")||x.contains("सन्चै")||x.contains("सन्चो"))return t("म ठीक छु 🙂 तपाईंलाई सुरक्षित राख्न app को हालको weather र river data हेर्न तयार छु।","I'm good 🙂 I'm ready to help you with the app's current weather and river safety data.");
        if(x.contains("who are you")||x.contains("what are you")||x.contains("timi ko")||x.contains("तिमी को")||x.contains("sathi ke"))return t("म FloodSafe Nepal को SATHI safety assistant हुँ। म app भित्र आएको हालको मौसम, नदी, station र warning data बुझ्न सजिलो भाषामा बताउँछु।","I'm SATHI, FloodSafe Nepal's safety assistant. I explain the app's current weather, river, station and warning data in simple language.");

        boolean weatherQ=x.contains("weather")||x.contains("मौसम")||x.contains("mausam")||x.contains("rain")||x.contains("वर्षा")||x.contains("pani")||x.contains("पानी")||x.contains("temperature")||x.contains("temp")||x.contains("garmi")||x.contains("chiso")||x.contains("aaja")||x.contains("आज");
        if(weatherQ){if(currentWeather.isEmpty())return t("मौसम data अहिले refresh हुँदैछ। केही क्षणपछि फेरि सोध्नुस्।","Weather data is refreshing right now. Please ask again in a moment.");return t("अहिलेको मौसम अनुसार: ","From the current weather data: ")+currentWeather;}

        boolean riverQ=x.contains("river")||x.contains("नदी")||x.contains("nadi")||x.contains("खोला")||x.contains("khola")||x.contains("flood")||x.contains("बाढी")||x.contains("badhi")||x.contains("badi")||x.contains("danger")||x.contains("warning")||x.contains("alert")||x.contains("चेतावनी")||x.contains("chetawani");
        if(riverQ){int d=0,w=0,a=0,fresh=0,total=0;synchronized(stations){for(RiverStation s:stations){total++;if(!s.fresh)continue;fresh++;if(s.stage.equals("danger"))d++;else if(s.stage.equals("warning"))w++;else if(s.stage.equals("alert"))a++;}}
            if(d>0)return t("अहिले fresh official river data मा "+d+" Danger, "+w+" Warning र "+a+" Alert छन्। Danger देखिएको नदी/स्टेशनबाट सुरक्षित दूरी राख्नुस् र map मा सम्बन्धित station खोलेर detail हेर्नुस्।","Current fresh official river data shows "+d+" Danger, "+w+" Warning and "+a+" Alert. Keep a safe distance from affected rivers/stations and open the relevant station on the map for details.");
            if(w>0||a>0)return t("अहिले fresh official river data मा Danger छैन; "+w+" Warning र "+a+" Alert छन्। "+fresh+" fresh station reading उपलब्ध छन्।","There is no fresh Danger right now; current official data shows "+w+" Warning and "+a+" Alert, with "+fresh+" fresh station readings available.");
            return t("अहिले "+fresh+" fresh official station reading मध्ये Danger/Warning/Alert देखिएको छैन। कुल "+total+" station app मा छन्; stale data लाई live threat मानिँदैन।","Among "+fresh+" fresh official station readings, none currently show Danger/Warning/Alert. The app has "+total+" stations in total; stale data is not treated as a live threat.");}

        if(x.contains("station")||x.contains("स्टेशन")||x.contains("nearby")||x.contains("najik")||x.contains("नजिक")){int fresh=0,total=0;synchronized(stations){for(RiverStation s:stations){total++;if(s.fresh)fresh++;}}if(Double.isFinite(lat)&&Double.isFinite(lon))return t("तपाईंको GPS location उपलब्ध छ। Nearby River Stations section ले यही location प्रयोग गर्छ। अहिले app मा "+total+" official station छन्, जसमध्ये "+fresh+" fresh छन्।","Your GPS location is available. Nearby River Stations uses this location. The app currently has "+total+" official stations, with "+fresh+" fresh readings.");return t("Official station data उपलब्ध छ, तर nearby station देखाउन GPS location चाहिन्छ। Location permission/GPS on भएपछि नजिकका station देखिन्छन्।","Official station data is available, but GPS location is needed to show nearby stations. Turn on location/permission to see the nearest stations.");}

        if(x.contains("location")||x.contains("gps")||x.contains("ma kaha")||x.contains("म कहाँ")){if(Double.isFinite(lat)&&Double.isFinite(lon))return t("GPS location active छ। FloodSafe ले nearby station र verified local river alert का लागि यही location प्रयोग गर्छ।","GPS location is active. FloodSafe uses it for nearby stations and verified local river alerts.");return t("अहिले GPS location उपलब्ध छैन। Location on/allow गरेपछि nearby river information update हुन्छ।","GPS location isn't available right now. Turn on/allow location to update nearby river information.");}

        if(x.contains("notification")||x.contains("सूचना"))return t("Safety monitoring active हुँदा weather digest र verified local river Warning/Danger notification background मा जाँच हुन्छ। Android ले background timing केही ढिलो गर्न सक्छ।","When safety monitoring is active, weather digests and verified local river Warning/Danger notifications are checked in the background. Android can sometimes defer background timing.");
        if(x.contains("app status")||x.equals("status")||x.contains("app thik")||x.contains("app ठीक"))return t("App चलिरहेको छ। Live sections ले fresh data आएपछि update गर्छन्, र stale river reading लाई live threat मानिँदैन।","The app is running. Live sections update when fresh data arrives, and stale river readings are not treated as a live threat.");

        return t("म त्यो प्रश्नको भरपर्दो उत्तर app को हालको data बाट निकाल्न सकिनँ। अलि फरक तरिकाले सोध्नुस् — जस्तै ‘आज पानी पर्छ?’, ‘कुनै नदी Danger मा छ?’, वा ‘मेरो नजिक station छ?’","I couldn't answer that reliably from the app's current data. Try asking it another way — for example, ‘Will it rain today?’, ‘Is any river in Danger?’, or ‘Is there a station near me?’");
    } // V0910_SATHI_NATURAL_GROUNDED_ANSWERS

    private void consumeSathiIntent(Intent i){'''

s2,n=re.subn(pattern,lambda m:replacement,s,count=1,flags=re.S)
if n!=1:
    raise SystemExit(f"SATHI block anchor expected once, got {n}")
s=s2

for marker in ["V0910_SATHI_CONVERSATIONAL_CHAT","V0910_SATHI_NATURAL_GROUNDED_ANSWERS"]:
    if marker not in s: raise SystemExit("missing marker "+marker)
if 'startVoice(answer)' in s: raise SystemExit('old SATHI voice call still present')
if 'android.webkit.WebView' in s: raise SystemExit('WebView introduced')

UI.write_text(s,encoding="utf-8")
print("V0910_STEP1_SATHI_CHAT_OK")
