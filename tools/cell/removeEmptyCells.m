function cleanedCellArray = removeEmptyCells(cellArray)
    % 이 함수는 셀 배열에서 비어 있는 셀을 제거합니다.

    % 셀 배열에서 비어 있는 셀을 식별합니다.
    emptyCells = cellfun(@isempty, cellArray) | ... % 완전히 비어 있는 셀
                cellfun(@(c) ischar(c) && isempty(c), cellArray) | ... % 빈 문자열을 포함하는 셀
                cellfun(@(c) isnumeric(c) && isempty(c), cellArray); % 빈 배열을 포함하는 셀

    % 비어 있는 셀을 제거합니다.
    cleanedCellArray = cellArray(~emptyCells);
end
