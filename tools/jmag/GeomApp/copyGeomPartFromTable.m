function GeomNameStruct=copyGeomPartFromTable(AssemRegionTable,geomApp)

GeomNameStruct    =findUniqueRegionNameListFromTable(AssemRegionTable);

uniqueRegionNameCell=GeomNameStruct.uniqueRegionNameCell;
%% det ItemName
ItemName        =detStatorORRotor(uniqueRegionNameCell);
%%
    HowMany= length(uniqueRegionNameCell);  
%% CopyFunction
    copyGeomPart(ItemName,geomApp,HowMany) 

%% getGeomPartlistCell
AssembleAllPartName=getGeomPartlistCell(geomApp);
AssembleItemIndex      =contains(AssembleAllPartName,ItemName);
ItemPartNameListCell   =AssembleAllPartName(AssembleItemIndex);

%%
GeomNameStruct.SketchName   =ItemName;
GeomNameStruct.PartNameList =ItemPartNameListCell;

end