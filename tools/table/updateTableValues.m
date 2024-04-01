function updatedTable = updateTableValues(targetTable, sourceTable)
    % targetTable을 업데이트하고, 결과를 updatedTable에 저장
    updatedTable = targetTable;
    
    % 공통 변수명 찾기
    commonVars = intersect(targetTable.Properties.VariableNames, sourceTable.Properties.VariableNames);
    
    % 공통 변수에 대해 값을 업데이트
    for varName = commonVars
        updatedTable.(varName{1}) = sourceTable.(varName{1});
    end
end
