from pathlib import Path
import subprocess, sys

root=Path(__file__).resolve().parent
subprocess.run([sys.executable,str(root/'run_patch_native_v0869.py')],check=True)
subprocess.run([sys.executable,str(root/'patch_native_v0870_bipad_point_inventory.py')],check=True)
subprocess.run([sys.executable,str(root/'patch_native_v0870_compile_repair.py')],check=True)
print('FloodSafe v0.8.70 complete patch chain + compile repair PASS')
