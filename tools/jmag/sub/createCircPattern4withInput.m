function createCircPattern4withInput(MachineData,StatorGeomAssemTable,AreaName,app,checkWithIDname)

    Poles              =MachineData.Poles               ;
    StatorOneSlotAngle =MachineData.StatorOneSlotAngle  ;
    PhaseNumber        =MachineData.PhaseNumber         ;
    NSPP               =MachineData.NSPP                ;
    q                  =MachineData.q                   ;
    slots              =MachineData.slots               ;
    RotorOnePoleAngle=360/Poles;
    % Poles       = 360/RotorOnePoleAngle;
    geomApp=app.CreateGeometryEditor(0);

   


    %% Check with IdenfierName

    otherAreaIndex=contains(StatorGeomAssemTable.IdentifierName,AreaName);

    %% Check With Name
    if nargin<5
    otherAreaIndex=contains(StatorGeomAssemTable.Name,AreaName);
    end
    otherAreaAssemTable=StatorGeomAssemTable(otherAreaIndex,:);
    %% createPattern

    for IdIndex=1:height(otherAreaAssemTable)
        Item=geomApp.GetDocument().GetAssembly().GetItem("Stator").CreateRegionCircularPattern();
        % Item.SetRegionList(otherAreaAssemTable.IdentifierName{IdIndex})
        % Item.SetRegionList((otherAreaAssemTable.Id(:)))
        Item.SetProperty('Region',otherAreaAssemTable.IdentifierName{IdIndex})
        Item.SetProperty('CenterType','DefaultOrigin')
        Item.SetAngle(360/Poles/(NSPP*PhaseNumber))
    
        if NSPP<1
        Item.SetInstance(360/StatorOneSlotAngle)
        else
        Item.SetInstance(NSPP*PhaseNumber)
        end
        Item.SetName(AreaName)
    end
    
end