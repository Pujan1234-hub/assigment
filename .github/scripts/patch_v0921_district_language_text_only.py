from pathlib import Path

p = Path('floodsafe-android-app/app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java')
s = p.read_text(encoding='utf-8')

# ONLY the district instruction text/language behaviour requested by the user.
# Do not touch map, river data, cloud, SATHI, weather logic, location logic, notifications or navigation.

field_old = '    private Button v0908DistrictPicker;\n'
field_new = '    private Button v0908DistrictPicker;\n    private TextView v0921DistrictHint; // V0921_DISTRICT_LANGUAGE_TEXT_ONLY\n'
if field_old not in s:
    raise SystemExit('district picker field anchor missing')
s = s.replace(field_old, field_new, 1)

hint_old = '        TextView districtHint=text(t("एउटा जिल्ला छान्दा त्यही जिल्लाका official नदी/खोला स्टेशन मात्र देखिन्छन्।","Choose one district to show only that district\'s official river stations."),11,true,Color.rgb(88,118,140));\n        c.addView(districtHint);\n'
hint_new = '        v0921DistrictHint=text(t("जिल्ला छान्दा त्यही जिल्लाका आधिकारिक नदी/खोला स्टेशन देखिन्छन्।","Choose a district to view its official river stations."),11,true,Color.rgb(88,118,140));\n        c.addView(v0921DistrictHint);\n'
if hint_old not in s:
    raise SystemExit('district hint exact anchor missing')
s = s.replace(hint_old, hint_new, 1)

# Remove the redundant empty-state sentence from the visible UI.
empty_old = '            nationalList.addView(empty(t("माथिको जिल्ला बटन थिच्नुहोस् — लामो ७७-जिल्ला सूची अब यहाँ देखिँदैन।","Tap the district button above — the long district list is no longer shown here.")));\n            return;\n'
empty_new = '            return; // V0921_REMOVE_REDUNDANT_DISTRICT_MESSAGE\n'
if empty_old not in s:
    raise SystemExit('redundant district message anchor missing')
s = s.replace(empty_old, empty_new, 1)

# v0.9.09 generated an in-place translation table containing the old sentence too.
# Replace those old literals everywhere so that wording cannot reappear after a language toggle.
s = s.replace(
    'माथिको जिल्ला बटन थिच्नुहोस् — लामो ७७-जिल्ला सूची अब यहाँ देखिँदैन।',
    'माथिबाट जिल्ला छान्नुहोस्।'
)
s = s.replace(
    'Tap the district button above — the long district list is no longer shown here.',
    'Choose a district above.'
)

# The existing fast language switch does not recreate the Activity, so explicitly refresh this
# newly tracked district hint in-place when English/Nepali changes.
toggle_old = 'applyLanguage();v0909TranslateStaticTree(root);refreshRiverUi();updateWeatherLayerUi();'
toggle_new = 'applyLanguage();v0921UpdateDistrictHint();v0909TranslateStaticTree(root);refreshRiverUi();updateWeatherLayerUi();'
if s.count(toggle_old) != 1:
    raise SystemExit(f'language toggle anchor count={s.count(toggle_old)}')
s = s.replace(toggle_old, toggle_new, 1)

helper = '''    private void v0921UpdateDistrictHint(){\n        if(v0921DistrictHint!=null)v0921DistrictHint.setText(t("जिल्ला छान्दा त्यही जिल्लाका आधिकारिक नदी/खोला स्टेशन देखिन्छन्।","Choose a district to view its official river stations."));\n    } // V0921_DISTRICT_HINT_LANGUAGE_SYNC\n\n'''
anchor = '    private String t(String ne,String en){return english?en:ne;}\n'
if anchor not in s:
    raise SystemExit('t() anchor missing')
s = s.replace(anchor, helper + anchor, 1)

# Guardrails: requested text must be gone and the known NativeFullActivity systems must still be present.
for banned in [
    'the long district list is no longer shown here',
    'लामो ७७-जिल्ला सूची अब यहाँ देखिँदैन'
]:
    if banned in s:
        raise SystemExit('redundant district wording still present: ' + banned)
for marker in [
    'V0918_LANGUAGE_KEEP_MAP_VISIBLE',
    'V0920_CURRENT_LOCATION_RETRY',
    'V0921_DISTRICT_LANGUAGE_TEXT_ONLY',
    'V0921_DISTRICT_HINT_LANGUAGE_SYNC',
    'V0921_REMOVE_REDUNDANT_DISTRICT_MESSAGE'
]:
    if marker not in s:
        raise SystemExit('required marker missing: ' + marker)
if 'android.webkit.WebView' in s:
    raise SystemExit('WebView introduced')

p.write_text(s, encoding='utf-8')
print('V0921_DISTRICT_LANGUAGE_TEXT_ONLY_OK')
