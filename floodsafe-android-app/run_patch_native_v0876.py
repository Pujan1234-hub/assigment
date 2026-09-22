from pathlib import Path
import subprocess,sys

root=Path(__file__).resolve().parent
subprocess.run([sys.executable,str(root/'run_patch_native_v0875.py')],check=True)
subprocess.run([sys.executable,str(root/'patch_native_v0876_realtime_truth_freshness.py')],check=True)
subprocess.run([sys.executable,str(root/'postflight_v0876_exact_number.py')],check=True)
print('FloodSafe v0.8.76 complete: v0.8.75 smooth map + exact official latest rows + fresh-only LIVE truth + exact source precision PASS')
