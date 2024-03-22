function uniqueColNames = makeUniqueColNames(colNames)
    % 중복된 이름을 찾아 번호를 붙이는 함수
    uniqueColNames = colNames; % 초기 셋업
    for i = 1:length(colNames)
        currentName = colNames{i};
        count = sum(strcmp(colNames(1:i-1), currentName));
        if count > 0
            % 중복된 이름에 번호 추가
            uniqueColNames{i} = [currentName, '_', num2str(count)];
        end
    end
end
