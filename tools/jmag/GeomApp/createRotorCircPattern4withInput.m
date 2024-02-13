function createRotorCircPattern4withInput(MachineData,RotorGeomAssembleTable,AreaName,app,checkWithIDname)

    Poles              =MachineData.Poles               ;
    StatorOneSlotAngle =MachineData.StatorOneSlotAngle  ;
    RotorOnePoleAngle   =MachineData.RotorOnePoleAngle   ;               
    PhaseNumber        =MachineData.PhaseNumber         ;
    NSPP               =MachineData.NSPP                ;
    q                  =MachineData.q                   ;
    slots              =MachineData.slots               ;

    geomApp=app.CreateGeometryEditor(0);

   


    %% Check with IdenfierName

    otherAreaIndex=contains(RotorGeomAssembleTable.IdentifierName,AreaName);

    %% Check With Name
    if nargin<5
    otherAreaIndex=contains(RotorGeomAssembleTable.Name,AreaName);
    end
    otherAreaAssemTable=RotorGeomAssembleTable(otherAreaIndex,:);
    %% createPattern

    for IdIndex=1:height(otherAreaAssemTable)
        geomApp.GetDocument().GetAssembly().GetItem("Rotor").OpenSketch()
        Item=geomApp.GetDocument().GetAssembly().GetItem("Rotor").CreateRegionCircularPattern();
        % Item.SetRegionList(otherAreaAssemTable.IdentifierName{IdIndex})
        % Item.SetRegionList((otherAreaAssemTable.Id(:)))
        Item.SetProperty('Region',otherAreaAssemTable.IdentifierName{IdIndex})
        Item.SetProperty('CenterType','DefaultOrigin')
        Item.SetAngle(RotorOnePoleAngle)
    
        if NSPP<1
        Item.SetInstance(360/RotorOnePoleAngle)
        else
        Item.SetInstance(NSPP*PhaseNumber)
        end
        Item.SetName(AreaName)
    end
    
end