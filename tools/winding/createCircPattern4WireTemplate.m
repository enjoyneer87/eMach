function createCircPattern4WireTemplate(MachineData,app)

    Poles              =MachineData.Poles               ;
    StatorOneSlotAngle =MachineData.StatorOneSlotAngle  ;
    PhaseNumber        =MachineData.PhaseNumber         ;
    NSPP               =MachineData.NSPP                ;
    q                  =MachineData.q                   ;
    slots              =MachineData.slots               ;

    geomApp=app.CreateGeometryEditor(0);

    %%
    WireTemplateRefObj  =getWireTemplateRefObject(app);
    WireTemplateName    =WireTemplateRefObj.GetIdentifier;

    Item=geomApp.GetDocument().GetAssembly().GetItem("Stator").CreateRegionCircularPattern();
    Item.SetProperty("Feature",WireTemplateName)
    Item.SetProperty('CenterType','DefaultOrigin')
    Item.SetAngle(360/Poles/(NSPP*PhaseNumber))
    Item.SetInstance((NSPP*PhaseNumber))

end