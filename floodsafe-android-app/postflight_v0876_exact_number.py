from pathlib import Path

root=Path(__file__).resolve().parent
p=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java'
s=p.read_text(encoding='utf-8')

pairs=[
('b.append(String.format(Locale.US,"\\n\\n%s%.6f m",t("पानीको सतह: ","Water level: "),s.level));',
 'b.append("\\n\\n").append(t("पानीको सतह: ","Water level: ")).append(v872ExactNumber(s.level)).append(" m"); // V0876_EXACT_SOURCE_LEVEL'),
('if(Double.isFinite(discharge))b.append(String.format(Locale.US,"\\n%s%.6f",t("Discharge / streamflow: ","Discharge / streamflow: "),discharge));',
 'if(Double.isFinite(discharge))b.append("\\n").append(t("Discharge / streamflow: ","Discharge / streamflow: ")).append(v872ExactNumber(discharge)).append(" m³/s");'),
('if(Double.isFinite(s.warning))b.append(String.format(Locale.US,"\\n%s%.6f m",t("चेतावनी तह: ","Warning level: "),s.warning));',
 'if(Double.isFinite(s.warning))b.append("\\n").append(t("चेतावनी तह: ","Warning level: ")).append(v872ExactNumber(s.warning)).append(" m");'),
('if(Double.isFinite(s.danger))b.append(String.format(Locale.US,"\\n%s%.6f m",t("खतरा तह: ","Danger level: "),s.danger));',
 'if(Double.isFinite(s.danger))b.append("\\n").append(t("खतरा तह: ","Danger level: ")).append(v872ExactNumber(s.danger)).append(" m");'),
]
for old,new in pairs:
    if old in s:s=s.replace(old,new,1)

if 'V0876_EXACT_SOURCE_LEVEL' not in s:raise SystemExit('v0876 exact number level anchor missing')
if 'v872ExactNumber(s.warning)' not in s or 'v872ExactNumber(s.danger)' not in s:raise SystemExit('v0876 exact threshold output missing')
p.write_text(s,encoding='utf-8')
print('FloodSafe v0.8.76 exact official numeric precision PASS')
