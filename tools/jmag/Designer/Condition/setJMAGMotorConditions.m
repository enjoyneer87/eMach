function setJMAGMotorConditions(app, PartStructByType, isConductor,NumStudies)
    if nargin<4
    Model = app.GetCurrentModel;
    NumStudies=Model.NumStudies;
    end 
    % [TC] setJmagCondition (Thermal Condition Table방식으로 변경
    % 모델 및 현재 모델 가져오기
    Model = app.GetCurrentModel;
    % 각 스터디를 순회하며 조건 설정
    for StudyIndex = 1:NumStudies
        % 현재 스터디 객체 가져오기
        curStudyObj = Model.GetStudy(StudyIndex - 1);
        app.SetCurrentStudy(curStudyObj);

        % 디자인 테이블 및 Pole, Slot 정보 가져오기
        Dtable = curStudyObj.GetDesignTable();
        Pole = Dtable.GetEquation('POLES').GetValue;
        Slot = Dtable.GetEquation('SLOTS').GetValue;
        RotorOnePoleAngle = calcMotorPeriodicity(Pole, Slot);

        % StatorEdgeXposition 계산
        CoreDistance =         PartStructByType.StatorCoreTable.CentroidR;
        StatorEdgeXposition = CoreDistance / 2;

        % 회전 주기 경계 조건 설정
        setRPBoundaryCondition(curStudyObj, RotorOnePoleAngle, StatorEdgeXposition);

        % 회전 운동 설정
        setRotationMotion(app, 'speed/60');

        % 토크 조건 설정
        setTorqueCondition(curStudyObj);

        % [TC]Iron Loss


        %% 도체 재질 설정
        % 코일 또는 도체 조건 설정
        if ~isempty(PartStructByType.SlotTable) && isConductor == 0
            setJMAGFEMCoil(curStudyObj, PartStructByType);
        elseif isConductor==1&(isempty(PartStructByType.SlotTable) | ~isempty(PartStructByType.ConductorTable))
            % 도체 조건 설정
            setJMAGFEMConductor(PartStructByType.ConductorTable, curStudyObj);
        elseif curStudyObj.GetWinding(0).IsValid      
            ConductorPartTable=PartStructByType.ConductorTable;
            
            firstSlotWirePartsTable=ConductorPartTable(contains(ConductorPartTable.Name,'Slot1'),:);
            firstSlotWirePartsTable=sortrows(firstSlotWirePartsTable,"CentroidR","descend");
            ConductorNumber         =height(firstSlotWirePartsTable);
            setWireRegion(app,firstSlotWirePartsTable,ConductorNumber) 
        end
    end
end