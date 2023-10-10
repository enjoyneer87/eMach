function plotSubPlotTNContour(plotFunction,matData1,subPlotList,matData2,startfigure)
    if nargin<5
     startfigure=1;
    end
    lastfigure=length(subPlotList);
    numFigure=lastfigure-startfigure+1;
    numRows = ceil(sqrt(numFigure));
    numCols = ceil(numFigure / numRows);
    switch nargin
        case 3
        figure
        for i = startfigure:lastfigure
            subfigureIndex=i-startfigure+1;
            subplot(numRows, numCols, subfigureIndex);
    
            plotFunction(matData1, subPlotList{i});
            legend off
        end 
        case 4   
        figure
        for i = startfigure:lastfigure
            subfigureIndex=i-startfigure+1;
            subplot(numRows, numCols, subfigureIndex);
    
            plotFunction(matData1, subPlotList{i},matData2);
            legend off
        end   
    end
end