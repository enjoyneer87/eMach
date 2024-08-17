function combineFiguresIntoSubplots()
    % 모든 열려있는 figure의 핸들을 얻습니다.
    % delete(allFigures)
    allFigures = findall(0, 'Type', 'figure');
    % 새로운 figure를 생성합니다.
    startfigure=1;
    % 각 원래 figure를 순회하며 내용을 새로운 subplot으로 복사합니다.
    numFigures = length(allFigures);
    
    numFigure=numFigures-startfigure+1;
   
    
    % 최대 열 수를 4로 제한하여 행과 열을 계산
    if numFigure <= 4
        % Figure 수가 4 이하인 경우: 1x4, 2x2 등의 배열
        numCols = numFigure;
        numRows = 1;
    elseif numFigure <= 8
        % Figure 수가 5에서 8 사이인 경우: 2x4 배열
        numCols = 4;
        numRows = ceil(numFigure / numCols);
    else
        % Figure 수가 9 이상인 경우: 열을 4로 제한하고 행을 계산
        numCols = 4;
        numRows = ceil(numFigure / numCols);
    end


    newFig = figure(numFigures+1);
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
