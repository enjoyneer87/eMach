function [StatorAssemRegionTable]=setGetGeomStatorNameNTable(geomApp)
    % StatorAssemRegionTable      =getRegionItemDataTable(StatorGeomAssemTable,'Stator',geomApp);
    % StatorAssemRegionTable = sortrows(StatorAssemRegionTable,'distanceRFromCenter','descend');

    % [StatorAssemRegionTable,StatorGeomArcTable,~]      =allocateSubSketchList2AssemRegionTable(StatorGeomAssemTable,StatorAssemRegionTable,geomApp);

    AssembleName='Stator';
    % StatorAssemRegionTable=getGeomAssembleTableWithHierData(geomApp,AssembleName);
    StatorAssemRegionTable=getGeomAssemTable(geomApp,AssembleName);
    [SlotUniqueValueStruct, StatorAssemRegionTable]=findConductorSlotinArea(StatorAssemRegionTable);

    %% Find StatorCore
    [maxValue,index]=max(StatorAssemRegionTable.Area(:));
    StatorAssemRegionTable.Name=StatorAssemRegionTable.sketchItemName;
    % StatorAssemRegionTable.Name{index}='StatorCore';
    % refObj=  StatorAssemRegionTable.ReferenceObj(index);
    % sel=getSelectRefObj(refObj,geomApp);
    % StatorCoreItem=sel.Item(0);
    % StatorCoreItemName=StatorCoreItem.GetName;
    if ~strcmp(StatorAssemRegionTable.Name{index},'StatorCore')
     StatorAssemRegionTable.Name{index}='StatorCore';
    end
    %% Conductor Setting
    if ~isempty(SlotUniqueValueStruct)
        if ~length(SlotUniqueValueStruct.Values)==1
            %% Slot
            nonStatorCore = (~strcmp(StatorAssemRegionTable.Name, 'StatorCore') & ~strcmp(StatorAssemRegionTable.Name, 'Housing'));
            StatorAssemRegionTable.Name(nonStatorCore) = {'Copper'};
            % changeNameGeomSketchAll(StatorAssemRegionTable,geomApp);
        else
            %% Other
            [otherSlotAreaGeomTable,StatorAssemRegionTable,StatorRegionTablePerType]=findnReNameOtherSlotArea(StatorAssemRegionTable);
            % changeNameGeomSketchAll(StatorAssemRegionTable,geomApp);
        end      
    end
    
    StatorAssemRegionTable.sketchItemName=StatorAssemRegionTable.Name;
    changeNameGeomSketchAll(StatorAssemRegionTable,geomApp);

    AssemTable = getGeomAssemItemListTable(geomApp);
    PartGeomTable=AssemTable(contains(AssemTable.Type,'Part'),:); 
    
    if isempty(PartGeomTable)  % only Sketch
        geomApp.GetDocument().GetAssembly().GetItem(AssembleName).CloseSketch();
        disp('2D')
    else 
        BoolPartIndex=contains(PartGeomTable.AssemItemName,AssembleName,"IgnoreCase",true);
        PartName=PartGeomTable.AssemItemName{BoolPartIndex};
        PartObj=geomApp.GetDocument().GetAssembly().GetItem(PartName);
        PartObj.ClosePart()
        disp('Sketch in 3D')
    end

    
end