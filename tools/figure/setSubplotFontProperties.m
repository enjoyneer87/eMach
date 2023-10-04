function setSubplotFontProperties(figureHandle, fontName, fontSize)
    % figureHandle: 변경할 figure의 핸들
    % fontName: 설정하려는 글씨체 이름
    % fontSize: 설정하려는 글씨체 크기
    
    % figure 내의 모든 축 핸들을 가져옵니다.
    axHandles = findall(figureHandle, 'Type', 'Axes');
    
    % 각 축 핸들에 대해 글씨체를 설정합니다.
    for i = 1:length(axHandles)
        set(axHandles(i), 'FontName', fontName, 'FontSize', fontSize);
    end
end
