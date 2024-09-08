function [JprojStruct,NumModels,ModelStudy] = getJProjHierModelStudyTable(app)
    % 앱에서 모델 수 가져오기
    NumModels = app.NumModels;
    % JprojStruct 초기화
    JprojStruct = struct();
    ModelObj =cell(NumModels,1);
    ModelName=cell(NumModels,1);

    % 각 모델에 대해 반복
    for ModelIndex = 1:NumModels
        % 모델 객체 가져오기
        tempModelObj= app.GetModel(ModelIndex-1);
        ModelName{ModelIndex} = tempModelObj.GetName;
        NumStudies = tempModelObj.NumStudies; 
        CurModelStudyTable=cell2table(cell(NumStudies,3));
        CurModelStudyTable.Properties.VariableNames={'NumCases','StudyObj','StudyName'};
        for StudyIndex = 1:NumStudies
            CurModelStudyTable.NumCases{StudyIndex}=tempModelObj.GetStudy(StudyIndex-1).GetDesignTable().NumCases();
            CurModelStudyTable.StudyObj{StudyIndex}=tempModelObj.GetStudy(StudyIndex-1);
            CurModelStudyTable.StudyName(StudyIndex)={tempModelObj.GetStudy(StudyIndex-1).GetName};
        end
            JprojStruct.([ModelName{ModelIndex},'Table'])=CurModelStudyTable;
            ModelStudy{ModelIndex}=NumStudies;
    end
end
