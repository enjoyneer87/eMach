function setWireRegion(StudyObj,firstSlotWirePartsTable,ConductorNumber)
if contains(class(StudyObj),'designer')
    app=StudyObj;
    NumModels=app.NumModels;
    NumStudies=app.NumStudies;
    if NumStudies==1 && NumModels==1
    % Model=app.GetModel(0);
    % Model.GetName;
    Study=app.GetModel(0).GetStudy(0);
    % if Study.IsValid==1
    Study.GetName;
    else 
    disp('study와 모델이 여러개입니다.')
    end
else
    app  = callJmag;
    Study=StudyObj;
end
    % end
    % Model=app.GetCurrentModel;
    % Study=app.GetCurrentStudy;
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
    NumWindingRegions=Study.NumWindingRegions;
    WindingRegion=Study.GetWindingRegion(0);
    WindingRegion.IsWireTemplateRegion
    NameWindingRegion=WindingRegion.GetName;
    Study.GetWindingRegion(NameWindingRegion).IsWireTemplateRegion
    Study.GetWindingRegion(NameWindingRegion).SetIsWireTemplateRegion(true);   

    if WindingRegion.IsValid==1
    Model=app.GetCurrentModel;
    SLOTSEq=Model.GetEquation("SLOTS");
    SLOTS=int32(str2double(SLOTSEq.GetExpression));
    POLEEq=Model.GetEquation("POLES");
    POLES=int32(str2double(POLEEq.GetExpression));
    WindingRegion.SetPoles(POLES);
    WindingRegion.SetSlots(SLOTS);
    end
    % a=Study.GetWindingRegion("HairPinWave")
    % a.IsValid
    % a.IsWireTemplateRegion
    % a.SetPoles(8)
    % a.SetSlots(48)
    % Study.GetWindingRegion("HairPinWave").SetSlots("Slots")    
    % WindingRegionObj.SetPoles("Poles")
    % % if 
    % pyrunfile("pySlotPoleWireTemplate.py")
    % 
    % WindingRegion.NumSlots
    % WindingRegion.NumPoles
end