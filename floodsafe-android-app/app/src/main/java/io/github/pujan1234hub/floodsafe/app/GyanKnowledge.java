package io.github.pujan1234hub.floodsafe.app;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Locale;

/** Curated offline education. Gita notes are interpretations, not quoted translations.
 * Flood safety guidance is education, not a live warning or substitute for local authorities.
 */
final class GyanKnowledge {
    static final class Entry {
        final String category, neTitle, enTitle, neBody, enBody, source;
        Entry(String c,String nt,String et,String nb,String eb,String s){
            category=c;neTitle=nt;enTitle=et;neBody=nb;enBody=eb;source=s;
        }
        String title(boolean en){return en?enTitle:neTitle;}
        String body(boolean en){return en?enBody:neBody;}
    }
    private GyanKnowledge(){}
    static final List<Entry> ITEMS;
    static {
        ArrayList<Entry> a=new ArrayList<>();
        add(a,"gita","फलको चिन्ताभन्दा कर्ममा ध्यान","Focus on effort, not outcomes",
            "भगवद्गीता २.४७ को जीवनोपयोगी भाव: आफ्नो नियन्त्रणमा भएको काम इमानदारीपूर्वक गरौँ। नतिजा सधैँ हाम्रो नियन्त्रणमा हुँदैन। अध्ययन वा काममा आज गर्न सकिने एउटा सानो कदम तय गर्नुहोस्।",
            "A practical reading of Gita 2.47: act diligently on what you can control; outcomes have many causes. Choose one useful action for today.","Bhagavad Gita 2.47");
        add(a,"gita","सफलता र असफलतामा सन्तुलन","Balance success and setbacks",
            "गीता २.४८ ले परिस्थितिको उतारचढावमा पनि विवेक राख्न प्रेरित गर्छ। असफल हुँदा गल्तीबाट सिक्ने र सफल हुँदा अहङ्कार नगर्ने अभ्यास उपयोगी हुन्छ।",
            "Gita 2.48 invites steadiness in changing circumstances. Learn from setbacks without losing perspective in success.","Bhagavad Gita 2.48");
        add(a,"gita","मनलाई मित्र बनाउने अभ्यास","Make the mind an ally",
            "गीता ६.५ को व्यावहारिक शिक्षा: आफैँलाई हेप्नुको सट्टा दिनचर्या, ध्यान र उपयोगी बानीबाट आफूलाई माथि उठाउने प्रयास गर्नुहोस्।",
            "A practical interpretation of Gita 6.5: encourage yourself through habits, reflection and constructive daily choices.","Bhagavad Gita 6.5");
        add(a,"gita","परिवर्तनलाई स्वीकार्ने क्षमता","Learning to face change",
            "गीता २.१४ मा सुख-दुःख तथा अनुकूल-प्रतिकूल अनुभव परिवर्तनशील हुने चर्चा छ। कठिन बेला आवेगमा निर्णय नगरी आवश्यक सहयोग र उचित समय लिनुहोस्।",
            "Gita 2.14 discusses changing experiences of comfort and discomfort. Pause before impulsive decisions and seek support when necessary.","Bhagavad Gita 2.14");
        add(a,"gita","अनुशासन र नियमित अभ्यास","Practice and discipline",
            "गीता ६.३५ को सन्देश: मन चञ्चल हुन सक्छ, तर अभ्यास र अनासक्तिले स्थिरता बढाउन सकिन्छ। एकैदिन धेरै होइन, दैनिक थोरै अभ्यासलाई निरन्तरता दिनुहोस्।",
            "Gita 6.35 connects mental steadiness with practice and detachment. Prefer a small repeatable routine over an unsustainable burst.","Bhagavad Gita 6.35");
        add(a,"gita","आफ्नो क्षमता अनुसार जिम्मेवारी","Responsibility and one's own path",
            "गीता ३.३५ को एक अर्थ आफ्ना कर्तव्य र क्षमतामा केन्द्रित रहनु हो। अरूको यात्रा नक्कल गर्नुभन्दा आफ्ना मूल्य र परिस्थितिसँग मिल्ने बाटो सोच्नुहोस्।",
            "One reading of Gita 3.35 is to act from your own responsibilities rather than blindly imitate someone else's path.","Bhagavad Gita 3.35");

        add(a,"flood","बाढी चेतावनी पाएपछि","When a flood warning arrives",
            "अधिकारिक DHM/स्थानीय प्रशासनको मितिसहितको सूचना जाँच्नुहोस्। सुरक्षित उचाइतर्फ जाने बाटो र परिवारको सम्पर्क योजना तयार राख्नुहोस्। खोल्सा, पुल र बाढी आएको सडक पार नगर्नुहोस्।",
            "Check dated official DHM/local instructions, prepare a safe higher-ground route and family contact plan, and never enter flooded roads or crossings.","General flood safety; verify DHM and local authority");
        add(a,"flood","नदीको जलस्तर बुझ्ने तरिका","Understanding river-gauge levels",
            "मिटरमा देखिएको संख्या एक्लैले खतरा बताउँदैन। सोही स्टेशनको चेतावनी/खतरा सीमा, मापन समय र बढ्दो-घट्दो क्रम हेर्नुपर्छ। पुरानो मापनलाई अहिलेको अवस्था नठान्नुहोस्।",
            "A water level in metres is not a universal danger threshold. Compare with that gauge's thresholds, timestamp and trend; stale readings are not current conditions.","DHM/BIPAD gauge interpretation");
        add(a,"flood","बाढीमा पैदल वा सवारी सुरक्षित राख्ने","Avoid flooded roads",
            "देखिनेभन्दा पानी गहिरो वा बहाव तीव्र हुन सक्छ। बाढीको पानीमा पैदल, बाइक वा गाडी चलाएर पार नगर्नुहोस्। सुरक्षित बाटो खोज्नुहोस् र स्थानीय निर्देशन मान्नुहोस्।",
            "Floodwater may hide depth, currents and road damage. Do not walk, ride or drive through it; choose a safe route and follow local advice.","General flood safety");
        add(a,"flood","आपतकालीन झोला","Prepare a go-bag",
            "औषधि, पानी, सुक्खा खाना, टर्च, पावर बैंक, आवश्यक कागजातको जलरोधी प्रतिलिपि र परिवारका नम्बर राख्नुहोस्। बच्चा, ज्येष्ठ नागरिक र अपाङ्गता भएका व्यक्तिको आवश्यकतालाई प्राथमिकता दिनुहोस्।",
            "Pack essential medication, drinking water, torch, power bank, protected document copies and contact numbers. Plan for children and people with additional needs.","Household disaster preparedness");
        add(a,"flood","वर्षा पूर्वानुमान र वास्तविक मापन","Forecast versus observation",
            "मौसम मोडेलको वर्षा अनुमान, NASA satellite चित्र र नदी स्टेशनको वास्तविक मापन फरक स्रोत हुन्। एउटालाई अर्कोको प्रत्यक्ष प्रमाण नठान्नुहोस्; स्रोत र समय हेर्नुहोस्।",
            "Weather forecasts, satellite layers and measured river levels answer different questions. Compare source, location and update time; do not treat a model as a measured warning.","Weather model and gauge literacy");
        add(a,"flood","बाढीपछि घर फर्कँदा","Returning after a flood",
            "स्थानीय निकायले सुरक्षित भनेपछि मात्र फर्कनुहोस्। बिजुली, दूषित पानी, कमजोर संरचना र पहिरोको जोखिम हुन सक्छ। पानी/खानाको स्वच्छता सुनिश्चित गर्नुहोस्।",
            "Return only when authorities say it is safe. Watch for damaged structures, electrical hazards, contaminated water and landslide risks.","General post-flood safety");

        add(a,"general","नेपालका ७ प्रदेश","Nepal's seven provinces",
            "नेपालका प्रदेश: कोशी, मधेश, बागमती, गण्डकी, लुम्बिनी, कर्णाली र सुदूरपश्चिम। नेपालमा ७७ जिल्ला छन्।",
            "Nepal has seven provinces: Koshi, Madhesh, Bagmati, Gandaki, Lumbini, Karnali and Sudurpashchim; it has 77 districts.","Nepal administrative geography");
        add(a,"general","भूगोल: अक्षांश र देशान्तर","Latitude and longitude",
            "अक्षांशले भूमध्यरेखाबाट उत्तर-दक्षिण स्थान, देशान्तरले पूर्व-पश्चिम स्थान बताउँछ। GPS ले यी निर्देशाङ्कमार्फत नक्सामा स्थान देखाउँछ।",
            "Latitude measures north-south position from the equator; longitude locates east-west position. GPS uses coordinates to show a place on a map.","Basic geography");
        add(a,"general","नक्साको स्केल","Reading map scale",
            "नक्साको स्केलले नक्साको दूरी र जमिनको वास्तविक दूरीको सम्बन्ध बताउँछ। नक्सा zoom गर्दा देखिने लम्बाइ बदलिन्छ, वास्तविक दूरी बदलिँदैन।",
            "Map scale relates map distance to ground distance. Zoom changes screen size, not real-world distance.","Basic cartography");
        add(a,"general","प्राथमिक उपचारको पहिलो नियम","First aid: safety first",
            "दुर्घटनास्थल आफ्ना लागि सुरक्षित छ कि छैन पहिले हेर्नुहोस्। सम्भव भए तत्काल स्थानीय आपतकालीन सेवालाई खबर गर्नुहोस्। आफ्नै सुरक्षालाई जोखिममा राखेर उद्धार प्रयास नगर्नुहोस्।",
            "First check scene safety and contact local emergency help when needed. Avoid becoming another casualty.","Introductory first aid");
        add(a,"general","विश्वसनीय जानकारी पहिचान","Spot credible information",
            "कुनै सूचना शेयर गर्नुअघि स्रोत, प्रकाशन मिति, लेखक/निकाय र अर्को स्वतन्त्र स्रोत जाँच्नुहोस्। पुरानो समाचारलाई नयाँ भनेर फैलाउनु हुँदैन।",
            "Before sharing a claim, check its source, date, author and independent confirmation. Old stories can be recirculated as new.","Information literacy");
        add(a,"general","नागरिक जिम्मेवारी","Civic responsibility",
            "समुदायमा विपद् सूचना पाउँदा अपुष्ट हल्ला होइन, सत्यापित सूचना साझा गर्नुहोस्। असुरक्षित व्यक्तिलाई निर्देशन बुझ्न सहयोग गर्नुहोस्।",
            "During an emergency, share verified notices rather than rumours and help neighbours understand practical safety guidance.","Civic and community knowledge");

        add(a,"science","जलचक्र कसरी चल्छ?","How the water cycle works",
            "सूर्यको तापले पानी वाष्पीकरण हुन्छ, वाष्प चिसिएर बादल बन्छ र वर्षा हुन्छ। पानीको एक भाग जमिनमा सोसिन्छ, अर्को भाग खोलानालामा बग्छ।",
            "Heat evaporates water; vapour condenses into clouds and falls as precipitation. Some water infiltrates soil; some runs into rivers.","Basic earth science");
        add(a,"science","मौसम र जलवायुको अन्तर","Weather versus climate",
            "आजको तापक्रम, वर्षा र हावाको अवस्था मौसम हो। लामो समयको औसत र प्रवृत्तिको अध्ययन जलवायु हो। एउटै दिनको मौसमले जलवायु निर्धारण गर्दैन।",
            "Weather describes short-term conditions; climate describes patterns over long periods. One unusual day alone does not define climate.","Basic earth science");
        add(a,"science","पहिरो किन जान्छ?","Why landslides happen",
            "भीषण वर्षा, भूकम्प, कमजोर भिरालो भूगर्भ, नदीले जमिन कटान र असुरक्षित निर्माणले पहिरोको जोखिम बढाउन सक्छ। एउटा satellite layer ले मात्र सटीक भविष्यवाणी गर्न सक्दैन।",
            "Intense rain, earthquakes, steep unstable slopes, erosion and construction can contribute to landslides. A satellite layer alone cannot predict exact events.","Landslide science");
        add(a,"science","विद्युत् र पानी","Electricity and floodwater",
            "बाढीले डुबेको बिजुली उपकरण वा तार नछुनुहोस्। सुरक्षित दूरीबाट विद्युत् सेवा/स्थानीय निकायलाई खबर गर्नुहोस्। पानी सुकेपछि पनि जाँचबिना उपकरण नचलाउनुहोस्।",
            "Avoid electrical equipment and wires touched by floodwater. Contact qualified responders; do not reuse affected equipment without inspection.","Electrical safety basics");
        add(a,"science","डेटा र अनिश्चितता","Data and uncertainty",
            "नापिएको जलस्तर, मोडेल अनुमान र समाचार तीन फरक प्रकारका प्रमाण हुन्। राम्रो निष्कर्षका लागि समय, ठाउँ, विधि र अनिश्चितता हेर्नु आवश्यक छ।",
            "Measurements, forecasts and news reports are different forms of evidence. Check timestamps, location, methods and uncertainty.","Scientific reasoning");

        add(a,"life","पढाइको सक्रिय सम्झना विधि","Active recall for studying",
            "पुस्तक पढेपछि बन्द गरेर आफूले बुझेको कुरा कागजमा लेख्नुहोस्। केही दिनको अन्तरमा फेरि सम्झने अभ्यास गर्नुहोस्; केवल दोहोर्‍याएर पढ्नुभन्दा उपयोगी हुन्छ।",
            "After reading, close the book and try to recall ideas without looking. Review after spaced intervals instead of only rereading.","Learning science: retrieval practice");
        add(a,"life","समस्या साना चरणमा बाँड्ने","Break problems into steps",
            "ठूलो कामलाई आज, यो हप्ता र पछि गर्ने भागमा बाँड्नुहोस्। स्पष्ट पहिलो कदम छान्दा काम सुरु गर्न सजिलो हुन्छ।",
            "Split a large task into today's step, this week's work and later goals. A clear next action can make a task manageable.","Practical study and work skills");
        add(a,"life","निर्णय गर्दा प्रमाण र विकल्प","Make thoughtful decisions",
            "कुनै निर्णयमा लक्ष्य, उपलब्ध विकल्प, लागत, जोखिम र अनुमान छुट्टाछुट्टै लेख्नुहोस्। सम्भव भए भरोसायोग्य व्यक्तिसँग छलफल गर्नुहोस्।",
            "Write down the goal, options, costs, risks and assumptions. Seek a trusted perspective before a high-impact decision.","Critical thinking");
        add(a,"life","मन शान्त राख्ने सामान्य अभ्यास","A simple calming routine",
            "केही समय फोनबाट टाढा बस्ने, बिस्तारै सास फेर्ने, हिँड्ने र नियमित सुत्ने बानीले धेरैलाई सहयोग गर्न सक्छ। स्वास्थ्य समस्या भए विशेषज्ञसँग कुरा गर्नुहोस्।",
            "A short screen break, gentle breathing, walking and regular sleep may help wellbeing. Seek professional help for health concerns.","General wellbeing education");
        add(a,"life","बचत र खर्चको आधार","Everyday budgeting",
            "आम्दानी, आवश्यक खर्च, ऋण र बचत छुट्टाछुट्टै टिपोट गर्नुहोस्। आकस्मिक खर्चका लागि सम्भव भएसम्म सानो रकम पनि नियमित छुट्याउनुहोस्।",
            "Track income, essentials, debt and savings separately. Where feasible, build a small emergency buffer.","General financial literacy");

        add(a,"digital","पासवर्ड र दुई-चरण सुरक्षा","Passwords and two-factor security",
            "हरेक महत्त्वपूर्ण खातामा फरक लामो पासवर्ड राख्नुहोस्। उपलब्ध भए दुई-चरण प्रमाणीकरण सक्रिय गर्नुहोस्। OTP कसैलाई नदिनुहोस्।",
            "Use distinct strong passwords, enable two-factor authentication where possible and never share one-time codes.","Digital safety");
        add(a,"digital","फिसिङ सन्देश चिन्नुहोस्","Recognise phishing",
            "अकस्मात् password, OTP वा पैसा माग्ने लिंक खोल्नुअघि आधिकारिक वेबसाइट वा फोनमार्फत छुट्टै पुष्टि गर्नुहोस्। डर/लोभ देखाउने सन्देशमा हतार नगर्नुहोस्।",
            "Independently verify messages demanding passwords, OTPs or money. Urgency and fear are common phishing tactics.","Cybersecurity basics");
        add(a,"digital","AI को जवाफ सधैँ सही हुँदैन","Check AI-generated answers",
            "AI ले विश्वसनीय जस्तो तर गलत जानकारी पनि दिन सक्छ। बाढी चेतावनी, औषधि र कानुनी विषयमा आधिकारिक स्रोत प्राथमिक राख्नुहोस्।",
            "AI can sound confident while being wrong. For emergency, medical or legal decisions, check authoritative sources.","AI literacy");
        add(a,"digital","अफलाइन र लाइभ डेटा","Offline versus live information",
            "एपमा पुरानो डेटा सुरक्षित रहन सक्छ तर त्यसलाई real-time भन्न मिल्दैन। अन्तिम मापन समय, नेटवर्क अवस्था र स्रोत हेरेर निर्णय लिनुहोस्।",
            "Cached information may remain visible offline but is not necessarily live. Inspect update time and source before acting.","Digital data literacy");

        add(a,"books","पढेको कुरा व्यवहारमा उतार्ने","Turn reading into action",
            "कुनै पुस्तकबाट एउटै उपयोगी विचार छानेर एक हप्ता अभ्यास गर्नुहोस्। मन परेको वाक्य मात्र होइन, व्यवहारमा आएको परिवर्तन पनि टिपोट गर्नुहोस्।",
            "Choose one practical idea from a book and try it for a week. Notice behavioural changes, not just memorable quotations.","Reading and reflection");
        add(a,"books","प्रश्न सोधेर पढ्ने","Read with questions",
            "अध्याय सुरु गर्दा 'मुख्य प्रश्न के हो?' र सकिँदा 'लेखकले के प्रमाण दिएको छ?' सोध्नुहोस्। यसले बुझाइ बढाउँछ।",
            "Ask what question a chapter answers and what evidence supports the author's point. This builds deeper reading.","Critical reading");
        add(a,"books","कथा र तथ्य छुट्याउने","Distinguish stories and facts",
            "उपन्यासले पात्र र अनुभवमार्फत जीवन बुझाउन सक्छ, तर त्यसका घटना वैज्ञानिक प्रमाण हुँदैनन्। विषयअनुसार साहित्य र तथ्यात्मक स्रोतको भूमिका फरक हुन्छ।",
            "Stories can teach perspective, but fictional events are not scientific evidence. Match source types to the question.","Literary and information literacy");
        add(a,"books","विनम्रता र निरन्तर सिकाइ","Stay curious and humble",
            "नजानेको कुरा स्वीकार्नु कमजोरी होइन। भरपर्दो स्रोत खोज्ने, प्रश्न गर्ने र नयाँ प्रमाणले विचार सुधार्ने बानीले ज्ञान बढ्छ।",
            "Admitting uncertainty, asking questions and updating beliefs with evidence are signs of good learning.","Learning and critical thinking");
        ITEMS=Collections.unmodifiableList(a);
    }
    private static void add(List<Entry>a,String c,String nt,String et,String nb,String eb,String s){a.add(new Entry(c,nt,et,nb,eb,s));}
    static String categoryName(String c,boolean en){
        switch(c){
            case "gita":return en?"Bhagavad Gita":"भगवद्गीताको जीवन ज्ञान";
            case "flood":return en?"Flood safety":"बाढी तथा विपद् सुरक्षा";
            case "general":return en?"General knowledge":"सामान्य ज्ञान";
            case "science":return en?"Science and geography":"विज्ञान र भूगोल";
            case "life":return en?"Study and life skills":"पढाइ र जीवन सीप";
            case "digital":return en?"Digital literacy":"डिजिटल ज्ञान";
            case "books":return en?"Books and reflection":"पुस्तक र चिन्तन";
            default:return en?"All topics":"सबै ज्ञान";
        }
    }
    static boolean isKnowledgeQuestion(String q){
        if(q==null)return false;
        String x=q.toLowerCase(Locale.ROOT);
        return has(x,"ज्ञान","gyan","gyaan","gita","गीता","कृष्ण","krishna","karma","कर्म","जीवन","जिन्दगी","life advice","motivation","study","पढाइ","पुस्तक","book","सामान्य ज्ञान","general knowledge","science","विज्ञान","पासवर्ड","password","phishing","फिसिङ","water cycle","जलचक्र","बाढीमा के","flood safety","बाढी सुरक्षा","आपतकालीन तयारी","कसरी जोगिने","सुरक्षा उपाय");
    }
    static String answer(String question,boolean en){return answerWithOffset(question,en,0);}
    static String answerWithOffset(String question,boolean en,int offset){
        if(question==null)return "";
        String q=question.toLowerCase(Locale.ROOT);
        Entry chosen=null;
        for(Entry e:ITEMS){
            if(q.contains(e.neTitle.toLowerCase(Locale.ROOT))||q.contains(e.enTitle.toLowerCase(Locale.ROOT))){chosen=e;break;}
        }
        if(chosen==null){
            String category=has(q,"gita","geeta","गीता","कृष्ण","krishna","कर्म")?"gita":
                has(q,"बाढी","flood","आपतकालीन तयारी","कसरी जोगिने")?"flood":
                has(q,"study","पढाइ")?"life":
                has(q,"पासवर्ड","password","phishing","फिसिङ")?"digital":
                has(q,"science","विज्ञान","जलचक्र","water cycle")?"science":
                has(q,"पुस्तक","book")?"books":
                has(q,"ज्ञान","gyan","gyaan","general knowledge","सामान्य ज्ञान")?"general":"life";
            java.util.ArrayList<Entry> lessons=new java.util.ArrayList<>();
            for(Entry e:ITEMS)if(category.equals(e.category))lessons.add(e);
            if(!lessons.isEmpty())chosen=lessons.get(Math.floorMod(offset,lessons.size()));
        }
        if(chosen==null)return en?"No curated lesson found.":"उपयुक्त पाठ भेटिएन।";
        return "📚 "+chosen.title(en)+"\n"+chosen.body(en)+"\n"+(en?"Reference: ":"सन्दर्भ: ")+chosen.source;
    }
    private static boolean has(String q,String...terms){for(String t:terms)if(q.contains(t))return true;return false;}
}
