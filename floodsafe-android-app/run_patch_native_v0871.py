from pathlib import Path
import subprocess, sys

root=Path(__file__).resolve().parent
# v0.8.71 = v0.8.70 contracts + exact source values + 1-second foreground recheck + live full detail.
subprocess.run([sys.executable,str(root/'run_patch_native_v0870.py')],check=True)
subprocess.run([sys.executable,str(root/'patch_native_v0871_source_exact_1s_live_detail.py')],check=True)
subprocess.run([sys.executable,str(root/'patch_native_v0871_compile_repair.py')],check=True)
print('FloodSafe v0.8.71 complete patch chain + source-status compile repair PASS')
