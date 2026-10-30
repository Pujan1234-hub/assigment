package io.github.pujan1234hub.floodsafe.app;

import android.app.Dialog;
import android.content.Context;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.view.Gravity;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import java.time.Instant;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.Locale;

/** Fast, custom native bottom-sheet that uses already loaded station values (no network wait). */
final class StationDetailSheet {
    private StationDetailSheet(){}
    static void show(Context context,String name,String stage,double level,
                     boolean fresh,long observedAt,String details,boolean english,boolean riverSegment){
        show(context,name,stage,level,fresh,observedAt,details,english,riverSegment,Double.NaN,Double.NaN);
    }

    /** Only supplied DHM/BIPAD gauge thresholds are displayed. Unknown limits stay unavailable. */
    static void show(Context context,String name,String stage,double level,
                     boolean fresh,long observedAt,String details,boolean english,boolean riverSegment,
                     double warningLevel,double dangerLevel){
        if(context==null)return;
        final int ink=Color.rgb(28,49,72),muted=Color.rgb(95,111,126),gold=Color.rgb(176,126,54);
        final int pad=dp(context,18);
        String status=normalized(stage,fresh);
        int accent="danger".equals(status)?Color.rgb(225,53,76):
                   "warning".equals(status)?Color.rgb(236,118,35):
                   "alert".equals(status)?Color.rgb(225,171,32):
                   "normal".equals(status)?Color.rgb(46,140,218):
                   Color.rgb(125,144,160);

        Dialog dialog=new Dialog(context);
        ScrollView scroll=new ScrollView(context);
        scroll.setFillViewport(false);
        scroll.setVerticalScrollBarEnabled(false);
        LinearLayout panel=new LinearLayout(context);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setPadding(pad,dp(context,12),pad,dp(context,23));
        panel.setBackground(bg(context,Color.rgb(255,250,241),Color.rgb(226,202,165),25));
        scroll.addView(panel,new ScrollView.LayoutParams(-1,-2));

        View grab=new View(context);
        grab.setBackground(bg(context,Color.rgb(208,194,174),Color.TRANSPARENT,6));
        LinearLayout.LayoutParams handle=new LinearLayout.LayoutParams(dp(context,44),dp(context,5));
        handle.gravity=Gravity.CENTER_HORIZONTAL;handle.bottomMargin=dp(context,18);
        panel.addView(grab,handle);

        TextView eyebrow=text(context,riverSegment?
            (english?"🗺️  RIVER SEGMENT":"🗺️  नदी खण्ड"):
            (english?"🇳🇵  OFFICIAL RIVER GAUGE":"🇳🇵  आधिकारिक नदी स्टेशन"),12,true,gold);
        panel.addView(eyebrow);
        TextView heading=text(context,name==null||name.isEmpty()?
            (english?"River station":"नदी स्टेशन"):name,22,true,ink);
        panel.addView(heading,params(context,0,6,0,14));

        TextView badge=text(context,"● "+statusText(status,english),13,true,accent);
        badge.setBackground(bg(context,Color.rgb(255,255,255),accent,14));
        badge.setPadding(dp(context,13),dp(context,8),dp(context,13),dp(context,8));
        LinearLayout.LayoutParams badgeP=new LinearLayout.LayoutParams(-2,-2);
        badgeP.bottomMargin=dp(context,12);panel.addView(badge,badgeP);

        LinearLayout metric=new LinearLayout(context);
        metric.setOrientation(LinearLayout.VERTICAL);
        metric.setPadding(dp(context,15),dp(context,14),dp(context,15),dp(context,13));
        metric.setBackground(bg(context,Color.WHITE,Color.rgb(218,226,235),19));
        panel.addView(metric,params(context,0,0,0,14));
        boolean measured=Double.isFinite(level) && fresh;
        // Only for an official gauge: an old VERIFIED reading remains useful
        // as history, but must never be displayed as the current river level.
        boolean historical=!riverSegment&&!fresh&&Double.isFinite(level)&&observedAt>0;
        metric.addView(text(context,historical?
                (english?"LAST VERIFIED WATER LEVEL · NOT LIVE":"अन्तिम प्रमाणित पानीको सतह · हालको होइन"):
                (english?"WATER LEVEL · DHM/BIPAD":"पानीको सतह · DHM/BIPAD"),11,true,muted));
        metric.addView(text(context,(measured||historical)?String.format(Locale.US,"%.2f m",level):
            (english?"—  Not current":"—  ताजा मापन छैन"),(measured||historical)?31:22,true,ink),params(context,0,4,0,0));
        String when=humanTime(observedAt,english);
        metric.addView(text(context,(historical?(english?"⏱ Last observed: ":"⏱ अन्तिम मापन: "):
            (english?"⏱ Observed: ":"⏱ मापन: "))+when,12,false,muted),params(context,0,9,0,0));
        if(historical)
            metric.addView(text(context,english?
                "⚪ Old measurement (30+ minutes) · Not live · Waiting for a new official reading.":
                "⚪ पुरानो मापन (३० मिनेटभन्दा पुरानो) · हालको अवस्था होइन · नयाँ आधिकारिक मापनको प्रतीक्षामा।",
                12,true,muted),params(context,0,8,0,0));

        if(!riverSegment){
            // Two compact fields right below the existing current-water-level card.
            // 0/negative/NaN from official source are missing, not actual warning levels.
            double warn=validThreshold(warningLevel),danger=validThreshold(dangerLevel);
            LinearLayout thresholds=new LinearLayout(context);
            thresholds.setOrientation(LinearLayout.HORIZONTAL);
            LinearLayout warnBox=thresholdCard(context,
                english?"🟠 WARNING LEVEL":"🟠 चेतावनी तह",warn,Color.rgb(222,135,61),ink,muted);
            LinearLayout dangerBox=thresholdCard(context,
                english?"🔴 DANGER LEVEL":"🔴 खतरा तह",danger,Color.rgb(213,72,83),ink,muted);
            LinearLayout.LayoutParams warningParams=new LinearLayout.LayoutParams(0,-2,1f);
            warningParams.setMargins(0,0,dp(context,5),0);
            LinearLayout.LayoutParams dangerParams=new LinearLayout.LayoutParams(0,-2,1f);
            dangerParams.setMargins(dp(context,5),0,0,0);
            thresholds.addView(warnBox,warningParams);
            thresholds.addView(dangerBox,dangerParams);
            panel.addView(thresholds,params(context,0,0,0,12));

            if(measured && (Double.isFinite(warn)||Double.isFinite(danger))){
                // Exact difference only for this SAME official gauge; no model or borrowed threshold.
                boolean overDanger=Double.isFinite(danger)&&level>=danger;
                double target=overDanger?danger:Double.isFinite(warn)?warn:danger;
                String which=overDanger?(english?"danger":"खतरा"):(Double.isFinite(warn)?(english?"warning":"चेतावनी"):(english?"danger":"खतरा"));
                double gap=Math.abs(target-level);
                String comparison=String.format(Locale.US,"%.2f m",gap)+" "+
                    (english?(level>=target?"above ":"below "):(level>=target?"माथि · ":"तल · "))+which;
                TextView delta=text(context,(english?"📏 ":"📏 ")+comparison,12,true,
                    level>=target?Color.rgb(202,67,69):Color.rgb(56,103,134));
                panel.addView(delta,params(context,0,0,0,12));
            } else if(!Double.isFinite(warn)&&!Double.isFinite(danger)){
                panel.addView(text(context,
                    english?"Official warning/danger thresholds are unavailable for this station.":
                    "यस स्टेशनको आधिकारिक चेतावनी/खतरा सीमा उपलब्ध छैन।",11,false,muted),
                    params(context,0,0,0,12));
            }
        }

        if(details!=null&&!details.trim().isEmpty()){
            LinearLayout note=new LinearLayout(context);note.setOrientation(LinearLayout.VERTICAL);
            note.setPadding(dp(context,14),dp(context,13),dp(context,14),dp(context,13));
            note.setBackground(bg(context,Color.rgb(245,251,255),Color.rgb(208,230,241),18));
            note.addView(text(context,details,13,false,ink));
            panel.addView(note,params(context,0,0,0,14));
        }
        panel.addView(text(context,english?
             "Source: DHM / BIPAD · A nearby gauge is not a reading at every river segment. Check observation time and official warning thresholds.":
             "स्रोत: DHM / BIPAD · नजिकको स्टेशनको मापन सबै नदीको सीधा मापन होइन। समय र आधिकारिक चेतावनी सीमा जाँच्नुहोस्।",11,false,muted),params(context,0,0,0,12));

        Button done=new Button(context);
        done.setText(english?"Back to map":"नक्सामा फर्कनुहोस्");
        done.setAllCaps(false);done.setTextSize(15);done.setTextColor(Color.WHITE);
        done.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
        done.setBackground(bg(context,Color.rgb(41,93,127),Color.rgb(41,93,127),17));
        done.setOnClickListener(v->dialog.dismiss());
        panel.addView(done,new LinearLayout.LayoutParams(-1,dp(context,52)));

        dialog.setContentView(scroll);
        Window w=dialog.getWindow();
        if(w!=null){
            w.setBackgroundDrawableResource(android.R.color.transparent);
            w.addFlags(WindowManager.LayoutParams.FLAG_DIM_BEHIND);
            WindowManager.LayoutParams p=w.getAttributes();p.dimAmount=.53f;w.setAttributes(p);
        }
        dialog.show();
        w=dialog.getWindow();
        if(w!=null){w.setGravity(Gravity.BOTTOM);w.setLayout(-1,-2);w.setBackgroundDrawableResource(android.R.color.transparent);}
        // Keep text accessible on short mobile windows and foldable displays.
        scroll.setLayoutParams(new android.widget.FrameLayout.LayoutParams(-1,
            Math.min(dp(context,650),(int)(context.getResources().getDisplayMetrics().heightPixels*.78f))));
    }
    private static double validThreshold(double x){
        return Double.isFinite(x)&&x>0d?x:Double.NaN;
    }
    private static LinearLayout thresholdCard(Context c,String title,double threshold,
                                              int accent,int ink,int muted){
        LinearLayout card=new LinearLayout(c);card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(c,11),dp(c,11),dp(c,9),dp(c,11));
        card.setBackground(bg(c,Color.WHITE,accent,15));
        card.addView(text(c,title,10,true,accent));
        String value=Double.isFinite(threshold)?String.format(Locale.US,"%.2f m",threshold):"—";
        card.addView(text(c,value,Double.isFinite(threshold)?19:16,true,
            Double.isFinite(threshold)?ink:muted),params(c,0,5,0,0));
        return card;
    }
    private static String humanTime(long ms,boolean en){
        if(ms<=0)return en?"Time unavailable":"मापन समय उपलब्ध छैन";
        try{
            return Instant.ofEpochMilli(ms).atZone(ZoneId.of("Asia/Kathmandu"))
                .format(DateTimeFormatter.ofPattern(en?"d MMM yyyy, h:mm a":"yyyy-MM-dd, h:mm a",Locale.ENGLISH))
                +" NPT";
        }catch(Exception e){return "—";}
    }
    private static String normalized(String stage,boolean fresh){
        if(!fresh)return "stale";
        String s=stage==null?"":stage.toLowerCase(Locale.ROOT);
        if(s.contains("danger")||s.contains("red"))return "danger";
        if(s.contains("warning")||s.contains("orange"))return "warning";
        if(s.contains("alert")||s.contains("watch")||s.contains("yellow"))return "alert";
        if(s.contains("normal")||s.contains("blue"))return "normal";
        return "stale";
    }
    private static String statusText(String stage,boolean en){
        switch(stage){
            case "danger":return en?"DANGER":"खतरा";
            case "warning":return en?"WARNING":"चेतावनी";
            case "alert":return en?"WATCH / ALERT":"निगरानी";
            case "normal":return en?"NORMAL":"सामान्य";
            default:return en?"OLD / UNVERIFIED":"पुरानो / अपुष्ट";
        }
    }
    private static TextView text(Context c,String value,int size,boolean bold,int color){
        TextView v=new TextView(c);v.setText(value);v.setTextSize(size);v.setTextColor(color);
        v.setLineSpacing(dp(c,2),1.08f);if(bold)v.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
        return v;
    }
    private static LinearLayout.LayoutParams params(Context c,int l,int t,int r,int b){
        LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,-2);
        p.setMargins(dp(c,l),dp(c,t),dp(c,r),dp(c,b));return p;
    }
    private static GradientDrawable bg(Context c,int fill,int stroke,int radius){
        GradientDrawable d=new GradientDrawable();d.setColor(fill);d.setCornerRadius(dp(c,radius));
        if(stroke!=Color.TRANSPARENT)d.setStroke(dp(c,1),stroke);return d;
    }
    private static int dp(Context c,int value){return Math.round(value*c.getResources().getDisplayMetrics().density);}
}
