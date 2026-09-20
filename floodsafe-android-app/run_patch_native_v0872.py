from pathlib import Path
import subprocess, sys

root=Path(__file__).resolve().parent
subprocess.run([sys.executable,str(root/'run_patch_native_v0871.py')],check=True)
subprocess.run([sys.executable,str(root/'patch_native_v0872_preflight.py')],check=True)
subprocess.run([sys.executable,str(root/'patch_native_v0872_status_colour_background.py')],check=True)
print('FloodSafe v0.8.72 complete patch chain PASS')
