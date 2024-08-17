function updatedTable = deleteRowsBelowThreshold(tableData, fieldName, threshold)
    % 특정 필드의 값이 작은 행 삭제
    updatedTable = tableData;
    updatedTable(updatedTable.(fieldName) < threshold, :) = [];
end
