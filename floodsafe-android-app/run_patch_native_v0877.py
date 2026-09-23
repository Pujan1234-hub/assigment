from pathlib import Path
import subprocess,sys

root=Path(__file__).resolve().parent
subprocess.run([sys.executable,str(root/'run_patch_native_v0876.py')],check=True)

# The legacy patch-chain method matcher assumes the opening brace follows ')' directly.
# loadTrustedRiverStationsV862 declares `throws Exception`, so make this one patch matcher
# accept an optional throws clause without touching any generated Java behavior.
p=root/'patch_native_v0877_full_station_observation_parity.py'
code=p.read_text(encoding='utf-8')
old="r'\\s*\\([^\\n]*\\)\\s*\\{',text)"
new="r'\\s*\\([^\\n]*\\)\\s*(?:throws\\s+[^{]+)?\\{',text)"
if old not in code:
    raise SystemExit('v0.8.77 matcher normalization anchor missing')
code=code.replace(old,new,1)

# v0.8.76 no longer guarantees the old V0869 comment beside refreshRiverUi's
# feedFresh.setText call. Match the call itself inside refreshRiverUi instead of a
# historical comment marker, so the parity patch survives harmless UI refactors.
old_headline="ui=re.sub(r'feedFresh\\\\.setText\\\\(t\\\\(.*?\\\\);\\\\s*// V0869_GAUGE_COUNT_UI',"
new_headline="ui=re.sub(r'feedFresh\\\\.setText\\\\(t\\\\(.*?\\\\)\\\\);(?:\\\\s*//[^\\\\n]*)?',"
if old_headline in code:
    code=code.replace(old_headline,new_headline,1)
elif new_headline not in code:
    raise SystemExit('v0.8.77 feedFresh matcher normalization anchor missing')

exec(compile(code,str(p),'exec'),{'__file__':str(p),'__name__':'__main__'})
print('FloodSafe v0.8.77 complete: v0.8.76 truth + full BIPAD river/river-trimed observation parity + stable station identity + honest inventory/live/latest status')

# Canonical v0.8.77 parity build trigger after low-end patch compatibility repair.
