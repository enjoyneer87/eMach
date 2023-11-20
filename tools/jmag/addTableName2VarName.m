function StartVertexTable = addTableName2VarName(tableName)
    StartVertexTable = evalin('base', tableName); % 작업 공간의 변수를 가져옴
    varNames = StartVertexTable.Properties.VariableNames;
    
    for varIndex = 1:length(varNames)
        oldVarName = varNames{varIndex};
        newVarName = [tableName, oldVarName];
        StartVertexTable.Properties.VariableNames{varIndex} = newVarName;
    end
    
    assignin('base', tableName, StartVertexTable); % 수정된 변수를 다시 작업 공간에 저장
end
