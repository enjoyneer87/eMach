function  exportData=exportAirGapBField(i_Stator_OD,app)
    exportData=struct();
% Jproject File Path
    JMAG=app;
    file_path=JMAG.GetProjectPath();
% Project Name
    [~, fileName,~]=fileparts(file_path);
    % app.SetProjectName(fileName);
    % pjt_name=app.GetProjectName() ;  
%   파일이 켜져있지 않으면 파일명 읽어서 열기
%% Find Model& study Name
    ModelName=JMAG.GetCurrentModel.GetName();
    StudyName=JMAG.GetCurrentStudy.GetName();
    Simulation.ModelName=ModelName;
    Simulation.StudyName=StudyName;
% Check for New Results
    JMAG.GetModel(Simulation.ModelName).GetStudy(Simulation.StudyName).CheckForNewResults();
% for number_case
    JStudy   =JMAG.GetModel(Simulation.ModelName).GetStudy(Simulation.StudyName);
    NumCases =JStudy.GetDesignTable().NumCases();

    
%% Model 단위 [Tobe]
%%study 단위에서
check_case = struct('result_exist', false, 'caseno', 0); % Preallocation을 위한 초기 배열 생성
check_case = repmat(check_case, NumCases, 1); % 배열 크기를 미리 할당

%% Result Check
for i=1:NumCases
    Hasresult=JStudy.CaseHasResult(i-1);
    check_case(i).result_exist=Hasresult;
    check_case(i).caseno=i;
end

%% 
for i=1:NumCases
    if check_case(i).result_exist==1
        % Select Air region
        JMAG.View().SetCurrentCase(i)
        selectAirByWorldPosSOD(i_Stator_OD,JMAG);
        % Slice Condition Number
        % Num_condition=Num_condition_slice(Simulation);
        Num_condition=0;
        selectObj='All';
        % export with skew check
        exportFilePath=exportJMAGResultTable(JMAG,Simulation,i,selectObj,Num_condition,0);
        exportData(i).case=i;
        exportData(i).exportFilePath=exportFilePath;
    end
end


end

