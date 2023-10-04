function plotMultipleSubplots(plotFunction, matList, matDataFieldName, lastfigure,startfigure)
    % plotFunction: 그래프를 그리는 함수 (함수 핸들)
    % lastfigure: 총 서브플롯의 개수
    if nargin < 5
        startfigure = 1;
    end
    

    % figure 생성
    mergedFigure = figure;
    numFigure=lastfigure-startfigure;
    % 서브플롯 배치를 적절하게 조정합니다.
    numRows = ceil(sqrt(numFigure));
    numCols = ceil(numFigure / numRows);

    for i = startfigure:lastfigure
        subfigureIndex=i-startfigure+1;
        subplot(numRows, numCols, subfigureIndex);
        plotFunction(matList(1).ElecMatFileList{:}, matList(2).ElecMatFileList{:}, matDataFieldName{i});
        legend off
    end

    a=findobj('type','figure');
    setSubplotFontProperties(a, 'Times New Roman', 8);


end
