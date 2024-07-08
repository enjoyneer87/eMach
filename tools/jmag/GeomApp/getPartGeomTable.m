function PartGeomTable=getPartGeomTable(geomApp)
% From devGeomExtrude3piece
%% get All RefObjPerPart Sort RefObjTable
%1) getRefObjListTableFromCurrentSelection 수행
%2) part별 ExtrudeSolid 이름 확인 by RegionItem으로
%3) face/Edge/Vertex 구분 
%4) lump구분(Solid)

%% getAllRefObjListTableWithSel
RefObjListTable =getAllRefObjListTableWithSel(geomApp);
AllRefObjIDCell =RefObjListTable.IdentifierName;
%% geomGeomAssemWithSimpleHier
PartGeomTable   =geomGeomAssemWithSimpleHier(geomApp); % sketch filter 내장
%% Face
for PartIndex=1:height(PartGeomTable)
    %% Get Face
       % get ExtrudeSolid Number
       ExtrudeSolidName      =PartGeomTable.ItemTableList{PartIndex}(2).ExtrudeSolid;
       % Bool ExtrudeSolid Face 
       Bool_CurExtrudeSolid  = contains(AllRefObjIDCell,ExtrudeSolidName);
       tempCell              = AllRefObjIDCell(Bool_CurExtrudeSolid);
       RefObjIDListTable     = RefObjListTable(Bool_CurExtrudeSolid,:);

       Bool_nonEdge          = ~contains(tempCell,'edge');
       tempCell              = tempCell(Bool_nonEdge);
       Bool_nonVertex        = ~contains(tempCell,'vertex');
       tempCell              = tempCell(Bool_nonVertex);
       Bool_nonlump          = ~contains(tempCell,'lump');
       tempCell              = tempCell(Bool_nonlump);
       %% FaceCell
       facesCell             = tempCell;
       if ~contains(facesCell,'faceExtrude','IgnoreCase',true)
       % Face Extrude Bool
       Bool_4rdBracket       = ~contains(facesCell,'))))');
       facesCell             = facesCell(Bool_4rdBracket);
       % Back    % Back face-face
       Bool_3rdBracket       = ~contains(facesCell,')))');
       BackfacesCell         = facesCell(Bool_3rdBracket);
       % Front   % face-face-face;
       FrontfaceCell         = facesCell(~Bool_3rdBracket);
       else
       % Face Extrude Bool
       Bool_4rdBracket       = ~contains(facesCell,')))))');
       facesCell             = facesCell(Bool_4rdBracket);
       % Back    % Back face-face
       Bool_3rdBracket       = ~contains(facesCell,'))))');
       BackfacesCell         = facesCell(Bool_3rdBracket);
       % Front   % face-face-face;
       FrontfaceCell         = facesCell(~Bool_3rdBracket);
       end
       %% 2 FaceExtrudeCells Struct
       FaceExtrudeCells.BackfacesCell    =BackfacesCell;
       FaceExtrudeCells.FrontfaceCell    =FrontfaceCell;
       %% 2 PartGeomTable 
       PartGeomTable.RefObjListTable(PartIndex) = {RefObjIDListTable};
       PartGeomTable.FaceExtrudeCells(PartIndex)  =  FaceExtrudeCells;    
end
end


       % get ExtrudeSolid Number
            % Get Lump
       % Origin Part Sketch Region
       % PartObj        = PartGeomTable.AssemItem(PartIndex);
       % PartName       = PartGeomTable.AssemItemName{PartIndex};
       % FaceRegionCell_of_ExtrudeSolid=PartGeomTable.ItemTableList{PartIndex}(1).Sketch.IdentifierName;