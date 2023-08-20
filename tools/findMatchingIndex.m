function matchingIndices = findMatchingIndex(cellName, variableName)
    % 주어진 조건에 따라 인덱스를 찾는 함수
    matchingIndices=[];
    for i = 1:numel(cellName)
        if strcmp(cellName{i}, variableName)
            matchingIndices = [matchingIndices i]; % 일치하는 것이면 인덱스 저장
        end
    end
end