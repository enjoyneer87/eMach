function trimLegendToIndex(maxIndex)
    % trimLegendToIndex - 범례에서 특정 번호까지의 string과 marker만 남김
    %
    % maxIndex - 남길 범례의 최대 인덱스 번호
    
    % 현재 figure에서 범례 핸들을 가져옴
    legendHandle = findobj(gcf, 'Type', 'Legend');
    
    if isempty(legendHandle)
        error('No legend found in the current figure.');
    end

    % 현재 범례의 String과 객체(플롯 핸들) 가져오기
    currentStrings = legendHandle.String;
    legendObjects = legendHandle.PlotChildren;

    % 인덱스 범위 초과 시 오류 방지
    if maxIndex > length(currentStrings)
        error('maxIndex exceeds the number of legend entries.');
    end

    % 남길 플롯 객체와 String만 남기기
    newStrings = currentStrings(1:maxIndex);
    newLegendObjects = legendObjects(1:maxIndex);

    % 기존 범례 삭제 후 새 범례 생성
    legend(newLegendObjects, newStrings);
end