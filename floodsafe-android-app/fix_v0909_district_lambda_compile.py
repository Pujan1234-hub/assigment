from pathlib import Path

p=Path("floodsafe-android-app/app/src/main/java/io/github/pujan1234hub/floodsafe/app/NativeFullActivity.java")
s=p.read_text(encoding="utf-8")
old='        List<String> names=v0909AllDistrictNames();if(names.isEmpty())names=new ArrayList<>(groups.keySet());\n        String[] labels=new String[names.size()];'
new='        List<String> allNames=v0909AllDistrictNames();final List<String> names=allNames.isEmpty()?new ArrayList<>(groups.keySet()):allNames;\n        String[] labels=new String[names.size()];'
if s.count(old)!=1: raise SystemExit(f"district lambda anchor expected once, got {s.count(old)}")
s=s.replace(old,new,1)
p.write_text(s,encoding="utf-8")
print("V0909_DISTRICT_LAMBDA_COMPILE_FIX_OK")
