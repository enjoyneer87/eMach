function PartGeomTable=GeomFaceExtrude3piece(PartGeomTable,geomApp)
% from devCreateGeomFaceExtrudeSolid
% from devGeomExtrude3piece
%% check IdName
mergedTable = vertcat(PartGeomTable.RefObjListTable{:});
BoolFaceExtrude       = contains(mergedTable.IdentifierName,'FaceExtrude');

%% Face Extrude
if ~any(BoolFaceExtrude)
    for PartIndex=1:height(PartGeomTable)
        FaceExtrudeCells = PartGeomTable.FaceExtrudeCells(PartIndex);
        PartName         = PartGeomTable.AssemItemName{PartIndex};    
        % createGeomFaceExtrudeSolid - FaceExtrudeSet으로 Extrdue하기
        FaceExtrudeObj  = createGeomFaceExtrudeSolid(FaceExtrudeCells,PartName,geomApp);
        PartGeomTable.FaceExtrudeObj(PartIndex)  ={FaceExtrudeObj}; % to Table
    end
end
%% Close part
PartGeomTable.AssemItem.ClosePart;
end