function combineFiguresIntoSubplots()
    % 모든 열려있는 figure의 핸들을 얻습니다.
    allFigures = findall(0, 'Type', 'figure');

    % 새로운 figure를 생성합니다.
    newFig = figure;
    startfigure=1;
    % 각 원래 figure를 순회하며 내용을 새로운 subplot으로 복사합니다.
    numFigures = length(allFigures);
    
    numFigure=numFigures-startfigure+1;
    numRows = ceil(sqrt(numFigure));
    numCols = ceil(numFigure / numRows);

    for idx = 1:numFigures
        subfigureIndex=idx-startfigure+1;
        originalFig = allFigures(idx);
        originalAxes = findall(originalFig, 'Type', 'axes');
    


        % 새로운 subplot을 생성합니다.
        ax = subplot(numRows, numCols, subfigureIndex, 'Parent', newFig);

        % 원래 figure의 내용을 새로운 subplot으로 복사합니다.
        copyobj(originalAxes.Children, ax);

        % 원래 axes의 속성을 새로운 subplot으로 복사합니다.
        ax.XLim = originalAxes.XLim;
        ax.YLim = originalAxes.YLim;
        ax.Title.String = originalAxes.Title.String;
        ax.XLabel.String = originalAxes.XLabel.String;
        ax.YLabel.String = originalAxes.YLabel.String;
        formatter_sci;
        % 원래 figure를 닫습니다.
        close(originalFig);
    end
end
