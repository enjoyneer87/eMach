function figInfo = saveFigureAxesInfo(filePath)
    figInfo = struct();
    
    % 현재 활성화된 figure
    fig = gcf;
    
%     % x축, y축 범위와 tick 정보 가져오기
%     xLim = xlim;
%     yLim = ylim;
%     xTick = xticks;
%     yTick = yticks;
    
    % x축, y축 label 가져오기
    xLabel = get(get(gca, 'XLabel'), 'String');
    yLabel = get(get(gca, 'YLabel'), 'String');
    figInfo.size=fig.Position;
    % x축, y축 범위 및 레이블 정보 저장
    figInfo.xLim = xlim;
    figInfo.yLim = ylim;
    figInfo.xTick = xticks;
    figInfo.yTick = yticks;
    figInfo.xTickLabel = cellstr(get(gca,'XTickLabel'));
    figInfo.yTickLabel = cellstr(get(gca,'YTickLabel'));
    figInfo.xLabel = xLabel;
    figInfo.yLabel = yLabel;
    
    % 저장된 정보를 확인
    disp(figInfo);

    % figure를 mat 파일로 저장합니다.
    save(filePath, 'figInfo');
end