function uniqueTable = filterAndSelectUniqueRows(table3, columnName)
    % table: 입력 테이블
    % columnName: 고유한 값을 기준으로 필터링할 열의 이름

    % 열을 기준으로 고유한 값을 찾음
    uniqueValues = unique(table3.(columnName));

    % 각 고유한 값에 대해 한 행만 선택하여 새로운 테이블 생성
    uniqueTable = table();
    for i = 1:length(uniqueValues)
        value = uniqueValues(i);
        idx = find(strcmp(table3.(columnName), value), 1, 'first');
        if ~isempty(idx)
            uniqueTable = [uniqueTable; table3(idx, :)];
        end
    end
end
