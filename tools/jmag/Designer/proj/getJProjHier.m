function JprojStruct = getJProjHier(app)
    % 앱에서 모델 수 가져오기
    NumModels = app.NumModels;
    
    % JprojStruct 초기화
    JprojStruct = struct();
    
    % 각 모델에 대해 반복
    for ModelIndex = 1:NumModels
        % 모델 객체 가져오기
        ModelObj = app.GetModel(ModelIndex-1);
        ModelName = ModelObj.GetName;
        
        % 모델 클래스 인스턴스 생성
        JprojStruct.(ModelName)=struct();
        % 모델의 스터디 수 가져오기
        NumStudies = ModelObj.NumStudies;
        
        % 각 스터디에 대해 반복
        for StudyIndex = 1:NumStudies
            % 스터디 이름 가져오기
            StudyName = ModelObj.GetStudy(StudyIndex-1).GetName;
            
            % 스터디 클래스 인스턴스 생성 및 추가
            % study = Study(StudyName);
            % model = model.addStudy(study);
            JprojStruct.(ModelName).(StudyName)=struct();
        end
        
        % JprojStruct에 모델 추가
        % JprojStruct.(ModelName) = model;
    end
end



% 
% function JprojTable=getJProjHier(app)
% 
%     NumModels=app.NumModels;
%     JprojTable=table();
%     for ModelIndex=1:NumModels
%         ModelObj=app.GetModel(ModelIndex-1);
%         JprojTable.ModelName{ModelIndex}=ModelObj.GetName;
%         NumStudies=ModelObj.NumStudies;
%         StudyCell=repmat({''},NumStudies,1);
%         for StudyIndex=1:NumStudies
%         StudyCell{StudyIndex}=ModelObj.GetStudy(StudyIndex-1).GetName;
%         end
%         JprojTable.StudyTable{ModelIndex}=StudyCell;
%     end
% end
