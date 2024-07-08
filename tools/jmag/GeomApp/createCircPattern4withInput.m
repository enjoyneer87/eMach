function createCircPattern4withInput(MachineData,AssemRegionTable,AreaName,geomApp,checkWithIDname)
%% check App or Geometry Editor
    AppDir=geomApp.GetAppDir;
    AppDirStr=split(AppDir,'/');
    if ~strcmp(AppDirStr{end},'Modeller')
    geomApp=geomApp.CreateGeometryEditor(0);
    geomApp.visible
    end

    Poles              =MachineData.Poles               ;
    StatorOneSlotAngle =MachineData.StatorOneSlotAngle  ;
    PhaseNumber        =MachineData.PhaseNumber         ;
    NSPP               =MachineData.NSPP                ;
    q                  =MachineData.q                   ;
    slots              =MachineData.slots               ;
    RotorOnePoleAngle=360/Poles;
    % Poles       = 360/RotorOnePoleAngle;

    %% Check with IdenfierName

    otherAreaIndex=contains(AssemRegionTable.IdentifierName,AreaName);

    %% Check With Name
    if nargin<5
    otherAreaIndex=contains(AssemRegionTable.Name,AreaName);
    end
    otherAreaAssemTable=AssemRegionTable(otherAreaIndex,:);
    %% createPattern

    for IdIndex=1:height(otherAreaAssemTable)
        SketchItem=geomApp.GetDocument().GetAssembly().GetItem("Stator");
        SketchItem.OpenSketch()
        circItemObj=SketchItem.CreateRegionCircularPattern();
        % Item.SetRegionList(otherAreaAssemTable.IdentifierName{IdIndex})
        % Item.SetRegionList((otherAreaAssemTable.Id(:)))
        circItemObj.SetProperty('Region',otherAreaAssemTable.IdentifierName{IdIndex})
        circItemObj.SetProperty('CenterType','DefaultOrigin')
        circItemObj.SetAngle(360/Poles/(NSPP*PhaseNumber))
    
        if NSPP<1
        circItemObj.SetInstance(int32(360/StatorOneSlotAngle))
        else
        circItemObj.SetInstance(int32(NSPP*PhaseNumber));
        end
        AreaName=otherAreaAssemTable.sketchItemName{IdIndex};
        circItemObj.SetName(AreaName);
        circItemObj.SetProperty("Merge", 1)

    end
    
end