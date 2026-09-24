from pathlib import Path

root=Path(__file__).resolve().parent
m_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
m=m_path.read_text(encoding='utf-8')

# v0.8.87 patch helper expects a modifier on method declarations.
# The generated map keeps setStations package-private, so expose it without changing behavior.
old='    void setStations(List<?> source, double lat, double lon) {'
new='    public void setStations(List<?> source, double lat, double lon) { // V0887_PREFLIGHT_SETSTATIONS_PATCHABLE'
if old in m:
    m=m.replace(old,new,1)
elif 'V0887_PREFLIGHT_SETSTATIONS_PATCHABLE' not in m:
    raise SystemExit('v0887 preflight setStations anchor missing')
m_path.write_text(m,encoding='utf-8')
print('FloodSafe v0.8.87 preflight PASS: setStations made patch-addressable')
