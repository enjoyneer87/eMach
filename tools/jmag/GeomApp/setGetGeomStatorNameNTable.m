function [StatorAssemRegionTable,StatorGeomArcTable]=setGetGeomStatorNameNTable(StatorGeomAssemTable,geomApp)
    StatorAssemRegionTable      =getRegionItemDataTable(StatorGeomAssemTable,'Stator',geomApp);
    StatorAssemRegionTable = sortrows(StatorAssemRegionTable,'distanceRFromCenter','descend');
    [SlotUniqueValueStruct, StatorAssemRegionTable]=findConductorSlotinArea(StatorAssemRegionTable);

    [StatorAssemRegionTable,StatorGeomArcTable,~]      =allocateSubSketchList2AssemRegionTable(StatorGeomAssemTable,StatorAssemRegionTable,geomApp);

   
    %% Find StatorCore
    [maxValue,index]=max(StatorAssemRegionTable.Area(:));
    % StatorAssemRegionTable.Name{index}='StatorCore';
    % refObj=  StatorAssemRegionTable.ReferenceObj(index);
    % sel=getSelectRefObj(refObj,geomApp);
    % StatorCoreItem=sel.Item(0);
    % StatorCoreItemName=StatorCoreItem.GetName;
    if ~strcmp(StatorAssemRegionTable.Name{index},'StatorCore')
     StatorAssemRegionTable.Name{index}='StatorCore';
     changeNameGeomSketchAll(StatorAssemRegionTable,geomApp);
    end
    %% Conductor Setting
    if ~isempty(SlotUniqueValueStruct)
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
    else
        
    end
    geomApp.GetDocument().GetAssembly().GetItem('Stator').CloseSketch();

end