function latestIndex = findMostRecentIndex(lastwriteDateList,numberofIndex)
    % lastwriteDateList: 날짜 및 시간이 저장된 문자열 셀 배열

    % 날짜 및 시간 문자열을 datetime 형식으로 변환
    
    for cellIndex=1:length(lastwriteDateList)
    dateTimes(cellIndex)=mkDateTimeType(lastwriteDateList{cellIndex});
    end
    % 날짜 및 시간 배열을 정렬하고 인덱스를 반환
    [~, sortedIndices] = sort(dateTimes, 'descend');
    
    if nargin<2
    % 두 번째로 최근 날짜의 인덱스를 가져옴
    latestIndex = sortedIndices(1);
    else
    latestIndex = sortedIndices(numberofIndex);
    end
end