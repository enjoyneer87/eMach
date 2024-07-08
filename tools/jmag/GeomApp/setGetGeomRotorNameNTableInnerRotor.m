function RotorAssemRegionTable=setGetGeomRotorNameNTableInnerRotor(geomApp)

% RotorGeomAssembleTable  =getGeomSketchAssembleTable('Rotor',geomApp);
% RotorAssemRegionTable      =getRegionItemDataTable(RotorGeomAssembleTable,'Rotor',geomApp);
% [RotorAssemRegionTable,RotorGeomArcTable]      =allocateSubSketchList2AssemRegionTable(RotorGeomAssembleTable,RotorAssemRegionTable,geomApp);
% RotorAssemRegionTable = sortrows(RotorAssemRegionTable,'distanceRFromCenter','descend');
% tic
% testfaceRegionTable=getGeomAssembleTableWithHierData(geomApp,AssembleName)
% toc

AssembleName='Rotor';
% RotorAssemRegionTable=getGeomAssembleTableWithHierData(geomApp,AssembleName);
% tic
RotorAssemRegionTable=getGeomAssemTable(geomApp,AssembleName);
% toc
RotorAssemRegionTable.Name=RotorAssemRegionTable.sketchItemName;
%% RotorCore & Shaft
RotorAssemRegionTable = updateRotorCoreAndShaftNames(RotorAssemRegionTable);
%% Magnet
RotorAssemRegionTable = allocateMagnetNamesMTable(RotorAssemRegionTable);

%%[TB] Sleeve

%% Air Region
RotorAssemRegionTable = updateOtherRegionNames2AirRegion(RotorAssemRegionTable);

%% changeName
RotorAssemRegionTable=changeNameGeomSketchAll(RotorAssemRegionTable,geomApp);

%%

AssemTable = getGeomAssemItemListTable(geomApp);
PartGeomTable=AssemTable(contains(AssemTable.Type,'Part'),:); 

if isempty(PartGeomTable)  % only Sketch
    geomApp.GetDocument().GetAssembly().GetItem('Rotor').CloseSketch();
    disp('2D')
else 
    BoolPartIndex=contains(PartGeomTable.AssemItemName,AssembleName,"IgnoreCase",true);
    PartName=PartGeomTable.AssemItemName{BoolPartIndex};
    PartObj=geomApp.GetDocument().GetAssembly().GetItem(PartName);
    PartObj.ClosePart()
    disp('Sketch in 3D')
end

end