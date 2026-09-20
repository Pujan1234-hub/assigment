from pathlib import Path
import subprocess,sys
root=Path(__file__).resolve().parent
subprocess.run([sys.executable,str(root/'run_patch_native_v0873.py')],check=True)
subprocess.run([sys.executable,str(root/'patch_native_v0874_nepal_fixed_map_district.py')],check=True)
print('FloodSafe v0.8.74 complete: v0.8.73 realtime source chain + Nepal-only map/district regression repair PASS')
