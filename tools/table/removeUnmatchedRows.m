function removedUnMatchedTable = removeUnmatchedRows(nameTable, inputTable)
    % inputTable의 VariableNames를 가져옴
    varNames = inputTable.Properties.VariableNames;
    
    % nameTable.LabTableCell 값 중 varNames에 포함되지 않는 값의 인덱스를 찾음
    isMatched = ismember(nameTable.LabTableCell, varNames);
    
    % 포함되지 않는 행을 삭제
    removedUnMatchedTable = nameTable(isMatched, :);
end
