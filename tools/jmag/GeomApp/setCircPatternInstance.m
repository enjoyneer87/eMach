function setCircPatternInstance(ItemName,copyInstanceQunatity,geomApp)

geomAssem=geomApp.GetDocument().GetAssembly();
geomItem=geomAssem.GetItem(ItemName);
geomItem.IsValid
GetScriptTypeName1=geomItem.GetScriptTypeName;

%% 파트 아이템이면 스케치아이템으로 반환
if strcmp(GetScriptTypeName1,'Part')
    NumItems=geomItem.NumItems;
    geomItem.OpenPart()
    geomItem=geomItem.GetItem(ItemName);
    GetScriptTypeName2=geomItem.GetScriptTypeName;
elseif strcmp(GetScriptTypeName1,'Sketch')
    geomItem.OpenSketch()
end

%% sketch Item 목록 구조체로가져오기
if strcmp(GetScriptTypeName2,'Sketch')
    SketchNumItems=geomItem.NumItems;
    geomItem.OpenSketch()
    for ItemIndex=1:SketchNumItems
    SketchItemStruct(ItemIndex).SketchItemObj=geomItem.GetItem(int32(ItemIndex-1));
    SketchItemObj=SketchItemStruct(ItemIndex).SketchItemObj;
    isobjValid=SketchItemObj.IsValid;
        if isobjValid==1
            SketchItemStruct(ItemIndex).SketchItemName=SketchItemObj.GetName();
            SketchItemName{ItemIndex}=SketchItemObj.GetName();
            SketchItemStruct(ItemIndex).ItemIndex=ItemIndex-1;
        end
    end
end

%% PatterObj 찾기
PatternItemIndex=find(contains(SketchItemName,'pattern','IgnoreCase',true));
PatternItemName=SketchItemName{PatternItemIndex};
PatterObj=SketchItemStruct(PatternItemIndex).SketchItemObj;

%% 패턴 개수 조정
if strcmp(PatterObj.GetName,PatternItemName)
PatterObj.SetProperty("Instance", int32(copyInstanceQunatity))
end

end

