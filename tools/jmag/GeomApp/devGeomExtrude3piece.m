function PartGeomTable=devGeomExtrude3piece(geomApp)
% BoolfaceExtrudeList=[];
% geomApp.Hide;
%% for문 getAllRefObjListTableWithSel 추가시 6.67초
%% getAllRefObjListTableWithSel 먼저하고
% % get RefObj 2.2초
% tic
RefObjListTable =getAllRefObjListTableWithSel(geomApp);
% toc
AllRefObjIDCell = RefObjListTable.IdentifierName;
%% geomGeomAssemWithSimpleHier에서 openPart하면서 Extrude하면 더빠를꺼같은데
% 2.39초
% tic
PartGeomTable=geomGeomAssemWithSimpleHier(geomApp); % sketch filter 내장
% toc
%% From AllRefObjIDCell 
% ExtrudeSolid Id Get Per Part By RegionItem
% Unique Extrude Solid
% BoolExtrudeSolid     =contains(AllRefObjIDCell,'TExtrudeSolid');
% ExtrudeSolidCell     = AllRefObjIDCell(BoolExtrudeSolid);
% splitIdentifierNames_ExtrudeSolid = cellfun(@(x) strsplit(x, '+'), ExtrudeSolidCell, 'UniformOutput', false);
% lastCells_Solid      = extractSplitedLastSCells(splitIdentifierNames_ExtrudeSolid);
% firstCells_Solid     = extractSplitedFirstCells(splitIdentifierNames_ExtrudeSolid);
% firstCells_Solid     = unique(firstCells_Solid)
% 
% splitIdentifierNames_firstCells_Solid = cellfun(@(x) strsplit(x, '('), firstCells_Solid, 'UniformOutput', false);
% ExtrudeSolidCell     = extractSplitedLastSCells(splitIdentifierNames_firstCells_Solid);
% ExtrudeSolidCell     =unique(ExtrudeSolidCell);

%% From AllRefObjIDCell
% splitIdentifierNames = cellfun(@(x) strsplit(x, '+'), AllRefObjIDCell, 'UniformOutput', false);
% lastCells            = extractSplitedLastSCells(splitIdentifierNames)
% BoolRegionItem       = contains(lastCells,'RegionItem')
% RegionItemCell       = AllRefObjIDCell(BoolRegionItem)
% BoolExtrudeSolid     =contains(RegionItemCell,'TExtrudeSolid');
% ExtrudeSolidCell     =RegionItemCell(BoolExtrudeSolid)
% extractSplitedLastSCells
%[TB] Check Is Ther FaceExtrude
BoolFaceExtrude       = contains(AllRefObjIDCell,'FaceExtrude');
if ~any(BoolFaceExtrude)
    %% Face
    for PartIndex=1:height(PartGeomTable)
        %% Get Face
            % get ExtrudeSolid Number
                % Get Lump
           % Origin Part Sketch Region
           PartObj        = PartGeomTable.AssemItem(PartIndex);
           PartName       = PartGeomTable.AssemItemName{PartIndex};
           % FaceRegionCell_of_ExtrudeSolid=PartGeomTable.ItemTableList{PartIndex}(1).Sketch.IdentifierName;
            % get ExtrudeSolid Number
           ExtrudeSolidName              =PartGeomTable.ItemTableList{PartIndex}(2).ExtrudeSolid;
           % ExtrudeSolidName      =ExtrudeSolidCell{PartIndex};
           % Bool ExtrudeSolid Face 
           Bool_CurExtrudeSolid        = contains(AllRefObjIDCell,ExtrudeSolidName)
           tempCell              = AllRefObjIDCell(Bool_CurExtrudeSolid);
           RefObjIDListTable     = RefObjListTable(Bool_CurExtrudeSolid,:)
      
           Bool_nonEdge          = ~contains(tempCell,'edge')
           tempCell              = tempCell(Bool_nonEdge);
           Bool_nonVertex        = ~contains(tempCell,'vertex')
           tempCell              = tempCell(Bool_nonVertex);
           Bool_nonlump          = ~contains(tempCell,'lump')
           tempCell              = tempCell(Bool_nonlump);
           %% FaceCell
           facesCell             = tempCell;
           % Face Extrude Bool
           Bool_4rdBracket       = ~contains(facesCell,'))))')
           facesCell             = facesCell(Bool_4rdBracket);
           % Back    % Back face-face
           Bool_3rdBracket       = ~contains(facesCell,')))')
           BackfacesCell         = facesCell(Bool_3rdBracket)
           % Front   % face-face-face
           FrontfaceCell         = facesCell(~Bool_3rdBracket)
           FaceExtrudeSet.BackfacesCell    =BackfacesCell;
           FaceExtrudeSet.FrontfaceCell    =FrontfaceCell;
           PartGeomTable.RefObjListTable(PartIndex) = {RefObjIDListTable};
           PartGeomTable.FaceExtrudeSet(PartIndex)  =  FaceExtrudeSet;    
    end
end
end