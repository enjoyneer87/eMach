function sketchAssemble=getGeomSketchAssembleTable(AssembleName,app)
SketchRefObjStr=getStatorGeomSketchData(app,AssembleName);
RegionData=getRegionDataArea(SketchRefObjStr,app,AssembleName);
refObjTable=struct2table(SketchRefObjStr);
ItemDataTable=struct2table(RegionData);
sketchAssemble=[refObjTable ItemDataTable];
end