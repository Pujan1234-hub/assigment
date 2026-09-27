from pathlib import Path
import re

JAVA = Path("floodsafe-android-app/app/src/main/java/io/github/pujan1234hub/floodsafe/app")
UI = JAVA / "NativeFullActivity.java"
FAST = JAVA / "FloodLiveGaugeMonitor.java"
FALLBACK = JAVA / "RiverAlertWorker.java"
GRADLE = Path("floodsafe-android-app/app/build.gradle")

ui = UI.read_text(encoding="utf-8")
fast = FAST.read_text(encoding="utf-8")
fallback = FALLBACK.read_text(encoding="utf-8")
g = GRADLE.read_text(encoding="utf-8")

# Ninda-style data can contain an impossible pair such as warning=125.00 and danger=122.50.
# Never invent/swap thresholds. Official BIPAD status wins; numeric threshold fallback is
# allowed only when warning/danger ordering is structurally sane.

# --- UI status + station dialog ------------------------------------------------
old_status = r'''    private String stationDialogStatus(RiverStation s){
        boolean aboveDanger=Double.isFinite(s.level)&&Double.isFinite(s.danger)&&s.danger>0d&&s.level>=s.danger;
        boolean aboveWarning=Double.isFinite(s.level)&&Double.isFinite(s.warning)&&s.warning>0d&&s.level>=s.warning;
        if(s.fresh){
            if(aboveDanger)return "🔴 "+t("खतरा","DANGER");
            if(aboveWarning)return "🟠 "+t("चेतावनी","WARNING");
            return stageDot(s.stage)+" "+stageName(s.stage);
        }
        if(aboveDanger)return "⚪ "+t("पुरानो reading • पछिल्लो मापन खतरा स्तर माथि थियो","STALE reading • last measurement was above the danger level");
        if(aboveWarning)return "⚪ "+t("पुरानो reading • पछिल्लो मापन चेतावनी स्तर माथि थियो","STALE reading • last measurement was above the warning level");
        return "⚪ "+t("ऐतिहासिक / पुरानो • अन्तिम ज्ञात reading","HISTORICAL / STALE • last known reading");
    } // V0911_NINDA_THRESHOLD_SAFE_DISPLAY
'''
new_status = r'''    private static boolean v0911ThresholdOrderInvalid(double warning,double danger){
        return Double.isFinite(warning)&&warning>0d&&Double.isFinite(danger)&&danger>0d&&danger<warning;
    } // V0911_THRESHOLD_ORDER_GUARD
    private String stationDialogStatus(RiverStation s){
        boolean sane=!v0911ThresholdOrderInvalid(s.warning,s.danger);
        boolean aboveDanger=sane&&Double.isFinite(s.level)&&Double.isFinite(s.danger)&&s.danger>0d&&s.level>=s.danger;
        boolean aboveWarning=sane&&Double.isFinite(s.level)&&Double.isFinite(s.warning)&&s.warning>0d&&s.level>=s.warning;
        if(s.fresh)return stageDot(s.stage)+" "+stageName(s.stage);
        if(aboveDanger)return "⚪ "+t("पुरानो reading • पछिल्लो मापन खतरा स्तर माथि थियो","STALE reading • last measurement was above the danger level");
        if(aboveWarning)return "⚪ "+t("पुरानो reading • पछिल्लो मापन चेतावनी स्तर माथि थियो","STALE reading • last measurement was above the warning level");
        return "⚪ "+t("ऐतिहासिक / पुरानो • अन्तिम ज्ञात reading","HISTORICAL / STALE • last known reading");
    } // V0911_NINDA_THRESHOLD_SAFE_DISPLAY
'''
if old_status not in ui:
    raise SystemExit("v0911 stationDialogStatus anchor missing")
ui = ui.replace(old_status, new_status, 1)

