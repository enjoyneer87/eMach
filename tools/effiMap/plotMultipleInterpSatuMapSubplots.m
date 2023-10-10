function plotMultipleInterpSatuMapSubplots(plotFunction, Data4Interp,Data4Interp2, subPlotList,lastfigure, startfigure)
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
        if ~isempty(varUnits)
        nonAmpereIndex=~strcmp(varUnits,'A');
        subPlotList=varNames(nonAmpereIndex);
        else
        subPlotList=varNames;
        end
    %% deleteCell
        subPlotList = removeCellwithMatchingStr(subPlotList, 'Sleeve_Loss');
        subPlotList = removeCellwithMatchingStr(subPlotList, 'Coefficient');      
        % Voltage Cell
        typeStrt.voltageCell = getCellwithMatchingStr(subPlotList, 'V');
        if isempty(typeStrt.voltageCell)
        typeStrt=rmfield(typeStrt,"voltageCell");
        end
        % Iron Loss Cell
        IronLossCell= getCellwithMatchingStr(subPlotList, 'Iron');
        FE= getCellwithMatchingStr(subPlotList, 'FE');     
        typeStrt.IronLossCell=[IronLossCell FE];
        % typeStrt.IronLossCell=FE;
        if isempty(typeStrt.IronLossCell)
        typeStrt=rmfield(typeStrt,"IronLossCell");
        end
        % Other Loss cell
        LossCell= getCellwithMatchingStr(subPlotList, 'Loss');
        LossCell = removeCellwithMatchingStr(LossCell, 'Fe');
        LossCell = removeCellwithMatchingStr(LossCell, 'AC_Copper_Loss_(C1)');
        typeStrt.LossCell = removeCellwithMatchingStr(LossCell, 'Iron');

        if isempty(typeStrt.LossCell)
        typeStrt=rmfield(typeStrt,"LossCell");
        end
        % Other cell
        otherCell = removeCellwithMatchingStr(subPlotList, 'Loss');      
        typeStrt.otherCell = removeCellwithMatchingStr(otherCell, 'V');      
        if isempty(typeStrt.otherCell)
        typeStrt=rmfield(typeStrt,"otherCell");
        end
    end 
    if nargin <5
        lastfigure=length(subPlotList);
        % typeStrt=struct();
        % typeStrt.(subPlotList{1})=subPlotList{1};
    end
    if nargin>1
        index = 1;
        for i = 1:lastfigure
            [tempFitResult, tempGof, tempSingleDataSet] = createInterpDataSetofStrWithFieldName(InputTable, subPlotList{i});
            
            if ~isempty(tempFitResult) && ~isempty(tempSingleDataSet)
                FitResultStr(index).fitResult = tempFitResult;
                FitResultStr(index).singleDataSet = tempSingleDataSet;
                FitResultStr(index).varNames = subPlotList{i};
                index = index + 1;
            end
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

        index = 1;
        for i = 1:lastfigure
            disp(num2str(i))
            [tempFitResult, tempGof, tempSingleDataSet] = createValidationDataSetTwoStrWithFieldName(InputTable,InputTable2,subPlotList{i});
            
            if ~isempty(tempFitResult) && ~isempty(tempSingleDataSet)
                FitResultStr(index).fitResult = tempFitResult;
                FitResultStr(index).singleDataSet = tempSingleDataSet;
                FitResultStr(index).varNames = subPlotList{i};
                index = index + 1;
            end
        end

        % 
        % for i = 1:lastfigure
        %     [FitResultStr(i).fitResult, ~, FitResultStr(i).singleDataSet] =createValidationDataSetTwoStrWithFieldName(InputTable,InputTable2,subPlotList{i});
        %     FitResultStr(i).varNames=subPlotList{i};
        % end    
    end

    %% figure 생성
    typestrtNames=fieldnames(typeStrt);
    for cellIndex=1:length(typestrtNames)
        cellName=typestrtNames{cellIndex};        
        if ~isempty(typeStrt.(cellName))             
            structbyType.(cellName)      = filterWithFieldValueStruct(FitResultStr,'varNames',typeStrt.(cellName));
            structbyTypeNames=fieldnames(structbyType);     
        end
    end
      
    for strctIndex=1:length(structbyTypeNames)
        structName=structbyTypeNames{strctIndex};
        cellName=typestrtNames{strctIndex};
        plotSubPlotbyStructAndstrCell(plotFunction,structbyType.(structName),typeStrt.(cellName)); 
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
