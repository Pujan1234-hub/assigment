from pathlib import Path

APP = Path('floodsafe-android-app/app/src/main/java/io/github/pujan1234hub/floodsafe/app')

# ONLY SATHI UI + answer-audio behavior. Do not touch river/map/data/weather/alerts/navigation.
native = APP / 'NativeFullActivity.java'
s = native.read_text(encoding='utf-8')

old = 'Button sathi=button("🤖 SATHI");sathi.setTextSize(13);sathi.setOnClickListener(v->showSathiDialog(null));FrameLayout.LayoutParams fp=new FrameLayout.LayoutParams(dp(104),dp(48),Gravity.END|Gravity.BOTTOM);fp.setMargins(0,0,dp(18),dp(82));root.addView(sathi,fp);'
new = '''Button sathi=button("✦  SATHI AI");
        sathi.setTextSize(12.5f);
        sathi.setTextColor(Color.WHITE);
        sathi.setTypeface(Typeface.create("sans-serif-medium",Typeface.BOLD));
        sathi.setGravity(Gravity.CENTER);
        sathi.setPadding(dp(14),0,dp(14),0);
        sathi.setMinWidth(0);sathi.setMinHeight(0);
        GradientDrawable sathiBg=new GradientDrawable(GradientDrawable.Orientation.LEFT_RIGHT,new int[]{Color.rgb(24,73,146),Color.rgb(26,144,181)});
        sathiBg.setCornerRadius(dp(25));
        sathiBg.setStroke(dp(1),Color.argb(110,255,255,255));
        sathi.setBackground(sathiBg);
        sathi.setElevation(dp(10));
        sathi.setOnClickListener(v->showSathiDialog(null));
        FrameLayout.LayoutParams fp=new FrameLayout.LayoutParams(dp(126),dp(50),Gravity.END|Gravity.BOTTOM);fp.setMargins(0,0,dp(18),dp(82));root.addView(sathi,fp);'''
if old not in s:
    raise SystemExit('SATHI floating button anchor not found')
s = s.replace(old, new, 1)

# Remove the robot-looking title from the fallback/base SATHI dialog too.
s = s.replace('.setTitle("🤖 SATHI")', '.setTitle("✦ SATHI AI")')

native.write_text(s, encoding='utf-8')

nextlevel = APP / 'SathiNextLevelV0918.java'
t = nextlevel.read_text(encoding='utf-8')

# Keep voice INPUT available, but answers are text-only: do not invoke TTS after an answer.
if 'speak(result);' not in t:
    raise SystemExit('SATHI spoken-answer anchor not found')
t = t.replace('speak(result);', '/* text-only SATHI reply: spoken answer disabled by user request */', 1)

# Premium/non-robot SATHI dialog title only; knowledge/data logic remains unchanged.
t = t.replace('setTitle("🤖 SATHI AI • live app data")', 'setTitle("✦ SATHI AI • live app data")', 1)

nextlevel.write_text(t, encoding='utf-8')

# Hard guards so this patch cannot silently drift into unrelated app areas.
check_native = native.read_text(encoding='utf-8')
check_sathi = nextlevel.read_text(encoding='utf-8')
if '✦  SATHI AI' not in check_native or 'GradientDrawable.Orientation.LEFT_RIGHT' not in check_native:
    raise SystemExit('premium SATHI floating UI missing')
if 'spoken answer disabled by user request' not in check_sathi:
    raise SystemExit('text-only SATHI answer guard missing')
print('V0918_SATHI_VISUAL_TEXT_ONLY_OK')
