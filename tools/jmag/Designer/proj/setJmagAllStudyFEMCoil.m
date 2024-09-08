function setJmagAllStudyFEMCoil(app)
NumModels=app.NumModels;

for ModelIndex=1:NumModels
    ModelObj        =app.GetModel(ModelIndex-1);
    NumStudies      =ModelObj.NumStudies;
    for StudyIndex=1:NumStudies
        PartStruct       = getJMAGDesignerPartStruct(app);
        PartStructByType = convertJmagPartStructByType(PartStruct);
        singleConductorArea=uniquetol(PartStructByType.SlotTable.Area,1e-5);
        % Coil Setting
        isConductor=0;
        curStudyObj=ModelObj.GetStudy(StudyIndex-1);
        app.SetCurrentStudy(curStudyObj.GetName)
        setJMAGFEMCoil(curStudyObj,PartStructByType); 
    end
end
