function lastCells = extractSplitedLastSCells(splitIdentifierNames)
    % 각 셀의 마지막 셀을 추출하는 함수
    % 입력: splitIdentifierNames - 여러 개의 1x3 셀로 구성된 셀 배열
    % 출력: lastCells - 각 1x3 셀의 마지막 셀로 구성된 셀 배열
    
    % 셀 배열의 행 개수 추출
    numRows = size(splitIdentifierNames, 1);
    
    % 결과를 저장할 셀 배열 초기화
    lastCells = cell(numRows, 1);
    
    % 각 행의 마지막 셀 추출
    for i = 1:numRows
        tempIdCell=splitIdentifierNames{i};
        lastCells{i} = tempIdCell{end};
    end
end