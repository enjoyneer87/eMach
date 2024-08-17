function NewCellofWindingfTableByPhase=SplitWindingTableByPhaseRowNParallelPathCol(NewWindingTable)

    PhaseNumbers=unique(NewWindingTable.PhaseNumber);
    ParallelPathNumbers=unique(NewWindingTable.ParallelPathNumber);
    
    
    for PhaseNumber = 1:length(PhaseNumbers)
        for ParallelPathNumber = 1:length(ParallelPathNumbers)
            % 특정 PhaseNumber와 ParallelPathNumber에 해당하는 행 선택
            selectedRows = (NewWindingTable.PhaseNumber == PhaseNumber) &(NewWindingTable.ParallelPathNumber == ParallelPathNumber);
            
            % 선택된 행으로부터 새로운 테이블 생성
            onePhaseParallelTable = NewWindingTable(selectedRows, :);
            
            % 결과를 cell 배열에 저장
            NewCellofWindingfTableByPhase{PhaseNumber, ParallelPathNumber} = onePhaseParallelTable;
        end
    end

end
