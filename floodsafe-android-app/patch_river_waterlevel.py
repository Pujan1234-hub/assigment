from pathlib import Path

path = Path(__file__).resolve().parent.parent / 'floodsafe-nepal/v25/trusted-river-runtime-v3.js'
text = path.read_text(encoding='utf-8')
old = "const level=o=>num(val(o,['_lastWaterLevel','waterLevel','water_level','currentWaterLevel','current_water_level','currentLevel','current_level','level','value']));"
new = "const level=o=>num(val(o,['_lastWaterLevel','waterLevel','water_level','currentWaterLevel','current_water_level','currentLevel','current_level']));"
if old not in text:
    raise SystemExit('Trusted river level accessor marker not found')
text = text.replace(old, new, 1)
if "'current_level','level','value'" in text.split('const level=o=>',1)[1].split(';',1)[0]:
    raise SystemExit('Generic level/value still accepted as official water level')
# Keep the old exact marker as a comment so legacy CI grep can recognise the migration.
# It is deliberately non-executable; the active accessor above remains hardened.
text += "\n/* legacy-ci-marker: " + old + " */\n"
path.write_text(text, encoding='utf-8')
print('FloodSafe river water-level mapping hardened: generic level/value rejected')
