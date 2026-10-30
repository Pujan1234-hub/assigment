package io.github.pujan1234hub.floodsafe.app;

import android.app.Activity;
import android.os.Bundle;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.Gravity;
import android.view.View;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.Spinner;
import android.widget.TextView;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/** A small, fully offline and searchable knowledge library. No remote AI or fabricated quotes. */
public final class GyanActivity extends Activity {
    private boolean english;
    private LinearLayout results;
    private EditText search;
    private Spinner category;
    private TextView counter;
    private Button more;
    private String categoryKey="";
    private int limit=8;
    private final String[] keys={"","gita","flood","general","science","life","digital","books"};

    @Override public void onCreate(Bundle b){
        super.onCreate(b);
        english=getSharedPreferences("floodsafe-native-full",MODE_PRIVATE).getBoolean("lang_en",false);
        getWindow().setStatusBarColor(Color.rgb(255,248,231));
        getWindow().setNavigationBarColor(Color.rgb(255,251,242));
        getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR|View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR);
        ScrollView scroll=new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(Color.rgb(255,250,240));
        LinearLayout page=new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        page.setPadding(dp(18),dp(18),dp(18),dp(36));
        scroll.addView(page);
        SafeInsets.apply(scroll);
        setContentView(scroll);

        Button back=button(english?"← Back":"← फर्कनुहोस्");
        back.setOnClickListener(v->finish());
        page.addView(back,margin(0,0,0,12));

        TextView heading=text(english?"📚 Knowledge for Life":"📚 ज्ञानका कुरा",26,true,Color.rgb(47,61,80));
        page.addView(heading);
        TextView lead=text(english?"Bhagavad Gita • Flood safety • General knowledge • Science • Books • Study • Digital safety"
            :"भगवद्गीता • बाढी सुरक्षा • सामान्य ज्ञान • विज्ञान • पुस्तक • पढाइ • डिजिटल सुरक्षा",14,false,Color.rgb(112,89,63));
        page.addView(lead,margin(0,8,0,18));
        TextView note=text(english?"Gita lessons are practical interpretations. Flood guidance is educational, not an official live warning."
            :"गीता सम्बन्धी पाठ जीवनोपयोगी भावार्थ हुन्। बाढीसम्बन्धी पाठ शैक्षिक हुन्; सरकारी live चेतावनी होइनन्।",12,false,Color.rgb(136,106,72));
        page.addView(note,margin(0,0,0,16));

        search=new EditText(this);
        search.setSingleLine(true);
        search.setTextSize(15);
        search.setPadding(dp(14),0,dp(14),0);
        search.setHint(english?"🔎 Search knowledge or keywords":"🔎 ज्ञानका विषय वा शब्द खोज्नुहोस्");
        search.setBackground(background(Color.WHITE,Color.rgb(220,195,143),16));
        page.addView(search,marginHeight(dp(52),0,0,0,12));

