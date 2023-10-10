function NonMatchingRows2Table = getTableNonMatchingRowsBetweenTwoTable(table1, variable_name1, table2, variable_name2)
    % table1에서 variable_name1과 table2에서 variable_name2를 비교하여 일치하지 않는 행 찾기

    % table1의 해당 열을 셀 배열로 변환
    col1 = table1.(variable_name1);

    % table2의 해당 열을 셀 배열로 변환
    col2 = table2.(variable_name2);

    % table1의 각 행이 table2의 열2에 포함되지 않는지 확인
    isNonMatching = cellfun(@(x) ~any(strcmp(x, col2)), col1);

    % 일치하지 않는 행 추출
    NonMatchingRows2Table = table1(isNonMatching, :);
end
