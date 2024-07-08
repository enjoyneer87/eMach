function  faceRegionTable=getGeomSketchTableWithHierData(geomApp,sketchObj)
%% 오래안걸림 -> RefObj 에서 Item으로 변경
% ReferenceObj   
% IdentifierName 
% Id   
sketchObj_NumItems=sketchObj.NumItems;
sketchItemListStruct=struct();
for SelIndex=1:sketchObj_NumItems
        sketchItemObj                                      =sketchObj.GetItem(int32(SelIndex-1));
        sketchItemListStruct(SelIndex).sketchItemObj       =sketchItemObj;
        sketchItemListStruct(SelIndex).sketchItemName      =sketchItemObj.GetName;
        sketchItemListStruct(SelIndex).Type                =sketchItemObj.GetScriptTypeName;
end   

%% Open Sketch and Select 4 Ref Obj
sketchObj.OpenSketch();
geomDocu=geomApp.GetDocument();
geomView=geomApp.View();
geomView.SetSelectionFilter(int32(3+4+8))
sel      =mkSelectionObj(geomApp,1);
NumSelections=sel.CountReferenceObject;
geomApp.Hide
AssemRefObjStruct=struct();
for SelIndex=1:NumSelections
        AssemRefObjStruct(SelIndex).ReferenceObj        =sel.GetReferenceObject(SelIndex-1);          
        AssemRefObjStruct(SelIndex).IdentifierName      =AssemRefObjStruct(SelIndex).ReferenceObj.GetIdentifier;
        AssemRefObjStruct(SelIndex).Id                  =AssemRefObjStruct(SelIndex).ReferenceObj.GetId;     
end

sel.Clear;

%% Table화
refObjTable                   =struct2table(AssemRefObjStruct);
sketchItemListTable           =struct2table(sketchItemListStruct);

%% faceRegion filter
faceRegionTable=sketchItemListTable(strcmp(sketchItemListTable.Type,'RegionItem'),:);
% faceRegionTable=AssembleTable(contains(AssembleTable.IdentifierName,'face'),:);
%% faceRegion Area
for SelIndex=1:height(faceRegionTable)
            refObj=geomDocu.CreateReferenceFromItem(faceRegionTable.sketchItemObj{SelIndex});       
            sel.AddReferenceObject(refObj);                           % Selection Object    -> 동작안되는것도 있는듯
            geomDocuVolManager            =geomDocu.GetVolumeCalculationManager();
            faceRegionTable.Area(SelIndex)=geomDocuVolManager.CalculateArea();
            selRefObj=sel.GetReferenceObject(0);        
            faceRegionTable.distanceRFromCenter(SelIndex)=getDistanceFromZero(selRefObj,geomApp);              
            sel.Clear
end

%% [RotorAssemRegionTable,RotorGeomArcTable]      =allocateSubSketchList2AssemRegionTable(RotorGeomAssembleTable,RotorAssemRegionTable,geomApp);
GeomArcTable          =getArcDataTable(sketchItemListTable);
GeomLineTable         =getLineDataTable(sketchItemListTable);
GeomArcTable   = sortrows(GeomArcTable,         'Angle','descend');
GeomLineTable  = sortrows(GeomLineTable,        'length','descend');
%% IdentifierName 추가
GeomArcTable       =addRefObj2AssemTable(GeomArcTable,geomApp);
GeomLineTable      =addRefObj2AssemTable(GeomLineTable,geomApp);
faceRegionTable    =addRefObj2AssemTable(faceRegionTable,geomApp);
sketchItemListTable      =addRefObj2AssemTable(sketchItemListTable,geomApp);
 
%% 찾을 대상 Region이름 추출
for RegionIndex=1:height(faceRegionTable)
    % 찾을 대상 Region 이름 추출
    clear SketchItemList
    faceItemName=erase(faceRegionTable.IdentifierName{RegionIndex},'faceregion(');
    faceItemName=erase(faceItemName,')');
    % 전체테이블에서 해당 RegionItem포함된 Index 추출
    faceItemIndex=find(contains(refObjTable.IdentifierName,faceItemName));
    FaceMatchedName=refObjTable.IdentifierName(faceItemIndex);

    edgeItemIndex=contains(FaceMatchedName,'edgeregion');
    edgeFaceMatchedName=FaceMatchedName(edgeItemIndex);

    %% ItemList
    SketchItemList=erase(edgeFaceMatchedName,['edgeregion(',faceItemName,'+']);
    SketchItemList=erase(SketchItemList,')');

    %%ArcTable
    TSketchArcNames=erase(GeomArcTable.IdentifierName,'edgeregion(');
    TSketchArcNames=erase(TSketchArcNames,')');
    MatchedArcTable=GeomArcTable((contains(TSketchArcNames,SketchItemList)),:);

    %%LineTable
    TSketchLineNames=erase(GeomLineTable.IdentifierName,'edgeregion(');
    TSketchLineNames=erase(TSketchLineNames,')');
    MatchedLineTable=GeomLineTable((contains(TSketchLineNames,SketchItemList)),:);

    %RegionList
    faceRegionTable.SketchList{RegionIndex}=    {MatchedArcTable,MatchedLineTable};
end
geomApp.Show
end
