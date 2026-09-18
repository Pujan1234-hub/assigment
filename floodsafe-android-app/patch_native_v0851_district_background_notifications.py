from pathlib import Path

root=Path(__file__).resolve().parent
a_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java'
main_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/MainActivity.java'
g_path=root/'app/build.gradle'
a=a_path.read_text(encoding='utf-8')
main=main_path.read_text(encoding='utf-8')
g=g_path.read_text(encoding='utf-8')

# -----------------------------------------------------------------------------
# v0.8.51 FIX 1: district card wording must never imply a district has only N rivers.
# The list contains official river monitoring stations only; map geometry is separate.
# -----------------------------------------------------------------------------
old='nationalTitle=text(t("🏞️ जिल्ला अनुसार नदी अवस्था","🏞️ River status by district"),20,true,Color.rgb(16,39,70));'
new='nationalTitle=text(t("🏞️ जिल्लाअनुसार आधिकारिक नदी मापन केन्द्र","🏞️ Official river monitoring stations by district"),20,true,Color.rgb(16,39,70)); // V0851_DISTRICT_STATION_LABELS'
if old in a:a=a.replace(old,new,1)
elif 'V0851_DISTRICT_STATION_LABELS' not in a:raise SystemExit('v0851 district title anchor missing')

old='nationalSub=text(t("जिल्ला छानेर official नदी स्टेशन हेर्नुहोस्।","Choose a district to see official river stations."),12,true,Color.rgb(100,130,151));'
new='nationalSub=text(t("यो संख्या नदी/खोलाको कुल संख्या होइन; आधिकारिक नदी मापन केन्द्र मात्र हो।","This is the official monitoring-station count, not the total number of rivers or streams."),12,true,Color.rgb(100,130,151));'
if old in a:a=a.replace(old,new,1)
elif 'This is the official monitoring-station count' not in a:raise SystemExit('v0851 district subtitle anchor missing')

old='nationalFresh.setText(t(selectedDistrict+": जम्मा "+total+" • 🟢 उपलब्ध "+on+" • पछिल्लो ३० मिनेट "+fr,selectedDistrict+": total "+total+" • 🟢 available "+on+" • within 30 min "+fr));'
new='int off=Math.max(0,total-on);nationalFresh.setText(t(selectedDistrict+": आधिकारिक नदी मापन केन्द्र "+total+" • 🟢 अनलाइन "+on+" • ⚫ अफलाइन "+off+" • पछिल्लो ३० मिनेट "+fr,selectedDistrict+": official river monitoring stations "+total+" • 🟢 online "+on+" • ⚫ offline "+off+" • readings within 30 min "+fr)); /* V0851_DISTRICT_SUMMARY */'
if old in a:a=a.replace(old,new,1)
elif 'V0851_DISTRICT_SUMMARY' not in a:raise SystemExit('v0851 district summary anchor missing')

# -----------------------------------------------------------------------------
# v0.8.51 FIX 2: enabling alerts must actually enter Android's background-location
# permission flow. Previously maybeRequestBackgroundLocation() returned immediately
# because pendingBackgroundLocationEducation was never armed in the enable paths.
# -----------------------------------------------------------------------------
old='''        alertPrefs().edit().putBoolean("enabled", true).apply();
        if (!notificationsAllowed()) {'''
new='''        alertPrefs().edit().putBoolean("enabled", true).apply();
        pendingBackgroundLocationEducation = true; // V0851_BACKGROUND_LOCATION_ENABLE
        if (!notificationsAllowed()) {'''
if old in main:main=main.replace(old,new,1)
elif 'V0851_BACKGROUND_LOCATION_ENABLE' not in main:raise SystemExit('v0851 setRainAlerts background permission anchor missing')

old='''        scheduleBackgroundRainAlerts();
        FirebaseMessaging.getInstance().subscribeToTopic("nepal-alerts");
        notifyAlertStatus(true);
    }

    private void syncRainAlertsStatus()'''
new='''        scheduleBackgroundRainAlerts();
        FirebaseMessaging.getInstance().subscribeToTopic("nepal-alerts");
        notifyAlertStatus(true);
        maybeRequestBackgroundLocation();
    }

    private void syncRainAlertsStatus()'''
