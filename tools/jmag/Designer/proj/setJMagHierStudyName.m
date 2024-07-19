function Jproj=setJMagHierStudyName(app)
%% Study 이름에 모델이름 추가
Jproj=getJProjHier(app);
ModelNameFields=fieldnames(Jproj);

for ModelIndex=1:height(ModelNameFields)
    ModelName=ModelNameFields{ModelIndex};
    Model=app.GetModel(ModelName);
    StudyNameFields=fieldnames(Jproj.(ModelName));
    for StudyIndex=1:Model.NumStudies
        StudyName=StudyNameFields{StudyIndex};
        if ~contains(StudyName,ModelName)
        HieredStudyName=[StudyName,'_of_',ModelName];
        StudyObj=Model.GetStudy(StudyName);
        StudyObj.SetName(HieredStudyName)
        Jproj.(ModelName) = renameField(Jproj.(ModelName), StudyName, HieredStudyName);
        end
    end
end
end
