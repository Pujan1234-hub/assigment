from pathlib import Path

root=Path(__file__).resolve().parent
p=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java'
a=p.read_text(encoding='utf-8')
old='main.postDelayed(this,1_000L); // V0871_ONE_SECOND_SOURCE_RECHECK'
new='main.postDelayed(this,1_000L); /* V0871_ONE_SECOND_SOURCE_RECHECK */'
if old in a:
    a=a.replace(old,new,1)
elif new not in a:
    raise SystemExit('v0871 inline 1s poll marker missing')
p.write_text(a,encoding='utf-8')
if 'main.postDelayed(this,1_000L); /* V0871_ONE_SECOND_SOURCE_RECHECK */' not in a:
    raise SystemExit('v0871 compile repair failed')
print('FloodSafe v0.8.71 compile repair PASS: 1s poll marker no longer comments out Runnable closure')
