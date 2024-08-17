function matchingIndices = findMatchingIndicesArray(A, B)
    % Az.NodeID와 WireStruct(Index).NodeID가 숫자 배열이라고 가정합니다.
    % 만약 문자열 배열이라면, str2double을 사용하여 숫자로 변환합니다.
    
    % 숫자 배열로 변환

    
    % 일치하는 인덱스 찾기
    [~, matchingIndices] = ismember(A, B);
    
    % 일치하지 않는 경우를 제거
    matchingIndices = matchingIndices(matchingIndices ~= 0);
end