if old in main:main=main.replace(old,new,1)
elif 'notifyAlertStatus(true);\n        maybeRequestBackgroundLocation();\n    }\n\n    private void syncRainAlertsStatus()' not in main:raise SystemExit('v0851 setRainAlerts request anchor missing')

old='''                .putBoolean("location_stale", false)
                .apply();

        if (!notificationsAllowed()) {'''
new='''                .putBoolean("location_stale", false)
                .apply();
        pendingBackgroundLocationEducation = true; // V0851_BACKGROUND_LOCATION_POINT

        if (!notificationsAllowed()) {'''
if old in main:main=main.replace(old,new,1)
elif 'V0851_BACKGROUND_LOCATION_POINT' not in main:raise SystemExit('v0851 enableBackgroundRainAlerts permission anchor missing')

# Run one immediate weather/rain worker too, beside the already-existing immediate river worker.
old='''        OneTimeWorkRequest riverNow = new OneTimeWorkRequest.Builder(RiverAlertWorker.class)
                .setConstraints(constraints).build();
        WorkManager manager = WorkManager.getInstance(this);'''
new='''        OneTimeWorkRequest riverNow = new OneTimeWorkRequest.Builder(RiverAlertWorker.class)
                .setConstraints(constraints).build();
        OneTimeWorkRequest rainNow = new OneTimeWorkRequest.Builder(RainAlertWorker.class)
                .setConstraints(constraints).build(); // V0851_IMMEDIATE_RAIN_CHECK
        WorkManager manager = WorkManager.getInstance(this);'''
if old in main:main=main.replace(old,new,1)
elif 'V0851_IMMEDIATE_RAIN_CHECK' not in main:raise SystemExit('v0851 immediate rain worker anchor missing')

old='''        manager.enqueueUniqueWork("floodsafe-local-river-alert-now",
                ExistingWorkPolicy.REPLACE, riverNow);
        FirebaseMessaging.getInstance().subscribeToTopic("nepal-alerts");'''
new='''        manager.enqueueUniqueWork("floodsafe-local-river-alert-now",
                ExistingWorkPolicy.REPLACE, riverNow);
        manager.enqueueUniqueWork("floodsafe-local-rain-alert-now",
                ExistingWorkPolicy.REPLACE, rainNow); // V0851_IMMEDIATE_RAIN_ENQUEUE
        FirebaseMessaging.getInstance().subscribeToTopic("nepal-alerts");'''
if old in main:main=main.replace(old,new,1)
elif 'V0851_IMMEDIATE_RAIN_ENQUEUE' not in main:raise SystemExit('v0851 immediate rain enqueue anchor missing')

old='''        manager.cancelUniqueWork("floodsafe-local-river-alert-now");
        FloodMonitorService.stop(this);'''
new='''        manager.cancelUniqueWork("floodsafe-local-river-alert-now");
        manager.cancelUniqueWork("floodsafe-local-rain-alert-now");
        FloodMonitorService.stop(this);'''
if old in main:main=main.replace(old,new,1)
elif 'cancelUniqueWork("floodsafe-local-rain-alert-now")' not in main:raise SystemExit('v0851 immediate rain cancel anchor missing')

# Preserve all prior behaviour; only bump release identity after v0.8.50 has run.
if "versionCode 70" in g:g=g.replace("versionCode 70","versionCode 71",1)
elif "versionCode 71" not in g:raise SystemExit('v0851 versionCode anchor missing')
if "versionName '0.8.50'" in g:g=g.replace("versionName '0.8.50'","versionName '0.8.51'",1)
elif "versionName '0.8.51'" not in g:raise SystemExit('v0851 versionName anchor missing')

for marker in ['V0851_DISTRICT_STATION_LABELS','V0851_DISTRICT_SUMMARY']:
    if marker not in a:raise SystemExit('missing '+marker)
for marker in ['V0851_BACKGROUND_LOCATION_ENABLE','V0851_BACKGROUND_LOCATION_POINT','V0851_IMMEDIATE_RAIN_CHECK','V0851_IMMEDIATE_RAIN_ENQUEUE']:
    if marker not in main:raise SystemExit('missing '+marker)

a_path.write_text(a,encoding='utf-8')
main_path.write_text(main,encoding='utf-8')
g_path.write_text(g,encoding='utf-8')
print('FloodSafe v0.8.51 district station semantics + background alert permission flow PASS')