        category=new Spinner(this);
        ArrayList<String> cats=new ArrayList<>();
        for(String key:keys)cats.add(GyanKnowledge.categoryName(key,english));
        ArrayAdapter<String> adapter=new ArrayAdapter<>(this,android.R.layout.simple_spinner_dropdown_item,cats);
        category.setAdapter(adapter);
        page.addView(category,marginHeight(dp(52),0,0,0,8));
        category.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener(){
            public void onItemSelected(AdapterView<?> parent,View v,int position,long id){
                categoryKey=keys[position];limit=8;render();
            }
            public void onNothingSelected(AdapterView<?> parent){}
        });

        counter=text("",12,true,Color.rgb(104,86,60));
        page.addView(counter,margin(0,8,0,10));
        results=new LinearLayout(this);
        results.setOrientation(LinearLayout.VERTICAL);
        page.addView(results);

        more=button(english?"Show more lessons ↓":"थप पाठ हेर्नुहोस् ↓");
        more.setOnClickListener(v->{limit+=8;render();});
        page.addView(more,margin(0,6,0,16));

        search.addTextChangedListener(new TextWatcher(){
            public void beforeTextChanged(CharSequence s,int st,int count,int after){}
            public void onTextChanged(CharSequence s,int st,int before,int count){limit=8;render();}
            public void afterTextChanged(Editable e){}
        });
        render();
    }
    private void render(){
        if(results==null)return;
        String query=search==null?"":search.getText().toString().trim().toLowerCase(Locale.ROOT);
        List<GyanKnowledge.Entry> filtered=new ArrayList<>();
        for(GyanKnowledge.Entry e:GyanKnowledge.ITEMS){
            if(!categoryKey.isEmpty()&&!categoryKey.equals(e.category))continue;
            String haystack=(e.neTitle+" "+e.enTitle+" "+e.neBody+" "+e.enBody+" "+e.category+" "+e.source).toLowerCase(Locale.ROOT);
            if(!query.isEmpty()&&!haystack.contains(query))continue;
            filtered.add(e);
        }
        results.removeAllViews();
        int count=Math.min(limit,filtered.size());
        for(int i=0;i<count;i++){
            GyanKnowledge.Entry e=filtered.get(i);
            LinearLayout c=new LinearLayout(this);
            c.setOrientation(LinearLayout.VERTICAL);
            c.setPadding(dp(16),dp(14),dp(16),dp(14));
            c.setBackground(background(Color.WHITE,Color.rgb(226,214,190),20));
            c.setElevation(dp(1));
            TextView categoryLabel=text(GyanKnowledge.categoryName(e.category,english),11,true,Color.rgb(163,113,46));
            c.addView(categoryLabel);
            c.addView(text(e.title(english),17,true,Color.rgb(43,59,80)),margin(0,6,0,8));
            c.addView(text(e.body(english),14,false,Color.rgb(62,75,88)));
            c.addView(text((english?"Reference: ":"सन्दर्भ: ")+e.source,11,false,Color.rgb(126,114,101)),margin(0,12,0,0));
            results.addView(c,margin(0,0,0,12));
        }
        if(filtered.isEmpty())results.addView(text(english?"No lesson found. Try another word or category.":"यो शब्दमा पाठ भेटिएन। अर्को शब्द वा विषय खोज्नुहोस्।",13,false,Color.rgb(94,107,122)));
        counter.setText(english?filtered.size()+" lessons found":filtered.size()+" वटा पाठ भेटिए");
        more.setVisibility(filtered.size()>limit?View.VISIBLE:View.GONE);
    }
    private Button button(String title){
        Button b=new Button(this);
        b.setAllCaps(false);b.setText(title);b.setTextSize(14);b.setTypeface(Typeface.DEFAULT_BOLD);
        b.setTextColor(Color.rgb(66,52,37));b.setBackground(background(Color.rgb(255,247,227),Color.rgb(225,195,134),16));
        return b;
    }
    private TextView text(String value,int size,boolean bold,int color){
        TextView v=new TextView(this);v.setText(value);v.setTextSize(size);v.setTextColor(color);
        v.setLineSpacing(dp(2),1.1f);v.setGravity(Gravity.START);
        if(bold)v.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
        return v;
    }
    private GradientDrawable background(int bg,int border,int radius){
        GradientDrawable g=new GradientDrawable();g.setColor(bg);g.setCornerRadius(dp(radius));g.setStroke(dp(1),border);return g;
    }
    private LinearLayout.LayoutParams margin(int left,int top,int right,int bottom){
        LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,-2);
        p.setMargins(dp(left),dp(top),dp(right),dp(bottom));return p;
    }
    private LinearLayout.LayoutParams marginHeight(int height,int left,int top,int right,int bottom){
        LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,height);
        p.setMargins(dp(left),dp(top),dp(right),dp(bottom));return p;
    }
    private int dp(int x){return Math.round(x*getResources().getDisplayMetrics().density);}
}
