function setMagnetConductor(app, MagnetTable, StudyIndex)
    % 현재 모델을 가져옵니다.
    Model = app.GetCurrentModel;
    
    % 'magnet'을 포함하는 MagnetTable의 인덱스를 찾습니다.
    MagnetNameIndex = find(contains(MagnetTable.Name, 'magnet', 'IgnoreCase', true));
    
    % 각 자석에 대해 도체를 설정합니다.
    for MagnetIndex = 1:length(MagnetNameIndex)
        % 현재 스터디 객체를 가져옵니다.
        CurrentStudyObj = Model.GetStudy(StudyIndex - 1);
        
        % 자석 이름과 해당하는 파트 인덱스를 가져옵니다.
        MagnetName = MagnetTable.Name{MagnetNameIndex(MagnetIndex)};
        partIndex = MagnetTable.partIndex(MagnetNameIndex(MagnetIndex));
        
        % 에디 전류 계산 허용 설정
        CurrentStudyObj.GetMaterial(partIndex).SetValue("EddyCurrentCalculation", 1);
        
        % 자석 회로 이름 생성 및 y 위치 설정
        magConductorName = ['mag', num2str(MagnetIndex)];
        yPosition = 0 + 5 * MagnetIndex;
        
        % 회로 객체 가져오기
        circuitObj = CurrentStudyObj.GetCircuit;
        ComponentObj = circuitObj.GetComponent(magConductorName);
        
        % 자석 회로가 존재하지 않으면 생성
        if ~ComponentObj.IsValid
            circuitObj.CreateComponent("FEMConductor", magConductorName);
            circuitObj.CreateInstance(magConductorName, -77, yPosition + 63);
            circuitObj.CreateComponent("Ground", "Ground");
            circuitObj.CreateInstance("Ground", -75, yPosition + 61);
        end
        
        % 자석 조건 생성
        if ~CurrentStudyObj.GetCondition(magConductorName).IsValid
            curConditionObj = CurrentStudyObj.CreateCondition("FEMConductor", magConductorName);
            
            % 자석 링크 설정
            curConditionObj.SetLink(magConductorName);
            
            % 파트 선택 및 설정
            subConObj = curConditionObj.GetSubCondition(0);
            if subConObj.IsValid
                subConObj.ClearParts();
                sel = subConObj.GetSelection();
                sel.SelectPart(partIndex);
                subConObj.AddSelected(sel);
            end
        end
    end
end