function wdgTabCellperPhRowNParaCol=parsMCADWindingTableByPhaseRNParaCol(NewWindingTable)
    %% 상-병렬회로
    PhaseNumber         =unique(NewWindingTable.PhaseNumber);
    ParallelPathNumber  =unique(NewWindingTable.ParallelPathNumber);
    %% 분류
    for PhNumberIndex = 1:length(PhaseNumber)
        for ParaPathNumberIndex = 1:length(ParallelPathNumber)
            selectedRows = (NewWindingTable.PhaseNumber == PhNumberIndex) &(NewWindingTable.ParallelPathNumber == ParaPathNumberIndex);  % 특정 PhaseNumber와 ParallelPathNumber에 해당하는 행 선택           
            onePhaseParallelTable = NewWindingTable(selectedRows, :);                                                                 % 선택된 행으로부터 새로운 테이블 생성     
            % 결과를 cell 배열에 저장
            wdgTabCellperPhRowNParaCol{PhNumberIndex, ParaPathNumberIndex} = onePhaseParallelTable;
        end
    end
end
