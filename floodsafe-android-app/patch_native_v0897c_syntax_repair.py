from pathlib import Path

root=Path(__file__).resolve().parent
p=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java'
s=p.read_text(encoding='utf-8')
old='row.put("_floodsafeCurrentResponse",false);row.put("_floodsafeSource","Last verified official observation cache"); // V0897_CACHE_NOT_CURRENT}catch(Exception ignored){}'
new='row.put("_floodsafeCurrentResponse",false);row.put("_floodsafeSource","Last verified official observation cache");}catch(Exception ignored){} // V0897C_CACHE_TRY_CATCH_REPAIR'
if old not in s: raise SystemExit('v0897c broken cache try/catch anchor missing')
s=s.replace(old,new,1)
if 'V0897C_CACHE_TRY_CATCH_REPAIR' not in s: raise SystemExit('v0897c marker missing')
p.write_text(s,encoding='utf-8')
print('v0.8.97c cache try/catch syntax repair applied')
