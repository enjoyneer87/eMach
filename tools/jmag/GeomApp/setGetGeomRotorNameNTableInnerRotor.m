function RotorAssemRegionTable=setGetGeomRotorNameNTableInnerRotor(RotorGeomAssembleTable,geomApp)

RotorGeomAssembleTable  =getGeomSketchAssembleTable('Rotor',geomApp);
RotorAssemRegionTable      =getRegionItemDataTable(RotorGeomAssembleTable,'Rotor',geomApp);
[RotorAssemRegionTable,RotorGeomArcTable]      =allocateSubSketchList2AssemRegionTable(RotorGeomAssembleTable,RotorAssemRegionTable,geomApp);
RotorAssemRegionTable = sortrows(RotorAssemRegionTable,'distanceRFromCenter','descend');



RotorOnePoleAngle=max(RotorGeomArcTable.EndVertexTabletheta);

Poles       = 360/RotorOnePoleAngle;
PhaseNumber=3;


%% RotorCore & Shaft
RotorAssemRegionTable = updateRotorCoreAndShaftNames(RotorAssemRegionTable);
%% Magnet
RotorAssemRegionTable = allocateMagnetNamesMTable(RotorAssemRegionTable);

%%[TB] Sleeve

%% Air Region
RotorAssemRegionTable = updateOtherRegionNames2AirRegion(RotorAssemRegionTable);

%% changeName
changeNameGeomSketchAll(RotorAssemRegionTable,geomApp);

end