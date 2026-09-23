from pathlib import Path
import subprocess,sys

root=Path(__file__).resolve().parent
subprocess.run([sys.executable,str(root/'run_patch_native_v0876.py')],check=True)
subprocess.run([sys.executable,str(root/'patch_native_v0877_full_station_observation_parity.py')],check=True)
print('FloodSafe v0.8.77 complete: v0.8.76 truth + full BIPAD river/river-trimed observation parity + stable station identity + honest inventory/live/latest status')
