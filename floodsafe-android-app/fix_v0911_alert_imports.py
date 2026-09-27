from pathlib import Path
p=Path('floodsafe-android-app/app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodLiveGaugeMonitor.java')
s=p.read_text(encoding='utf-8')
if 'import java.util.ArrayList;' not in s:
    s=s.replace('import java.util.Locale;\n','import java.util.Locale;\nimport java.util.ArrayList;\nimport java.util.List;\n',1)
elif 'import java.util.List;' not in s:
    s=s.replace('import java.util.ArrayList;\n','import java.util.ArrayList;\nimport java.util.List;\n',1)
if 'import java.util.List;' not in s or 'import java.util.ArrayList;' not in s: raise SystemExit('alert collection imports missing')
p.write_text(s,encoding='utf-8')
print('V0911_ALERT_IMPORTS_OK')
