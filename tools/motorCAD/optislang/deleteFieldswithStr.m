function updatedTable = deleteFieldswithStr(tableData, fieldName)
    % 특정 필드 이름을 포함하는 필드 삭제
    updatedTable = removevars(tableData, contains(tableData.Properties.VariableNames, fieldName));
end
