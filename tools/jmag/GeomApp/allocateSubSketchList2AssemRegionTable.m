% sketchList로부터
% AssemRegion으로부터 SketchList가져오는 For문 돌리기

% StatorAssemRegionTable

function [AssemRegionTable,GeomArcTable,GeomLineTable]=allocateSubSketchList2AssemRegionTable(GeomAssemTable,AssemRegionTable,geomApp)

%% check App or Geometry Editor
    AppDir=geomApp.GetAppDir;
    AppDirStr=split(AppDir,'/');
    if ~strcmp(AppDirStr{end},'Modeller')
        geomApp=geomApp.CreateGeometryEditor(0);
        % geomApp.Show
    end

GeomArcTable          =getArcDataTable(GeomAssemTable,geomApp);
GeomLineTable         =getLineDataTable(GeomAssemTable,geomApp);

GeomArcTable   = sortrows(GeomArcTable,         'Angle','descend');
GeomLineTable  = sortrows(GeomLineTable,        'length','descend');

for RegionIndex=1:height(AssemRegionTable)
    % 찾을 대상 Region 이름 추출
    clear SketchItemList
    faceItemName=erase(AssemRegionTable.IdentifierName{RegionIndex},'faceregion(');
    faceItemName=erase(faceItemName,')');
    % 전체테이블에서 해당 RegionItem포함된 Index 추출
    faceItemIndex=find(contains(GeomAssemTable.IdentifierName,faceItemName));
    
    edgeItemIndex=contains(GeomAssemTable.IdentifierName(faceItemIndex),'edgeregion');
    skechItemIndex=faceItemIndex(edgeItemIndex);

    %% ItemList
    SketchItemList=GeomAssemTable.IdentifierName(skechItemIndex);
    SketchItemList=erase(SketchItemList,['edgeregion(',faceItemName,'+']);
    SketchItemList=erase(SketchItemList,')');

    %%ArcTable
    TSketchArcNames=erase(GeomArcTable.IdentifierName,'edgeregion(');
    TSketchArcNames=erase(TSketchArcNames,')');
    MatchedArcTable=GeomArcTable(contains(TSketchArcNames,SketchItemList),:);

    %%LineTable
    TSketchLineNames=erase(GeomLineTable.IdentifierName,'edgeregion(');
    TSketchLineNames=erase(TSketchLineNames,')');
    MatchedLineTable=GeomLineTable(contains(TSketchLineNames,SketchItemList),:);

    %RegionList
    AssemRegionTable.SketchList{RegionIndex}=    {MatchedArcTable,MatchedLineTable};
    % contains(StatorGeomAssemTable.IdentifierName(faceIteMatchedArcTablemIndex),'Line')
    % contains(StatorGeomAssemTable.IdentifierName(faceItemIndex),'Arc')
    % all(~contains(StatorGeomAssemTable.IdentifierName(faceItemIndex),'Boolean'))
    



end

end