from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parent
patches = [
    'patch_webview_crash.py',
    'patch_launcher_reopen_hard_reset.py',
    'patch_auto_alerts.py',
    'patch_river_waterlevel.py',
    'patch_two_hour_weather.py',
    'patch_cold_start_blank.py',
    'patch_cross_device_navigation.py',
    'patch_native_compat_fallback.py',
    'patch_map_smooth_v075.py',
    'patch_full_native_v080.py',
    'patch_native_v081_polish.py',
    'patch_native_v081_escape_fix.py',
    'patch_native_maplibre_v082.py',
    'patch_native_map_detail_v083.py',
    'patch_native_v084_sathi_map.py',
    'patch_native_v085_flow_sathi.py',
    'patch_native_v086_full_waterways.py',
    'patch_native_v087_runtime_rivers.py',
    'patch_native_v088_restore_web_rivers.py',
    'patch_native_v089_realtime_gauges.py',
    'patch_native_v0810_live_source_colours.py',
    'patch_native_v0810_compile_fix.py',
    'patch_native_v0811_map_anr_fix.py',
    'patch_native_v0812_trusted_latest_flow.py',
    'patch_native_v0813_prep_truth_ui.py',
    'patch_native_v0813_nepal_truth_map.py',
    'patch_native_v0814_prep_runtime_counts.py',
    'patch_native_v0814_source_exact_smooth.py',
    'patch_native_v0814_compile_fix.py',
    'patch_native_v0815_single_source_truth.py',
    'patch_native_v0816_current_only_map.py',
    'patch_native_v0817_clean_web_map.py',
    'patch_native_v0817_compile_rain_fix.py',
    'patch_native_v0818_direct_river_clean_flow.py',
    'patch_native_v0819_web_live_master.py',
    'patch_native_v0820_place_labels_prep.py',
    'patch_native_v0820_nepal_mask_prep.py',
    'patch_native_v0820_nepal_only_local_rivers.py',
    'patch_native_v0821_actual_river_geometry.py',
    'patch_native_v0822_viewport_rivers.py',
    'patch_native_v0823_visible_bounds_rivers.py',
    'patch_native_v0824_strict_nepal_source_truth.py',
    'patch_native_v0825_segment_current_flow.py',
    'patch_native_v0825_helper_restore.py',
    'patch_native_v0826_video_map_ui.py',
    'patch_native_v0827_compact_realtime_map.py',
    'patch_native_v0828_finish_blue_nepal_map.py',
    'patch_native_v0828_compile_fix.py',
    'patch_native_v0829_flow_glow_dense_network.py',
    'patch_native_v0830_visible_blue_glow_everywhere.py',
    'patch_native_v0831_hard_nepal_clip.py',
    'patch_native_v0832_restore_strict_blue_flow.py',
    'patch_native_v0833_thin_flow_risk_colours.py',
    'patch_native_v0834_force_visible_nepal_flow.py',
    'patch_native_v0835_fast_overview_rain_taps.py',
    'patch_native_v0836_five_minute_freshness.py',
]

for name in patches:
    print(f'==> {name}', flush=True)
    subprocess.run([sys.executable, str(root / name)], check=True)

print('FloodSafe patches through v0.8.36 applied successfully')
