from pathlib import Path
import subprocess,sys

root=Path(__file__).resolve().parent
# Start only from the last canonical, proven v0.8.76 source chain.
subprocess.run([sys.executable,str(root/'run_patch_native_v0876.py')],check=True)
# Apply one clean v0.8.77 parity patch. No patch-on-patch runtime rewriting.
subprocess.run([sys.executable,str(root/'patch_native_v0877_full_station_observation_parity.py')],check=True)
print('FloodSafe v0.8.77 clean runner complete')
