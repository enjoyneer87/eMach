function devsetWindingCircuit(app, NumStudies, RMSCurrent, NoLoadStudyName, LoadStudyName, PWMStudyName)
    % 현재 모델 가져오기
    Model = app.GetCurrentModel;
    
    % 입력 전류 데이터 설정
    InputCurrentData.Current = RMSCurrent * sqrt(2);  % 피크 전류
    InputCurrentData.freqE = 'FreqE';
    InputCurrentData.phaseAdvance = 'MCADPhaseAdvance';
    InputCurrentData.CoilList = [1, 5, 13, 9];
    
    % 각 스터디에 대해 회로 설정 수행
    for StudyIndex = 1:NumStudies
        % 현재 스터디 가져오기
        curStudyObj = Model.GetStudy(StudyIndex - 1);
        app.SetCurrentStudy(curStudyObj.GetName);
        
        % 현재 스터디 이름 가져오기
        curStudyName = curStudyObj.GetName;
        
        % No Load 또는 Load 스터디 처리
        if strcmp(NoLoadStudyName, curStudyName) || strcmp(LoadStudyName, curStudyName)
            CoilList = InputCurrentData.CoilList;
            setInsertInput2SinCircuit(app, InputCurrentData);
        
        % PWM 스터디 처리
        elseif strcmp(PWMStudyName, curStudyName)
            loadJMAG_PWMInput(app);
            curStudyObj.GetCircuit().GetComponent("theta_m").SetLink("Rotation");
        end
    end
end