function sketchAssembleTable=getGeomSketchAssembleTable(AssembleName,geomApp)
    geomApp.Hide;
    AssemObjStruct              = getStatorGeomSketchData(geomApp,AssembleName);
    % RegionData                  = getRegionDataArea(AssemObjStruct,app,AssembleName);
    %% Struct 2 Table
    refObjTable                 =struct2table(AssemObjStruct);
    % ItemDataTable=struct2table(RegionData);
    % sketchAssemble=[refObjTable ItemDataTable];
    sketchAssembleTable=refObjTable;

    sketchAssembleTable=getRegionSubSketchList(sketchAssembleTable);
    geomApp.Show

end