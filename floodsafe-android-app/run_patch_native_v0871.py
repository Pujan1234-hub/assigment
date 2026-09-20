from pathlib import Path
import subprocess, sys

root=Path(__file__).resolve().parent
subprocess.run([sys.executable,str(root/'run_patch_native_v0870.py')],check=True)
subprocess.run([sys.executable,str(root/'patch_native_v0871_source_exact_1s_live_detail.py')],check=True)
subprocess.run([sys.executable,str(root/'patch_native_v0871_compile_repair.py')],check=True)
print('FloodSafe v0.8.71 complete patch chain + compile repair PASS')
