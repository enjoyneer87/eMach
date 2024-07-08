function    TargetTableRefObjList=findRefObjFromRegionTablePerType(RegionTablePerType,RegionList2Delete)

FieldNames=fieldnames(RegionTablePerType);
TargetTableRefObjList=[];
for RegionIndex=1:length(RegionList2Delete)
    for TableIndex=1:length(FieldNames)
        TargetRegion=RegionList2Delete{RegionIndex};
        TargetTable=RegionTablePerType.(FieldNames{TableIndex});
        if ~isempty(TargetTable)
        RegionNameList=TargetTable.Name;
        TargetIndex=find(strcmp(RegionNameList,TargetRegion));
            if ~isempty(TargetIndex)
                TargetTableRefObj={TargetTable.ReferenceObj(TargetIndex)};
                TargetTableRefObjList=[TargetTableRefObjList;TargetTableRefObj];
            end
        end
    end
end