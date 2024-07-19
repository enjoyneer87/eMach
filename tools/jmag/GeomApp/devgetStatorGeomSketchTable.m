function StatorAssemTable=devgetStatorGeomSketchTable(app)
    StatorSketchRefObjStr=getStatorGeomSketchData(app);
    % RegionData=getRegionDataArea(StatorSketchRefObjStr,app);
    refObjTable=struct2table(StatorSketchRefObjStr);
    % ItemDataTable=struct2table(RegionData);
    
    % StatorAssemTable=[refObjTable ItemDataTable];
end