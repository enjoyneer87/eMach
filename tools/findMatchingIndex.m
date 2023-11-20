function matchingIndices = findMatchingIndex(list2search, str)
    % 주어진 조건에 따라 인덱스를 찾는 함수
    matchingIndices = [];
    % if isstruct({list2search})
    %     matchingIndices = strcmp({list2search}, str);
    if ~iscell(list2search)
        list2search=cellstr(list2search);
    end
    if iscell(list2search) || iscategorical(list2search)
        for i = 1:numel(list2search)
            if iscell(list2search)
                if contains(list2search{i}, str,'IgnoreCase',true)
                matchingIndices = [matchingIndices i]; % 일치하는 것이면 인덱스 저장
                end
            elseif iscategorical(list2search) && any(contains(char(list2search(i)), str,'IgnoreCase',true))
                matchingIndices = [matchingIndices i]; % 일치하는 것이면 인덱스 저장
            end
        end
    end
end
