function sketchAssembleTable=getGeomSketchAssembleTable(AssembleName,app)
    AssemObjStruct              = getStatorGeomSketchData(app,AssembleName);
    % RegionData                  = getRegionDataArea(AssemObjStruct,app,AssembleName);
    %% Struct 2 Table
    refObjTable                 =struct2table(AssemObjStruct);
    % ItemDataTable=struct2table(RegionData);
    % sketchAssemble=[refObjTable ItemDataTable];
    sketchAssembleTable=refObjTable;



end