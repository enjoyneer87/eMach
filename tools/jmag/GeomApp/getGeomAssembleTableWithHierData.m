function faceRegionTable=getGeomAssembleTableWithHierData(geomApp,AssembleName)

% 3D GeomApp
    % 3D > 2D > sel 
% 2D 만동작 > 3d는 getGeomAssemTabled에서 실행 with getGeomSketchTableWithHierData
%% Obj Call
% app=callJmag
% Model3d=app.GetCurrentModel
% Model3d.RestoreCadLink
% geomApp=app.CreateGeometryEditor(0);
geomDocu=geomApp.GetDocument();
geomAssem=geomApp.GetDocument().GetAssembly();
geomView=geomApp.View();

%% 3D Check
% ItemStruct=struct();
% NumItems=geomAssem.NumItems;
% for ItemIndex=1:NumItems
% ItemStruct.ItemObj{ItemIndex}=geomAssem.GetItem(int32(ItemIndex-1));
% if ItemStruct.ItemObj{ItemIndex}.IsValid
%     ItemStruct.ItemName{ItemIndex}=ItemStruct.ItemObj{ItemIndex}.GetName();
%     ItemStruct.Numteims{ItemIndex}=ItemStruct.ItemObj{ItemIndex}.NumItems;
%     ItemStruct.Type{ItemIndex}=ItemStruct.ItemObj{ItemIndex}.GetScriptTypeName;
% end
% end
%% [WC]

geomAssem.GetItem(AssembleName).OpenSketch();
geomView.SetSelectionFilter(int32(3+4+8))
sel      =mkSelectionObj(geomApp,1);
NumSelections=sel.CountReferenceObject;
% geomApp.Hide
AssemTable = getGeomAssemItemListTable(geomApp);
AssemItemObj=AssemTable.AssemItem(contains(AssemTable.AssemItemName,AssembleName));
SketchTable=getGeomObjItemListTable(AssemItemObj);
AssemObjNumItems=AssemItemObj.NumItems;
%% 오래안걸림 -> RefObj 에서 Item으로 변경
% ReferenceObj   
% IdentifierName 
% Id   
AssemObjStruct=struct();
for SelIndex=1:AssemObjNumItems
        sketchItemObj                                =AssemItemObj.GetItem(int32(SelIndex-1));
        AssemObjStruct(SelIndex).sketchItemObj       =sketchItemObj;
        AssemObjStruct(SelIndex).sketchItemName      =sketchItemObj.GetName;
        AssemObjStruct(SelIndex).Type                =sketchItemObj.GetScriptTypeName;
end   
%% Selection
for SelIndex=1:NumSelections
        AssemRefObjStruct(SelIndex).ReferenceObj        =sel.GetReferenceObject(SelIndex-1);          
        AssemRefObjStruct(SelIndex).IdentifierName      =AssemRefObjStruct(SelIndex).ReferenceObj.GetIdentifier;
        AssemRefObjStruct(SelIndex).Id                  =AssemRefObjStruct(SelIndex).ReferenceObj.GetId;     
end
sel.Clear;

%% Table화
refObjTable                 =struct2table(AssemRefObjStruct);
AssembleItemTable           =struct2table(AssemObjStruct);

%% faceRegion filter
faceRegionTable=AssembleItemTable(strcmp(AssembleItemTable.Type,'RegionItem'),:);
% faceRegionTable=AssembleTable(contains(AssembleTable.IdentifierName,'face'),:);
%% faceRegion Area
for SelIndex=1:height(faceRegionTable)
            % refObj=faceRegionTable.ReferenceObj(SelIndex);
            refObj=geomDocu.CreateReferenceFromItem(faceRegionTable.sketchItemObj{SelIndex});       
            % sel.Add(faceRegionTable.sketchItemObj{SelIndex})
            sel.AddReferenceObject(refObj);                           % Selection Object    -> 동작안되는것도 있는듯
            geomDocuVolManager            =geomDocu.GetVolumeCalculationManager();
            faceRegionTable.Area(SelIndex)=geomDocuVolManager.CalculateArea();
            selRefObj=sel.GetReferenceObject(0);        
            faceRegionTable.distanceRFromCenter(SelIndex)=getDistanceFromZero(selRefObj,geomApp);     
            % faceRegionTable.distanceRFromCenter(SelIndex)=getDistanceFromZero(refObj,geomApp);
            % if sel.Count~=0
            %% Object
            % CurItem=sel.Item(0)                                      ; % get sketch Item
         %    CurItem=refObj;                                    ; % get sketch Item
         % 
         % if CurItem.IsValid==1            
         %    faceRegionTable.Name{SelIndex}             =CurItem.GetName;
         %    faceRegionTable.Type{SelIndex}             =CurItem.GetScriptTypeName;
         % end
         sel.Clear
end

%% [RotorAssemRegionTable,RotorGeomArcTable]      =allocateSubSketchList2AssemRegionTable(RotorGeomAssembleTable,RotorAssemRegionTable,geomApp);
% GeomArcTable          =getArcDataTable(AssembleItemTable,geomApp);
GeomArcTable          =getArcDataTable(AssembleItemTable);
GeomLineTable         =getLineDataTable(AssembleItemTable);

% GeomLineTable         =getLineDataTable(AssembleItemTable,geomApp);
GeomArcTable   = sortrows(GeomArcTable,         'Angle','descend');
GeomLineTable  = sortrows(GeomLineTable,        'length','descend');
%% IdentifierName 추가
GeomArcTable            =addRefObj2AssemTable(GeomArcTable,geomApp);
GeomLineTable           =addRefObj2AssemTable(GeomLineTable,geomApp);
faceRegionTable         =addRefObj2AssemTable(faceRegionTable,geomApp);
AssembleItemTable       =addRefObj2AssemTable(AssembleItemTable,geomApp);
 
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



end