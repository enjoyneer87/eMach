function plotSubPlotbyStructAndstrCell(plotFunction,FitResultStr,subPlotList,startfigure)
if nargin<4
startfigure=1;
end

% 서브플롯 배치를 적절하게 조정합니다.
lastfigure=length(subPlotList);
numFigure=lastfigure-startfigure+1;
numCols = ceil(sqrt(numFigure));
numRows = ceil(numFigure / numCols);

    figure
    for i = startfigure:lastfigure
        subfigureIndex=i-startfigure+1;
        subplot(numRows, numCols, subfigureIndex);
        plotFunction(FitResultStr(i).fitResult, FitResultStr(i).singleDataSet, 0);
        legend off
    end   
    figure
    for i = startfigure:lastfigure
        subfigureIndex=i-startfigure+1;
        subplot(numRows, numCols, subfigureIndex);
        plotFunction(FitResultStr(i).fitResult, FitResultStr(i).singleDataSet, 1);
    end

end