function numColumns = suggestLegendColumns(legendItems, figureWidth)
    % legendItems: legend에 포함될 항목의 cell 배열
    % figureWidth: 그래프의 폭 (단위: 픽셀)

    % 문자열 길이의 평균을 계산
    avgStringLength = mean(cellfun(@length, legendItems));
    
    % 예상되는 legend 항목의 폭을 설정 (픽셀 단위)
    % 이 값은 폰트 크기와 디스플레이 해상도에 따라 조정해야 할 수 있습니다.
    estimatedItemWidth = avgStringLength * 6; % 가정: 각 문자는 약 6픽셀의 폭을 차지
    
    % 적절한 column 수를 추정
    % 그래프 폭을 예상 legend 항목 폭으로 나누어 column 수를 결정
    numColumns = max(1, floor(figureWidth / estimatedItemWidth));
end
