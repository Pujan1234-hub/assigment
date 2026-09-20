from pathlib import Path
import subprocess, sys

root=Path(__file__).resolve().parent
# Preserve the complete native v0.8.72 chain, then apply only the requested
# river/rain/hydrology-lake station visibility and status-colour parity change.
subprocess.run([sys.executable,str(root/'run_patch_native_v0872.py')],check=True)
subprocess.run([sys.executable,str(root/'patch_native_v0873_official_hydro_rain_lake.py')],check=True)
print('FloodSafe v0.8.73 complete native river/rain/hydrology-lake patch chain PASS')
