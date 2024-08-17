function     FigureData=checkExistFigure(figNumber)
%%Check There is Same Type Figure
    if ishandle(figNumber) && strcmp(get(figNumber, 'Type'), 'figure')
        FigureData.PlotType ='Comparison';
    
    % 현재 figure 내의 모든 line 객체 찾기
        lineHandles = findobj(gcf, 'Type', 'line');
        
        % 각 line 객체의 색상 조회
        for i = 1:length(lineHandles)
        FigureData.lineColor = get(lineHandles(i), 'Color');
        % disp(['Line ', num2str(i), ' 색상: ', num2str(lineColor)]);
        end

    else
        FigureData.PlotType ='ref';
    end
    
end