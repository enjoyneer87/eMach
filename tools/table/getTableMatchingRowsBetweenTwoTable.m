function matchingRows2Table = getTableMatchingRowsBetweenTwoTable(table1, variable_name1, table2, variable_name2)
    % table1에서 variable_name1과 table2에서 variable_name2를 비교하여 일치하는 행 찾기
    matchingIndices = [];
    for i = 1:numel(table2.(variable_name2))
        matchingIndices = [matchingIndices; find(strcmp(table1.(variable_name1), table2.(variable_name2){i}))];
    end

    % 일치하는 행 추출
    matchingRows2Table = table1(matchingIndices, :);
end