old_parse = 'long at=OfficialRiverData.observationTime(r);boolean fresh=OfficialRiverData.isCurrent(at,now);String stage=OfficialRiverData.stage(r,fresh);int rank=OfficialRiverData.rank(stage);'
new_parse = 'long at=OfficialRiverData.observationTime(r);boolean fresh=OfficialRiverData.isCurrent(at,now);String stage=OfficialRiverData.stage(r,fresh);if(fresh&&v0911ThresholdOrderInvalid(warning,danger)){String official=OfficialRiverData.officialStage(str(r,"status","status_name","alertStatus","alert_status","riskLevel","risk_level","_officialStatus"));if(official.isEmpty())stage="unknown";else stage=official;}int rank=OfficialRiverData.rank(stage); // V0911_INVERTED_THRESHOLDS_NOT_TRUSTED'
if old_parse not in ui:
    raise SystemExit("final parseStation status anchor missing")
ui = ui.replace(old_parse, new_parse, 1)

old_danger = 'if(Double.isFinite(s.danger))b.append(t("\\nखतरा स्तर: ","\\nDanger: ")).append(String.format(Locale.US,"%.2f m",s.danger));'
new_danger = 'if(Double.isFinite(s.danger)){if(v0911ThresholdOrderInvalid(s.warning,s.danger))b.append(t("\\nखतरा स्तर: — (official threshold क्रम असंगत)","\\nDanger: — (official thresholds inconsistent)"));else b.append(t("\\nखतरा स्तर: ","\\nDanger: ")).append(String.format(Locale.US,"%.2f m",s.danger));} // V0911_INVERTED_THRESHOLD_HIDDEN'
if old_danger not in ui:
    raise SystemExit("localized danger display anchor missing")
ui = ui.replace(old_danger, new_danger, 1)

# --- fast one-second monitor: official status first, malformed numeric pair ignored ---
old_fast_stage = 'private static String stage(double level,double warning,double danger,String raw){if(Double.isFinite(level)&&Double.isFinite(danger)&&danger>0&&level>=danger)return"danger";if((raw.contains("DANGER")||raw.contains("RED"))&&!raw.contains("BELOW DANGER"))return"danger";if(Double.isFinite(level)&&Double.isFinite(warning)&&warning>0&&level>=warning)return"warning";if((raw.contains("WARNING")||raw.contains("ORANGE"))&&!raw.contains("BELOW WARNING"))return"warning";if(raw.contains("ALERT")||raw.contains("WATCH")||raw.contains("YELLOW")||raw.contains("RISING")||raw.contains("INCREASING"))return"alert";return"normal";}'
new_fast_stage = r'''private static String stage(double level,double warning,double danger,String raw){
        String official=v0911OfficialStage(raw);if(!official.isEmpty())return official;
        boolean sane=!v0911ThresholdOrderInvalid(warning,danger);
        if(sane&&Double.isFinite(level)&&Double.isFinite(danger)&&danger>0d&&level>=danger)return"danger";
        if(sane&&Double.isFinite(level)&&Double.isFinite(warning)&&warning>0d&&level>=warning)return"warning";
        if(raw.contains("ALERT")||raw.contains("WATCH")||raw.contains("YELLOW")||raw.contains("RISING")||raw.contains("INCREASING"))return"alert";
        return"normal";
    } // V0911_FAST_OFFICIAL_STATUS_FIRST
    private static boolean v0911ThresholdOrderInvalid(double warning,double danger){return Double.isFinite(warning)&&warning>0d&&Double.isFinite(danger)&&danger>0d&&danger<warning;}
    private static String v0911OfficialStage(String raw){String s=raw==null?"":raw.trim().toUpperCase(Locale.ROOT);if(s.isEmpty())return"";if((s.contains("DANGER")||s.contains("RED"))&&!s.contains("BELOW DANGER"))return"danger";if((s.contains("WARNING")||s.contains("ORANGE"))&&!s.contains("BELOW WARNING"))return"warning";if(s.contains("ALERT")||s.contains("WATCH")||s.contains("YELLOW"))return"alert";if(s.contains("BELOW WARNING")||s.contains("BELOW ALERT")||s.contains("NORMAL")||s.contains("SAFE")||s.contains("GREEN")||s.contains("BLUE"))return"normal";return"";}'''
