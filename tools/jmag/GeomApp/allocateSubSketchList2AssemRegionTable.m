% sketchList로부터
% AssemRegion으로부터 SketchList가져오는 For문 돌리기

% StatorAssemRegionTable

function [StatorAssemRegionTable,StatorGeomArcTable,StatorGeomLineTable]=allocateSubSketchList2AssemRegionTable(StatorGeomAssemTable,StatorAssemRegionTable,geomApp)

%% check App or Geometry Editor
    AppDir=geomApp.GetAppDir;
    AppDirStr=split(AppDir,'/');
    if ~strcmp(AppDirStr{end},'Modeller')
        geomApp=geomApp.CreateGeometryEditor(0);
        % geomApp.Show
    end

StatorGeomArcTable          =getArcDataTable(StatorGeomAssemTable,geomApp);
StatorGeomLineTable         =getLineDataTable(StatorGeomAssemTable,geomApp);

StatorGeomArcTable   = sortrows(StatorGeomArcTable,         'Angle','descend');
StatorGeomLineTable  = sortrows(StatorGeomLineTable,        'length','descend');

for RegionIndex=1:height(StatorAssemRegionTable)
    % 찾을 대상 Region 이름 추출
    clear SketchItemList
    faceItemName=erase(StatorAssemRegionTable.IdentifierName{RegionIndex},'faceregion(');
    faceItemName=erase(faceItemName,')');
    % 전체테이블에서 해당 RegionItem포함된 Index 추출
    faceItemIndex=find(contains(StatorGeomAssemTable.IdentifierName,faceItemName));
    
    edgeItemIndex=contains(StatorGeomAssemTable.IdentifierName(faceItemIndex),'edgeregion');
    skechItemIndex=faceItemIndex(edgeItemIndex);

    %% ItemList
    SketchItemList=StatorGeomAssemTable.IdentifierName(skechItemIndex);
    SketchItemList=erase(SketchItemList,['edgeregion(',faceItemName,'+']);
    SketchItemList=erase(SketchItemList,')');

    %%ArcTable
    TSketchArcNames=erase(StatorGeomArcTable.IdentifierName,'edgeregion(');
    TSketchArcNames=erase(TSketchArcNames,')');
    MatchedArcTable=StatorGeomArcTable(find(contains(TSketchArcNames,SketchItemList)),:);

    %%LineTable
    TSketchLineNames=erase(StatorGeomLineTable.IdentifierName,'edgeregion(');
    TSketchLineNames=erase(TSketchLineNames,')');
    MatchedLineTable=StatorGeomLineTable(find(contains(TSketchLineNames,SketchItemList)),:);

    %RegionList
    StatorAssemRegionTable.SketchList{RegionIndex}=    {MatchedArcTable,MatchedLineTable};
    % contains(StatorGeomAssemTable.IdentifierName(faceIteMatchedArcTablemIndex),'Line')
    % contains(StatorGeomAssemTable.IdentifierName(faceItemIndex),'Arc')
    % all(~contains(StatorGeomAssemTable.IdentifierName(faceItemIndex),'Boolean'))
    



end

end