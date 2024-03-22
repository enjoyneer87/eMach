function filteredDataSetCell=removeEmptyCellByCol(DataSetCell,ColIndex)
notEmptyIndices = ~cellfun(@isempty, DataSetCell(:, ColIndex)); % 2열 기준으로 비어있지 않은 행을 찾음
filteredDataSetCell = DataSetCell(notEmptyIndices, :);
end