from pathlib import Path

p = Path("floodsafe-android-app/patch_native_v0911_river2km_events_language_ninda.py")
code = p.read_text(encoding="utf-8")
old = '''if 'danger>0&&level>=danger' not in ui:\n    raise SystemExit("fresh numeric danger threshold invariant missing")'''
new = '''if not re.search(r'danger\\s*>\\s*0(?:d)?\\s*&&\\s*level\\s*>=\\s*danger', ui):\n    raise SystemExit("fresh numeric danger threshold invariant missing")'''
if old not in code:
    raise SystemExit("v0911 invariant check source anchor missing")
code = code.replace(old, new, 1)
exec(compile(code, str(p), "exec"), {"__name__": "__main__", "__file__": str(p)})
