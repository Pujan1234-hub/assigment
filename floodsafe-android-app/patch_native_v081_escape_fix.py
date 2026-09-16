from pathlib import Path

p = Path(__file__).resolve().parent / 'app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java'
text = p.read_text(encoding='utf-8')

bad = 'rows[i]=stageDot(s.stage)+" "+s.name+"\n"+stationLine(s);'
good = 'rows[i]=stageDot(s.stage)+" "+s.name+"\\n"+stationLine(s);'

if good not in text:
    if bad not in text:
        raise SystemExit('district row newline marker missing')
    text = text.replace(bad, good, 1)

p.write_text(text, encoding='utf-8')
if good not in p.read_text(encoding='utf-8'):
    raise SystemExit('district row newline escape fix failed')
print('FloodSafe v0.8.1 district row newline escape PASS')
