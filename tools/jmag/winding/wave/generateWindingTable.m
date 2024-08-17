function WindingTable5PhaseNParaPath = generateWindingTable(LayerInSlot, SlotNumber, ParallelNumber, CoilSpan, PhaseNumber, PolePairs)
    % LayerInSlot: 슬롯당 레이어 수
    % SlotNumber: 슬롯 수
    % ParallelNumber: 병렬 회로 수
    % CoilSpan: 코일 스팬 (슬롯 간 거리)
    % PhaseNumber: 상의 수 (예: 3상)
    % PolePairs: 극수 쌍 수

    % 한 순환에서 GoSlot과 reSlot의 개수
    slotsPerCycle = SlotNumber / CoilSpan / 2;

    % 총 코일 수 계산
    TotalCoilNumber = (SlotNumber / 2) * LayerInSlot;
    TotalCoilNumberPerPhase = TotalCoilNumber / PhaseNumber;
    TotalCoilNumberPerPhasePerParaPath = TotalCoilNumberPerPhase / ParallelNumber;

    % Initialize Slot Arrays
    GoSlotArray = zeros(TotalCoilNumberPerPhasePerParaPath * ParallelNumber, 1);
    GoSlotPositionArray = cell(TotalCoilNumberPerPhasePerParaPath * ParallelNumber, 1);
    reSlotArray = zeros(TotalCoilNumberPerPhasePerParaPath * ParallelNumber, 1);
    reSlotPositionArray = cell(TotalCoilNumberPerPhasePerParaPath * ParallelNumber, 1);

    % Position Labels (슬롯 레이어 수에 따라 포지션 설정)
    PositionLabels = {'a', 'b', 'c', 'd', 'e', 'f'};  % 최대 6개의 포지션 레이블
    PositionLabels = PositionLabels(1:LayerInSlot);   % 슬롯 레이어 수에 따라 포지션을 잘라냄

    % Initialize startSlot for each phase and path
    CoilCounter = 0;  % 코일 번호 초기화
    for PhaseIndex = 1:PhaseNumber
        slotOffset = (PhaseIndex - 1) * (SlotNumber / PhaseNumber);  % 상별 슬롯 오프셋 설정

        for i = 1:TotalCoilNumberPerPhasePerParaPath
            for ParallelPathIndex = 1:ParallelNumber
                CoilCounter = CoilCounter + 1;

                % 코일이 한 바퀴 순환할 조건
                if mod(i-1, slotsPerCycle) == 0 && i > 1
                    startSlot = mod(startSlot + 1, SlotNumber);  % 다음 순환의 시작 슬롯을 1 증가시킴
                    if startSlot == 0
                        startSlot = SlotNumber;
                    end
                else
                    startSlot = mod(CoilCounter - 1 + slotOffset, SlotNumber) + 1;
                end

                % 홀수 패쓰: 시계방향, 짝수 패쓰: 반시계방향
                if mod(ParallelPathIndex, 2) == 1  % 홀수 패스: 시계 방향
                    if i == 1
                        GoSlotArray(CoilCounter) = mod(startSlot - 1 + slotOffset, SlotNumber) + 1;
                    else
                        GoSlotArray(CoilCounter) = mod(GoSlotArray(CoilCounter-1) + CoilSpan, SlotNumber) + 1;
                    end
                else  % 짝수 패스: 반시계 방향
                    if i == 1
                        GoSlotArray(CoilCounter) = mod(startSlot - 1 + slotOffset, SlotNumber) + 1;
                    else
                        GoSlotArray(CoilCounter) = mod(GoSlotArray(CoilCounter-1) - CoilSpan - 1, SlotNumber) + 1;
                    end
                end

                % reSlotArray: CoilSpan만큼 이동한 후의 슬롯 번호
                reSlotArray(CoilCounter) = mod(GoSlotArray(CoilCounter) + CoilSpan - 1, SlotNumber) + 1;

                % Determine the positions for GoSlot and reSlot
                cycle = floor((i-1) / slotsPerCycle);  % 4번의 GoSlot 할당이 한 사이클
                if mod(ParallelPathIndex, 2) == 1  % 홀수 패스: 기본 순서
                    GoSlotPositionArray{CoilCounter} = PositionLabels{mod(2 * cycle, LayerInSlot) + 1};   % 순환에 따른 포지션 설정
                    reSlotPositionArray{CoilCounter} = PositionLabels{mod(2 * cycle + 1, LayerInSlot) + 1};   % 순환에 따른 포지션 설정
                else  % 짝수 패스: 반대 순서
                    GoSlotPositionArray{CoilCounter} = PositionLabels{mod(2 * cycle + 1, LayerInSlot) + 1};   % 순환에 따른 포지션 설정
                    reSlotPositionArray{CoilCounter} = PositionLabels{mod(2 * cycle, LayerInSlot) + 1};   % 순환에 따른 포지션 설정
                end
            end
        end
    end

    % Flatten arrays for table creation
    GoSlotArray = GoSlotArray(:);
    reSlotArray = reSlotArray(:);
    GoSlotPositionArray = GoSlotPositionArray(:);
    reSlotPositionArray = reSlotPositionArray(:);

  % Phase Number Array
    PhaseNumberArray = repelem((1:PhaseNumber)', TotalCoilNumberPerPhasePerParaPath * ParallelNumber);

    % Path Number Array
    PathNumberArray = repmat((1:ParallelNumber)', TotalCoilNumberPerPhasePerParaPath, PhaseNumber);

    % Initialize ThrowArray and TurnsArray
    CoilNumberArray = repmat((1:TotalCoilNumberPerPhasePerParaPath)', ParallelNumber * PhaseNumber, 1);
    ThrowArray = zeros(size(CoilNumberArray));
    TurnsArray = ones(size(CoilNumberArray));
   
    WindingTable5PhaseNParaPath.PhaseNumberArray       =  PhaseNumberArray     ;           
    WindingTable5PhaseNParaPath.CoilNumberArray        =  CoilNumberArray      ;       
    WindingTable5PhaseNParaPath.PathNumberArray        =  PathNumberArray      ;       
    WindingTable5PhaseNParaPath.GoSlotArray            =  GoSlotArray          ;   
    WindingTable5PhaseNParaPath.GoSlotPositionArray    =  GoSlotPositionArray  ;           
    WindingTable5PhaseNParaPath.reSlotArray            =  reSlotArray          ;   
    WindingTable5PhaseNParaPath.reSlotPositionArray    =  reSlotPositionArray  ;           
    % Display the resulting table
end