if old_fast_stage not in fast:
    raise SystemExit("fast stage anchor missing")
fast = fast.replace(old_fast_stage, new_fast_stage, 1)

# --- closed-app fallback worker: same threshold safety, geometry behavior unchanged ---
pattern = re.compile(r'''        String stage = "";\n        if \(Double\.isFinite\(level\).*?        if \(stage\.isEmpty\(\)\) return null;''', re.S)
new_block = r'''        String stage = v0911OfficialStage(official);
        if (stage.isEmpty()) {
            boolean sane = !v0911ThresholdOrderInvalid(warning, danger);
            if (sane && Double.isFinite(level) && Double.isFinite(danger) && danger > 0d && level >= danger) {
                stage = "danger";
            } else if (sane && Double.isFinite(level) && Double.isFinite(warning) && warning > 0d && level >= warning) {
                stage = "warning";
            }
        }
        if (!("warning".equals(stage) || "danger".equals(stage))) return null; // V0911_FALLBACK_OFFICIAL_STATUS_FIRST'''
fallback2, n = pattern.subn(lambda m:new_block, fallback, count=1)
if n != 1:
    raise SystemExit(f"fallback hazard status block expected once, got {n}")
fallback = fallback2

anchor = '    private static List<RiverShape> loadRiverShapes(Context app) throws Exception {'
helpers = r'''    private static boolean v0911ThresholdOrderInvalid(double warning, double danger) {
        return Double.isFinite(warning) && warning > 0d
                && Double.isFinite(danger) && danger > 0d && danger < warning;
    }

    private static String v0911OfficialStage(String raw) {
        String s = raw == null ? "" : raw.trim().toUpperCase(Locale.ROOT);
        if (s.isEmpty()) return "";
        if ((s.contains("DANGER") || s.contains("RED")) && !s.contains("BELOW DANGER")) return "danger";
        if ((s.contains("WARNING") || s.contains("ORANGE")) && !s.contains("BELOW WARNING")) return "warning";
        if (s.contains("ALERT") || s.contains("WATCH") || s.contains("YELLOW")) return "alert";
        if (s.contains("BELOW WARNING") || s.contains("BELOW ALERT") || s.contains("NORMAL")
                || s.contains("SAFE") || s.contains("GREEN") || s.contains("BLUE")) return "normal";
        return "";
    }

'''
if anchor not in fallback:
    raise SystemExit("fallback helper insertion anchor missing")
fallback = fallback.replace(anchor, helpers + anchor, 1)

# v0.9.10 is versionCode 27. v0.9.11 must be installably newer.
if "versionCode 27" not in g:
    raise SystemExit("v0.9.10 versionCode 27 missing after reconstruction")
g = g.replace("versionCode 27", "versionCode 28", 1)

for marker in ["V0911_THRESHOLD_ORDER_GUARD","V0911_INVERTED_THRESHOLD_HIDDEN","V0911_INVERTED_THRESHOLDS_NOT_TRUSTED"]:
    if marker not in ui: raise SystemExit("missing UI marker "+marker)
if "V0911_FAST_OFFICIAL_STATUS_FIRST" not in fast: raise SystemExit("missing fast status marker")
if "V0911_FALLBACK_OFFICIAL_STATUS_FIRST" not in fallback: raise SystemExit("missing fallback status marker")

UI.write_text(ui,encoding="utf-8")
FAST.write_text(fast,encoding="utf-8")
FALLBACK.write_text(fallback,encoding="utf-8")
GRADLE.write_text(g,encoding="utf-8")
print("V0911_THRESHOLD_ORDER_FIX_OK")
