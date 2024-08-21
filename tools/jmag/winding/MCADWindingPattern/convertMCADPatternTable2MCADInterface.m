function [reNumberLayerTable,TotalTable] = convertMCADPatternTable2MCADInterface(McadWindingPatternTable)

    %% renumber - RadPosition, SlotNumber
    NewWindingTable                     = renumberCoilNumber(McadWindingPatternTable);
    reNumberLayerTable                  = renumberRadialPositionNumber(NewWindingTable);
    [NewWindingTable, SlotArray]        = renumberMCADSlotNumber(reNumberLayerTable);
    NewWindingTable.TypeofData          = categorical(NewWindingTable.TypeofData);
    if min(SlotArray)==0
    NumSlots                            =max(SlotArray)+1;
    else
    NumSlots                            =max(SlotArray);
    end
    %% get Phase N ParaPathNumber
    PhaseNumber                         =length(unique(NewWindingTable.PhaseNumber));
    ParaPathNumber                      =length(unique(NewWindingTable.ParallelPathNumber));
    %% refer 
    % wdgTabCellperPhRowNParaCol         = parsMCADWindingTableByPhaseRNParaCol(NewWindingTable);
    %% Get Table
    % Preallocate cell array to hold tables for each Phase and ParaPath
    cellTableArray = cell(PhaseNumber, ParaPathNumber);
    TotalTable     = table();
    for PhaseIndex = 1:PhaseNumber
        % Phase별로 필터링
        curPhaseCoilTable = NewWindingTable(NewWindingTable.PhaseNumber == PhaseIndex, :);
        for ParaPathIndex = 1:ParaPathNumber
            % Parallel Path별로 필터링
            curPhaseParaPathCoilTable = curPhaseCoilTable(curPhaseCoilTable.ParallelPathNumber == ParaPathIndex, :);
            curCoilTable = curPhaseParaPathCoilTable;
            % CoilNumber 가져오기
            CoilNumber = unique(curCoilTable.CoilNumber);
            % ValueTable에서 GoSlot, GoRadialPosition, ReturnSlot, ReturnRadialPosition 정보를 가져오기
            GoSlot                  = curCoilTable.ValueTable(curCoilTable.TypeofData == 'GoSlot');
            GoRadialPosition        = curCoilTable.ValueTable(curCoilTable.TypeofData == 'GoRadialPosition');
            ReturnSlot              = curCoilTable.ValueTable(curCoilTable.TypeofData == 'ReturnSlot');
            ReturnRadialPosition    = curCoilTable.ValueTable(curCoilTable.TypeofData == 'ReturnRadialPosition');
            Turns                   = curCoilTable.ValueTable(curCoilTable.TypeofData == 'Turns');
            % Pitch 계산 (GoSlot과 ReturnSlot의 차이 절대값)
            [direction, Pitch] = calcPitchwithDirection(str2double(GoSlot), str2double(ReturnSlot), NumSlots);
            Pitch              = num2cell(Pitch);
            % Phase와 ParaPath에 해당하는 테이블 생성
            coilTableMCADInterface = table(CoilNumber, GoSlot, GoRadialPosition, ReturnSlot, ReturnRadialPosition, Pitch, Turns, ...
                'VariableNames', {'CoilNumber', 'GoSlot', 'GoRadialPosition', 'ReturnSlot', 'ReturnRadialPosition', 'Pitch', 'Turns'});
            coilTableMCADInterface.GoRadialPosition    =categorical(coilTableMCADInterface.GoRadialPosition);
            coilTableMCADInterface.ReturnRadialPosition=categorical(coilTableMCADInterface.ReturnRadialPosition);
            cellTableArray{PhaseIndex, ParaPathIndex} = coilTableMCADInterface;
            % 누적 테이블
            Table4TotalTable=coilTableMCADInterface;
            % PhaseNumber와 ParallelPath 열을 각각 문자열 셀 배열로 설정
            Table4TotalTable.PhaseNumber   = arrayfun(@(x) num2str(x), PhaseIndex*ones(height(coilTableMCADInterface),1), 'UniformOutput', false);
            Table4TotalTable.ParallelPath  = arrayfun(@(x) num2str(x), ParaPathIndex*ones(height(coilTableMCADInterface),1), 'UniformOutput', false);
            TotalTable=[TotalTable;Table4TotalTable];
        end
    end
    %% Categorial
    TotalTable.PhaseNumber = categorical(TotalTable.PhaseNumber);
    TotalTable.ParallelPath = categorical(TotalTable.ParallelPath);
    %% 위치정렬
    TotalTable                  = movevars(TotalTable, "PhaseNumber", "Before", "CoilNumber");
    TotalTable                  = movevars(TotalTable, "ParallelPath", "After", "PhaseNumber");
    % 각 Phase와 ParaPath를 행과 열로 가지는 최종 테이블로 변환
    reNumberLayerTable          = cell2table(cellTableArray, 'VariableNames', arrayfun(@(x) sprintf('ParaPath%d', x), 1:ParaPathNumber, 'UniformOutput', false));
    reNumberLayerTable.Phase    = (1:PhaseNumber)';
    % 최종 테이블을 원하는 형태로 재배열
    reNumberLayerTable          = [reNumberLayerTable(:, end), reNumberLayerTable(:, 1:end-1)];
    % reNumberLayerTable에 'Phase'와 행 번호를 조합한 행 이름 설정
    reNumberLayerTable.Properties.RowNames = arrayfun(@(x) ['Phase', num2str(x)], reNumberLayerTable.Phase, 'UniformOutput', false);
    reNumberLayerTable                     =removevars(reNumberLayerTable,"Phase");
    reNumberLayerTable.Properties.DimensionNames={'PhaseNumber','ParallelPath'};
end