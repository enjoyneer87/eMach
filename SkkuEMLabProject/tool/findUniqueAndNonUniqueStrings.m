function [uniqueStringsInCell1, uniqueStringsInCell2, nonUniqueStrings] = findUniqueAndNonUniqueStrings(cell1, cell2)
    % 함수 설명:
    % 두 개의 string cell 배열을 비교하여 cell1과 cell2 각각에 대해
    % 고유한 문자열과 고유하지 않은 문자열을 찾습니다.
    nonUniqueStrings = intersect(cell1, cell2);
    uniqueStringsInCell1 = setdiff(cell1,nonUniqueStrings);
    uniqueStringsInCell2 = setdiff(cell2, nonUniqueStrings);
end
