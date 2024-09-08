function setJmagNameByHier(app)
PJTPDir=app.GetProjectFolderPath();
[~,PJTName,~]=fileparts(PJTPDir);
app.SetProjectName(PJTName)
ModelList={'_REF','_SCL'}
StudyList={'_Load','_Noload'}
for ModelIndex=1:2
        ModelName=[PJTName,ModelList{ModelIndex}];
        ModelObj=app.GetModel(ModelIndex-1);
        ModelObj.SetName(ModelName)
        NumStudies=ModelObj.NumStudies;
    for StudyIndex=1:NumStudies
        StudyObj=ModelObj.GetStudy(StudyIndex-1);
        StudyName=[ModelName,StudyList{StudyIndex}];
        StudyObj.SetName(StudyName)
        NumStudies=app.NumStudies;
    end
end
