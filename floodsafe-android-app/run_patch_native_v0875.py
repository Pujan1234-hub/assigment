from pathlib import Path
import subprocess,sys

root=Path(__file__).resolve().parent
subprocess.run([sys.executable,str(root/'run_patch_native_v0874.py')],check=True)
subprocess.run([sys.executable,str(root/'patch_native_v0875_map_smooth_river_detail.py')],check=True)
print('FloodSafe v0.8.75 complete: v0.8.74 official realtime contracts + touch-first smooth map + geometry-safe river detail PASS')
