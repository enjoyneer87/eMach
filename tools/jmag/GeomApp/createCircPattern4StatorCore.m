function createCircPattern4StatorCore(MachineData,StatorAssemRegionTable,geomApp)
%% check App or Geometry Editor
    AppDir=geomApp.GetAppDir;
    AppDirStr=split(AppDir,'/');
    if ~strcmp(AppDirStr{end},'Modeller')
    geomApp=geomApp.CreateGeometryEditor(0);
    geomApp.visible
    end

%% MachineData
    Poles              =MachineData.Poles               ;
    StatorOneSlotAngle =MachineData.StatorOneSlotAngle  ;
    PhaseNumber        =MachineData.PhaseNumber         ;
    NSPP               =MachineData.NSPP                ;
    q                  =MachineData.q                   ;
    slots              =MachineData.slots               ;

    %% CoreIndex
    STcoreIndex=contains(StatorAssemRegionTable.Name,'StatorCore');
    % STcoreIndex=contains(StatorGeomAssemTable(:,"Name"){:},'StatorCore');

    %%
    StatorCoreAssemRegionTable=StatorAssemRegionTable(STcoreIndex,:);
    SketchItem=geomApp.GetDocument().GetAssembly().GetItem("Stator");
    SketchItem.OpenSketch()
    circItemObj=SketchItem.CreateRegionCircularPattern();
    circItemObj.SetProperty('CenterType','DefaultOrigin')
    circItemObj.SetAngle(360/Poles/(NSPP*PhaseNumber))
    if NSPP<1
    circItemObj.SetInstance(360/StatorOneSlotAngle)
    else
    circItemObj.SetInstance(NSPP*PhaseNumber)
    end
    circItemObj.SetName('StatorCore')
    % Item.GetName
    circItemObj.SetProperty("Merge", 1)
    circItemObj.SetRegionList(StatorCoreAssemRegionTable.IdentifierName{:})

end