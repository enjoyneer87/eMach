function removedUnMatchedTable = removeUnmatchedRows(nameTable, inputTable)
    % inputTable의 VariableNames를 가져옴
    % nameTable=SLLabTable
    % inputTable=refGetTable
    varNames = inputTable.Properties.VariableNames;
    
    if ~contains(nameTable.Properties.VariableNames,'LabTableCell')
    newTable=cell2table(nameTable.Properties.VariableNames');
    newTable.Properties.VariableNames={'LabTableCell'};
    nameTable=newTable;
    end

    % nameTable.LabTableCell 값 중 varNames에 포함되지 않는 값의 인덱스를 찾음
    isMatched = ismember(nameTable.LabTableCell, varNames');    
    % 포함되지 않는 행을 삭제
    removedUnMatchedTable = nameTable(isMatched, :);
end
