function plotMultipleInterpSubplots(plotFunction, Data4Interp,Data4Interp2, subPlotList,lastfigure, startfigure)
    % plotFunction: 그래프를 그리는 함수 (함수 핸들)
    % lastfigure: 총 서브플롯의 개수
        
    if istable(Data4Interp)
        InputTable=Data4Interp;
    elseif isstruct(Data4Interp)
        [InputTable,~] = createTableFromMCADSatuMapStr(Data4Interp);
    else 
        error('올바른 데이터를 입력하세요');
    end

    if nargin < 6
        startfigure = 1;
    end
    if nargin <4
        varNames=InputTable.Properties.VariableNames;
        varUnits=InputTable.Properties.VariableUnits;
        nonAmpereIndex=~strcmp(varUnits,'A');
        subPlotList=varNames(nonAmpereIndex);  
    %% deleteCell
        subPlotList = removeCellwithMatchingStr(subPlotList, 'Sleeve_Loss');
        subPlotList = removeCellwithMatchingStr(subPlotList, 'Coefficient');      
        %% Voltage Cell
        voltageCell = getCellwithMatchingStr(subPlotList, 'V');
        %% Iron Loss Cell
        IronLossCell= getCellwithMatchingStr(subPlotList, 'Iron');        
        %% Other Loss cell
        LossCell= getCellwithMatchingStr(subPlotList, 'Loss');
        LossCell = removeCellwithMatchingStr(LossCell, 'Iron');
        %% Other cell
        otherCell = removeCellwithMatchingStr(subPlotList, 'Loss');      
        otherCell = removeCellwithMatchingStr(otherCell, 'V');      
    end 
    if nargin <5
        lastfigure=length(subPlotList);
    end
    if nargin>1
        for i = 1:lastfigure
        [FitResult(i).fitResult, ~, FitResult(i).singleDataSet] =createInterpDataSetofStrWithFieldName(InputTable,subPlotList{i});
        end
    end
       
    if nargin>2
        if istable(Data4Interp2)
            InputTable2=Data4Interp2;
        elseif isstruct(Data4Interp2)
            [InputTable2,~] = createTableFromMCADSatuMapStr(Data4Interp2);
        else 
            error('올바른 데이터를 입력하세요');
        end
        for i = 1:lastfigure
            [FitResult(i).fitResult, ~, FitResult(i).singleDataSet] =createValidationDataSetTwoStrWithFieldName(InputTable,InputTable2,subPlotList{i});
        end    
    end

    % for i = startfigure:lastfigure
    %     subfigureIndex=i-startfigure+1;
    %     [FitResult(i).fitResult, ~, FitResult(i).singleDataSet] = interpSurfNResidualTwoTableWithVar(Data4InterP, Data4Interp2, subPlotList{i});
    % end        
    

    %% figure 생성
    % mergedFigure = figure;
    numFigure=lastfigure-startfigure+1;
    voltageCell
    
    % 서브플롯 배치를 적절하게 조정합니다.
    numRows = ceil(sqrt(numFigure));
    numCols = ceil(numFigure / numRows);
    % Voltage
        figure(1)
        for i = startfigure:lastfigure
        if contains(FitResult(i).singleDataSet.varName,'V')

            subfigureIndex=i-startfigure+1;
            subplot(numRows, numCols, subfigureIndex);
            plotFunction(FitResult(i).fitResult, FitResult(i).singleDataSet, 0);
            % plotFitResult(FitResult(i).fitResult, FitResult(i).singleDataSet, 0);
            legend off
        end
        end   
        figure(2)
        for i = startfigure:lastfigure
        if contains(FitResult(i).singleDataSet.varName,'V')

            subfigureIndex=i-startfigure+1;
            subplot(numRows, numCols, subfigureIndex);
            plotFunction(FitResult(i).fitResult, FitResult(i).singleDataSet, 1);
            % plotFitResult(FitResult(i).fitResult, FitResult(i).singleDataSet, 1);
        end
        end
    %% Loss
        figure(3)
        for i = startfigure:lastfigure
        if contains(FitResult(i).singleDataSet.varName,'Loss')

            subfigureIndex=i-startfigure+1;
            subplot(numRows, numCols, subfigureIndex);
            plotFunction(FitResult(i).fitResult, FitResult(i).singleDataSet, 0);
            % plotFitResult(FitResult(i).fitResult, FitResult(i).singleDataSet, 0);
            legend off
        end
        end
 
        figure(4)
        for i = startfigure:lastfigure
        if contains(FitResult(i).singleDataSet.varName,'Loss')

            subfigureIndex=i-startfigure+1;
            subplot(numRows, numCols, subfigureIndex);
            plotFunction(FitResult(i).fitResult, FitResult(i).singleDataSet, 1);
            % plotFitResult(FitResult(i).fitResult, FitResult(i).singleDataSet, 1);
        end
        end
    
        figure(5)
        for i = startfigure:lastfigure
            if all(~contains(FitResult(i).singleDataSet.varName,'Loss'),~contains(FitResult(i).singleDataSet.varName,'V'))
            subfigureIndex=i-startfigure+1;
            subplot(numRows, numCols, subfigureIndex);
            plotFunction(FitResult(i).fitResult, FitResult(i).singleDataSet, 0);
            % plotFitResult(FitResult(i).fitResult, FitResult(i).singleDataSet, 0);
            legend off
            end
        end
 
        figure(6)
        for i = startfigure:lastfigure
            if all(~contains(FitResult(i).singleDataSet.varName,'Loss'),~contains(FitResult(i).singleDataSet.varName,'V'))

            subfigureIndex=i-startfigure+1;
            subplot(numRows, numCols, subfigureIndex);
            plotFunction(FitResult(i).fitResult, FitResult(i).singleDataSet, 1);
            % plotFitResult(FitResult(i).fitResult, FitResult(i).singleDataSet, 1);
            end
        end
    


    %%
    % figure(3)
    % for i = startfigure:lastfigure
    %     subfigureIndex=i-startfigure+1;
    %     subplot(numRows, numCols, subfigureIndex);
    %     plotFunction(FitResult(i).fitResult, FitResult(i).singleDataSet, 2);
    % end
    a=findobj('type','figure');
    setSubplotFontProperties(a, 'Times New Roman', 8);

end
