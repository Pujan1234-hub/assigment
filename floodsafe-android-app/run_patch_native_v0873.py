from pathlib import Path
import subprocess, sys

root=Path(__file__).resolve().parent
# Preserve the verified native v0.8.71 chain (which includes the accepted v0.8.70 baseline),
# then apply only the requested official river/rain/hydrology-lake station parity fix.
# The older v0.8.72 layer-anchor patch is deliberately bypassed because its hard-coded
# visual anchor is incompatible with the later native river renderer; its background
# one-second behavior is already provided by FloodLiveGaugeMonitor/FloodMonitorService.
subprocess.run([sys.executable,str(root/'run_patch_native_v0871.py')],check=True)

# v0.8.71 compile repair converts the one-line scheduler comment to a block comment so
# the Runnable body remains valid Java. Normalize only the v0.8.73 patch's expected
# anchor before executing it; this changes no app behavior.
p=root/'patch_native_v0873_source_parity_v2.py'
s=p.read_text(encoding='utf-8')
s=s.replace("poll='main.postDelayed(this,1_000L); // V0871_ONE_SECOND_SOURCE_RECHECK'",
            "poll='main.postDelayed(this,1_000L); /* V0871_ONE_SECOND_SOURCE_RECHECK */'",1)
p.write_text(s,encoding='utf-8')

subprocess.run([sys.executable,str(p)],check=True)
print('FloodSafe v0.8.73 complete native river/rain/hydrology-lake V2 patch chain PASS')
