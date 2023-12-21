function createCircPattern4StatorCore(MachineData,StatorGeomAssemTable,app)

    Poles              =MachineData.Poles               ;
    StatorOneSlotAngle =MachineData.StatorOneSlotAngle  ;
    PhaseNumber        =MachineData.PhaseNumber         ;
    NSPP               =MachineData.NSPP                ;
    q                  =MachineData.q                   ;
    slots              =MachineData.slots               ;

    geomApp=app.CreateGeometryEditor(0);

    %%
    STcoreIndex=contains(StatorGeomAssemTable.Name,'StatorCore');
    StatorCoreAssemTable=StatorGeomAssemTable(STcoreIndex,:);
    geomApp.GetDocument().GetAssembly().GetItem("Stator").OpenSketch()
    Item=geomApp.GetDocument().GetAssembly().GetItem("Stator").CreateRegionCircularPattern();
    Item.GetName
    Item.SetProperty("Merge", 1)
    Item.SetRegionList(StatorCoreAssemTable.IdentifierName{:})
    Item.SetProperty('CenterType','DefaultOrigin')
    Item.SetAngle(360/Poles/(NSPP*PhaseNumber))

    if NSPP<1
    Item.SetInstance(360/StatorOneSlotAngle)
    else
    Item.SetInstance(NSPP*PhaseNumber)
    end
    Item.SetName('StatorCore')

end