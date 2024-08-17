function updatedTable = deleteRowsWithNaNs(tableData)
    % NaN이 포함된 행 삭제
    updatedTable = tableData;
    updatedTable(any(isnan(updatedTable{:,:}), 2), :) = [];
end
