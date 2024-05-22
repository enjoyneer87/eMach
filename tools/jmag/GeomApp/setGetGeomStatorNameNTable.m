function StatorAssemRegionTable=setGetGeomStatorNameNTable(StatorGeomAssemTable,geomApp)

    StatorAssemRegionTable      =getRegionItemDataTable(StatorGeomAssemTable,'Stator',geomApp);
    StatorAssemRegionTable      =allocateSubSketchList2AssemRegionTable(StatorGeomAssemTable,StatorAssemRegionTable,geomApp);

    StatorAssemRegionTable = sortrows(StatorAssemRegionTable,'distanceRFromCenter','descend');

    %% Find StatorCore
    [maxValue,index]=max(StatorAssemRegionTable.Area(:));
    refObj=  StatorAssemRegionTable.ReferenceObj(index);
    sel=getSelectRefObj(refObj,geomApp);
    StatorCoreItem=sel.Item(0);
    StatorCoreItem.IsValid
    StatorCoreItemName=StatorCoreItem.GetName;
    if ~strcmp(StatorCoreItemName,'StatorCore')
     StatorAssemRegionTable.Name{index}='StatorCore';
    end
    %% Conductor Setting
    [SlotUniqueValueStruct, StatorAssemRegionTable]=findConductorSlotinArea(StatorAssemRegionTable);
    if ~length(SlotUniqueValueStruct.Values)==1
        %% Slot
        nonStatorCore = (~strcmp(StatorAssemRegionTable.Name, 'StatorCore') & ~strcmp(StatorAssemRegionTable.Name, 'Housing'));
        StatorAssemRegionTable.Name(nonStatorCore) = {'Copper'};
        changeNameGeomSketchAll(StatorAssemRegionTable,geomApp);
    else
        %% Other
        [otherSlotAreaGeomTable,StatorAssemRegionTable,StatorRegionTablePerType]=findnReNameOtherSlotArea(StatorAssemRegionTable);
        changeNameGeomSketchAll(StatorAssemRegionTable,geomApp);
    end

end