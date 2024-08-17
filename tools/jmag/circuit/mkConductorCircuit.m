function PhaseStruct = mkConductorCircuit(pole,slotNumber,ParallelNumber, CoilList, app, initialY)
    %% Initial Obj
    curStudyObj   = app.GetCurrentStudy;
    curCircuitObj = app.GetCurrentStudy.GetCircuit;
    %% dev
    PhaseNameList = {'U', 'V', 'W'};

    %% input
    if nargin < 4
        initialY = 70;  % 시작 Y 위치를 설정
    end

    % 24개
    % 3*2*2
    % U1_Slot_Component
    %% 상 간 간격을 병렬 회로 수에 따라 조정
    interPhaseGap = ParallelNumber * (-4);
    groundPosition = [10, 53];  % 그라운드 위치 (X, Y)
    curCircuitObj.CreateInstance("Ground", groundPosition(1), groundPosition(2));

    for PhaseIndex = 1:3
        PhaseName = PhaseNameList{PhaseIndex};
        ParaStruct = struct();
        
        % 각 상별로 Y 위치를 상수를 곱하여 조정
        PhaseBaseY = initialY + (PhaseIndex - 1) * interPhaseGap;  % 각 상의 기본 Y 위치
        
        %% slot, Pole, q
        q             =calcWindingQs(slotNumber,pole);
        turnPerSlot   =4;
        slotNumberInSinglePole=slotNumber/(360/calcMotorPeriodicity(double(pole),slotNumber));

        for qIndex=1:q
            slotName=['Slot',num2str((qIndex-1)+(PhaseIndex*q-1))];
            %% Parallel
            for ParaPathIndex = 1:ParallelNumber
                PhaseParaName = [PhaseName,'Para',num2str(ParaPathIndex)];
                ComponentName=  [PhaseParaName,'Coil',num2str(CoilList(ComponentIndex)),slotName];
                PositionY = PhaseBaseY + (-ParaPathIndex * 3);  % 병렬 경로별로 위치 조정
                for ComponentIndex=1:length(CoilList)
                ComponentName{ComponentIndex}               =;
                
                ParaStruct(ParaPathIndex).ComponentTable = mkConductorSingleSeries(PhaseParaName, CoilList,slotName, app, PositionY);
                end
            end
            
            %% Connect Parallel Path
            numberofSeries = height(ParaStruct(1).ComponentTable);
            offset = 2;  % X 위치 조정
    
            % 병렬 경로의 시작을 연결
            for ParallePathIndex = 1:ParallelNumber-1
                ParaStartPosition1 = ParaStruct(ParallePathIndex).ComponentTable.position{1};
                ParaStartPosition2 = ParaStruct(ParallePathIndex+1).ComponentTable.position{1};
                curCircuitObj.CreateWire(ParaStartPosition1(1) - offset, ParaStartPosition1(2), ...
                                         ParaStartPosition2(1) - offset, ParaStartPosition2(2));
            end
    
            % 병렬 경로의 끝을 연결
            for ParallePathIndex = 1:ParallelNumber-1
                ParaEndPosition1 = ParaStruct(ParallePathIndex).ComponentTable.position{numberofSeries};
                ParaEndPosition2 = ParaStruct(ParallePathIndex+1).ComponentTable.position{numberofSeries};
                curCircuitObj.CreateWire(ParaEndPosition1(1) + offset, ParaEndPosition1(2), ...
                                         ParaEndPosition2(1) + offset, ParaEndPosition2(2));
            end
    
            % 첫 번째와 마지막 병렬 경로의 시작과 끝 위치 저장
            PhaseStruct(PhaseIndex).StartPosition = [ParaStruct(1).ComponentTable.position{1}, ...
                                                     ParaStruct(ParallelNumber).ComponentTable.position{1}];
            PhaseStruct(PhaseIndex).EndPosition   = [ParaStruct(1).ComponentTable.position{numberofSeries}, ...
                                                     ParaStruct(ParallelNumber).ComponentTable.position{numberofSeries}];
    
            %% Connect each phase to ground
            EndPosition = ParaStruct(1).ComponentTable.position{numberofSeries};
            curCircuitObj.CreateWire(EndPosition(1)+2, EndPosition(2), groundPosition(1), groundPosition(2)+2);
    
            PhaseStruct(PhaseIndex).ParaStruct = ParaStruct;
        end
    end
end