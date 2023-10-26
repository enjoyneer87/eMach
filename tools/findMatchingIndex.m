function matchingIndices = findMatchingIndex(cellNameorCategorical, str)
    % 주어진 조건에 따라 인덱스를 찾는 함수
    matchingIndices = [];
    if ~iscell(cellNameorCategorical)
        cellNameorCategorical=cellstr(cellNameorCategorical);
    end
    if iscell(cellNameorCategorical) || iscategorical(cellNameorCategorical)
        for i = 1:numel(cellNameorCategorical)
            if iscell(cellNameorCategorical)
                if contains(cellNameorCategorical{i}, str,'IgnoreCase',true)
                matchingIndices = [matchingIndices i]; % 일치하는 것이면 인덱스 저장
                end
            elseif iscategorical(cellNameorCategorical) && any(contains(char(cellNameorCategorical(i)), str,'IgnoreCase',true))
                matchingIndices = [matchingIndices i]; % 일치하는 것이면 인덱스 저장
            end
        end
    end
end
