function [StatorAssemRegionTable]=setGetGeomStatorNameNTable(geomApp)

%% Assemble Region Table
    AssembleName='Stator';
    StatorAssemRegionTable=getGeomAssemTable(geomApp,AssembleName);
%% check WireTemplate (NonRegion)
    WireTemplateObj=getWireTemplateObject(geomApp);
    %% Conductor
    [SlotUniqueValueStruct, StatorAssemRegionTable]=findConductorSlotinArea(StatorAssemRegionTable);
    % emptyRows = findEmptyRows(StatorAssemRegionTable, 'sketchItemObj');  
    % StatorAssemRegionTable=StatorAssemRegionTable(~emptyRows,:);
    %% Find StatorCore
    [maxValue,index]=max(StatorAssemRegionTable.Area(:));
    StatorAssemRegionTable.Name=StatorAssemRegionTable.sketchItemName;
    if ~strcmp(StatorAssemRegionTable.Name{index},'StatorCore')
     StatorAssemRegionTable.Name{index}='StatorCore';
    end

    %% WireTemplate이 없으면 Conductor Setting이나 Slot Setting
    if ~WireTemplateObj.IsValid
        %% Conductor Setting
        if ~isempty(SlotUniqueValueStruct)
            if ~length(SlotUniqueValueStruct.Values)==1
                %% Slot
                nonStatorCore = (~strcmp(StatorAssemRegionTable.Name, 'StatorCore') & ~strcmp(StatorAssemRegionTable.Name, 'Housing'));
                StatorAssemRegionTable.Name(nonStatorCore) = {'Copper'};
                % changeNameGeomSketchAll(StatorAssemRegionTable,geomApp);
            else %% Conductor
                %% Other
                [otherSlotAreaGeomTable,StatorAssemRegionTable,StatorRegionTablePerType]=findnReNameOtherSlotArea(StatorAssemRegionTable);
                % changeNameGeomSketchAll(StatorAssemRegionTable,geomApp);        
            end      
        end
    end
    %%  add wireTable 2 RegionTable
    if WireTemplateObj.IsValid
    newVarNames={'sketchItemObj','sketchItemName','Type'};   
    WireTable = mkNewTablewithTable(StatorAssemRegionTable, newVarNames, WireTemplateObj,WireTemplateObj.GetName,WireTemplateObj.GetScriptTypeName);
    WireTable.Name=WireTable.sketchItemName;
    StatorAssemRegionTable =[StatorAssemRegionTable;WireTable];
    end
    %%  change Name 
    StatorAssemRegionTable.sketchItemName=StatorAssemRegionTable.Name;
    changeNameGeomSketchAll(StatorAssemRegionTable,geomApp);
    
    %% check 3D or 2D
    AssemTable = getGeomAssemItemListTable(geomApp);
    PartGeomTable=AssemTable(contains(AssemTable.Type,'Part'),:); 
    
    if isempty(PartGeomTable)  % only Sketch
        AssemNameInGeomApp  = AssemTable.AssemItemName(contains(AssemTable.AssemItemName,AssembleName,"IgnoreCase",true));       
        if length(AssemNameInGeomApp)==1
        AssembleName = AssemNameInGeomApp{:};
        end
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