from pathlib import Path
import subprocess, sys, re

root=Path(__file__).resolve().parent

patches=[
'patch_webview_crash.py','patch_launcher_reopen_hard_reset.py','patch_auto_alerts.py','patch_river_waterlevel.py',
'patch_two_hour_weather.py','patch_cold_start_blank.py','patch_cross_device_navigation.py','patch_native_compat_fallback.py',
'patch_map_smooth_v075.py','patch_full_native_v080.py','patch_native_v081_polish.py','patch_native_v081_escape_fix.py',
'patch_native_maplibre_v082.py','patch_native_map_detail_v083.py','patch_native_v084_sathi_map.py','patch_native_v085_flow_sathi.py',
'patch_native_v086_full_waterways.py','patch_native_v087_runtime_rivers.py','patch_native_v088_restore_web_rivers.py',
'patch_native_v089_realtime_gauges.py','patch_native_v0810_live_source_colours.py','patch_native_v0810_compile_fix.py',
'patch_native_v0811_map_anr_fix.py','patch_native_v0812_trusted_latest_flow.py','patch_native_v0813_prep_truth_ui.py',
'patch_native_v0813_nepal_truth_map.py','patch_native_v0814_prep_runtime_counts.py','patch_native_v0814_source_exact_smooth.py',
'patch_native_v0814_compile_fix.py','patch_native_v0815_single_source_truth.py','patch_native_v0816_current_only_map.py',
'patch_native_v0817_clean_web_map.py','patch_native_v0817_compile_rain_fix.py','patch_native_v0818_direct_river_clean_flow.py',
'patch_native_v0819_web_live_master.py','patch_native_v0820_place_labels_prep.py','patch_native_v0820_nepal_mask_prep.py',
'patch_native_v0820_nepal_only_local_rivers.py','patch_native_v0821_actual_river_geometry.py','patch_native_v0822_viewport_rivers.py',
'patch_native_v0823_visible_bounds_rivers.py','patch_native_v0824_strict_nepal_source_truth.py','patch_native_v0825_segment_current_flow.py',
'patch_native_v0825_helper_restore.py','patch_native_v0826_video_map_ui.py','patch_native_v0827_compact_realtime_map.py',
'patch_native_v0828_finish_blue_nepal_map.py','patch_native_v0828_compile_fix.py','patch_native_v0829_flow_glow_dense_network.py',
'patch_native_v0830_visible_blue_glow_everywhere.py','patch_native_v0831_hard_nepal_clip.py','patch_native_v0832_restore_strict_blue_flow.py',
'patch_native_v0833_thin_flow_risk_colours.py','patch_native_v0834_force_visible_nepal_flow.py']

for p in patches:
    subprocess.run([sys.executable,str(root/p)],check=True)

p=root/'patch_native_v0835_fast_overview_rain_taps.py'
s=p.read_text(encoding='utf-8')
s='\n'.join(line for line in s.splitlines() if "'readRiverTile(x,y,null)'," not in line)+'\n'
p.write_text(s,encoding='utf-8')

rest=[
'patch_native_v0835_fast_overview_rain_taps.py','patch_native_v0835_compile_helpers.py',
'patch_native_v0836_video_blue_rivers_combined_detail.py','patch_native_v0837_preclipped_visible_rivers.py',
'patch_native_v0838_full_nepal_rivers_close.py','patch_native_v0839_complete_edge_rivers.py',
'patch_native_v0840_regional_edge_tiles.py','patch_native_v0841_full_national_network.py',
'patch_native_v0842_progressive_zoom_rivers.py','patch_native_v0843_touchable_rivers.py',
'patch_native_v0844_final_all_river_taps_online.py','patch_native_v0845_live_source_parity.py',
'patch_native_v0846_bipad_dhm_union_realtime.py','patch_native_v0847_moving_river_glow.py',
'patch_native_v0848_station_district.py','patch_native_v0848_sathi_advanced.py','patch_native_v0848_risk_colour.py',
'patch_native_v0848_compile_fix.py','patch_native_v0849_source_parity_online_dots.py','run_patch_native_v0850.py',
'patch_native_v0851_district_background_notifications.py','patch_native_v0852_my_location_map.py',
'patch_native_v0853_five_minute_river_freshness.py','patch_native_v0854_language_five_minute_ui.py',
'patch_native_v0856_crashfix_clean_20min.py','patch_native_v0857_nearby_status_language.py',
'patch_native_v0858_station_history_realtime.py','patch_native_v0859_header_language_no_crash.py',
'patch_native_v0860_restore_source_parity_header_location.py','run_patch_native_v0861.py',
'patch_native_v0862_realtime_final.py','patch_native_v0862_compile_helpers.py',
'patch_native_v0863_river_tap_truth.py','patch_native_v0864_restore_station_inventory.py',
'patch_native_v0865_news_language_sync.py','patch_native_v0866_station_river_geometry_truth.py',
'patch_native_v0867_realtime_source_parity.py']
for p in rest:
    subprocess.run([sys.executable,str(root/p)],check=True)

rain_worker=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/RainAlertWorker.java'
rw=rain_worker.read_text(encoding='utf-8')
if 'V0869_TWO_HOUR_DIGEST' not in rw:
    rw,n=re.subn(r'private\s+static\s+final\s+long\s+WEATHER_DIGEST_INTERVAL_MS\s*=\s*[^;]+;',
                 'private static final long WEATHER_DIGEST_INTERVAL_MS = 3L * 60L * 60L * 1000L;',rw,count=1)
    if n!=1: raise SystemExit('v0869 runner could not normalize weather digest anchor')

# Normalize whatever earlier formatting/version of the follow-device freshness block exists.
# This only touches RainAlertWorker; RiverAlertWorker keeps the strict 2 km safety policy.
if 'V0869_WEATHER_LOCATION_RESILIENCE' not in rw:
    pat=re.compile(r'(?ms)^\s*if\s*\(\s*prefs\.getBoolean\(\s*"follow_device"\s*,\s*false\s*\)\s*\)\s*\{.*?^\s*\}')
    canonical='''        if (prefs.getBoolean("follow_device", false)) {
            long locationTime = prefs.getLong("location_time", 0L);
            if (!MonitoringLocationPolicy.freshDeviceLocation(
                    locationTime, System.currentTimeMillis(), lat, lon)) return Result.success();
        }'''
    rw,n=pat.subn(canonical,rw,count=1)
    if n!=1: raise SystemExit('v0869 runner could not normalize RainAlertWorker location anchor')

rain_worker.write_text(rw,encoding='utf-8')

subprocess.run([sys.executable,str(root/'patch_native_v0869_gauge_notifications_truth.py')],check=True)
print('FloodSafe v0.8.69 complete patch chain PASS')
