from pathlib import Path

root=Path(__file__).resolve().parent
m_path=root/'app/src/main/java/io/github/pujan1234hub/floodsafe/app/FloodSafeNativeMapView.java'
m=m_path.read_text(encoding='utf-8')

start=m.find('    private static final String STYLE_JSON =')
end=m.find(';\n',start)
if start<0 or end<0:
    raise SystemExit('STYLE_JSON block missing')
block=m[start:end+1]

if 'World_Boundaries_and_Places' not in block:
    source_anchor='\\"attribution\\":\\"Terrain © AWS Terrain Tiles\\"}}'
    source_new='\\"attribution\\":\\"Terrain © AWS Terrain Tiles\\"},\\"places\\":{\\"type\\":\\"raster\\",\\"tiles\\":[\\"https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}\\"],\\"tileSize\\":256,\\"minzoom\\":7,\\"maxzoom\\":19,\\"attribution\\":\\"Places © Esri\\"}}'
    layer_anchor='\\"hillshade-accent-color\\":\\"#4f7f8e\\"}}]}'
    layer_new='\\"hillshade-accent-color\\":\\"#4f7f8e\\"}},{\\"id\\":\\"places\\",\\"type\\":\\"raster\\",\\"source\\":\\"places\\",\\"minzoom\\":7,\\"paint\\":{\\"raster-opacity\\":0.94}}]}'
    if source_anchor not in block:
        raise SystemExit('terrain source insertion anchor missing')
    if layer_anchor not in block:
        raise SystemExit('hillshade layer insertion anchor missing')
    block=block.replace(source_anchor,source_new,1).replace(layer_anchor,layer_new,1)
    m=m[:start]+block+m[end+1:]

if 'World_Boundaries_and_Places' not in m or '\\"id\\":\\"places\\"' not in m:
    raise SystemExit('place labels overlay prep failed')

m_path.write_text(m,encoding='utf-8')
print('FloodSafe v0.8.20 place-name overlay prep PASS')
