function setWireRegion(app,firstSlotWirePartsTable,ConductorNumber)
    Model=app.GetCurrentModel;
    Study=app.GetCurrentStudy;
if nargin<3
    WireTemplateObj=getWireTemplateObject(app);
    if WireTemplateObj.IsValid
        WireTemplateName=WireTemplateObj.GetName;
        ConductorNumber=WireTemplateObj.GetProperty("WireCount");
    end
end
    WindingRegionObj=devmkWindingRegion(app);
    % Model=app.GetCurrentModel;
    % Study=app.GetCurrentStudy;
   % Study.CreateWindingRegion("HairPinWave",1)  % Coil Template
    % WindingRegionObj=Study.CreateWindingRegion("HairPinWave",0);  % Wire (Geometry) Template
    % Study.CreateWinding("HairPinWave")
    % equationStruct=getJmagDesignerEquationStruct(app);
    % equationStruct.object
    % WindingRegionObj.IsWireTemplateRegion


    %% GetWindingRegion WindingRegion object는 매번 호출해야됨 아직 matlab으로 객체인식이 잘안됨
    % Study.GetWindingRegion("HairPinWave");
    Study.GetWindingRegion("HairPinWave").SetOriginXYZ(0, 0, 0);
    % WindingRegionObj.SetIsWireTemplateRegion(1);   
    % WindingRegionObj.SetIsWireTemplateRegion({'True'})
    % WindingRegionObj.Is
    % Study.GetWindingRegion("HairPinWave").SetIsWireTemplateRegion(1);   
    

    for RegionIndex=1:double(ConductorNumber)
        CoilRegionName=['Coil Region ',num2str(RegionIndex)];
        Study.GetWindingRegion("HairPinWave").AddCoilRegion(CoilRegionName);
        sel1 = Study.GetWindingRegion("HairPinWave").GetSelection(RegionIndex-1);
        sel1.SelectPart(double(firstSlotWirePartsTable.partIndex(RegionIndex)))
        Study.GetWindingRegion("HairPinWave").AddSelected(RegionIndex-1, sel1)
        sel1.Clear
    end
    % a=Study.GetWindingRegion(0)
    % Study.GetWindingRegion("HairPinWave").IsWireTemplateRegion
    % Study.GetWindingRegion("HairPinWave").SetIsWireTemplateRegion(0);   

    % Study.GetWindingRegion("HairPinWave").SetSlots("Slots")
    % a=Study.GetWindingRegion("HairPinWave")
    % a.IsValid
    % a.IsWireTemplateRegion
    % a.SetPoles(8)
    % a.SetSlots(48)
    % Study.GetWindingRegion("HairPinWave").SetSlots("48")    
    % WindingRegionObj.SetPoles("Poles")
    % % if 
    pyrunfile("pySlotPoleWireTemplate.py")

    Study.GetWindingRegion("HairPinWave").NumSlots
    Study.GetWindingRegion("HairPinWave").NumPoles

end