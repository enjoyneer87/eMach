function FitResultStr = plotMultipleInterpSatuMapSubplots(plotFunction, Data4Interp, mode, Data4Interp2, subPlotList, lastfigure, startfigure)
    % plotFunction : 보간 결과를 subplot에 시각화할 함수 핸들
    % Data4Interp  : 보간용 데이터 (table 또는 struct)
    % mode         : 'fit' 또는 'basis' (기본값은 'fit')
    % Data4Interp2 : (옵션) validation용 데이터
    % subPlotList  : (옵션) subplot에 그릴 변수 목록
    % lastfigure   : (옵션) 그릴 subplot 개수
    % startfigure  : (옵션) subplot 시작 index

    %% 기본값 설정
    if nargin < 3 || isempty(mode)
        mode = 'fit';  % mode 생략 시 기본은 'fit'
    end

    if ~ischar(mode) || ~any(strcmpi(mode, {'fit', 'basis','bilinear'}))
        error('3번째 인수 mode는 ''fit'' 또는 ''basis'' 중 하나여야 합니다.');
    end

    % Data4Interp를 table로 변환
    if istable(Data4Interp)
        InputTable = Data4Interp;
    elseif isstruct(Data4Interp)
        [InputTable, ~] = createTableFromMCADSatuMapStr(Data4Interp);
    else
        error('Data4Interp는 table 또는 struct여야 합니다.');
    end

    if nargin < 7; startfigure = 1; end

    %% subplot 대상 변수 목록 자동 생성
    if nargin < 5 || isempty(subPlotList)
        varNames = InputTable.Properties.VariableNames;
        varUnits = InputTable.Properties.VariableUnits;

        if ~isempty(varUnits)
            nonAmpereIndex = (~strcmp(varUnits, 'A') & ~strcmp(varUnits, 'Amps')) & (~strcmp(varUnits, 'EDeg'));
            subPlotList = varNames(nonAmpereIndex);
        else
            subPlotList = varNames;
        end

        % 필터링
        subPlotList = removeCellwithMatchingStr(subPlotList, 'Sleeve_Loss');
        subPlotList = removeCellwithMatchingStr(subPlotList, 'Coefficient');

        % 그룹별 분류
        typeStrt.voltageCell = getCellwithMatchingStr(subPlotList, 'V');
        if isempty(typeStrt.voltageCell); typeStrt = rmfield(typeStrt, "voltageCell"); end

        IronLossCell = getCellwithMatchingStr(subPlotList, 'Iron');
        FE = getCellwithMatchingStr(subPlotList, 'FE');
        typeStrt.IronLossCell = [IronLossCell FE];
        if isempty(typeStrt.IronLossCell); typeStrt = rmfield(typeStrt, "IronLossCell"); end

        LossCell = getCellwithMatchingStr(subPlotList, 'Loss');
        LossCell = removeCellwithMatchingStr(LossCell, 'Fe');
        LossCell = removeCellwithMatchingStr(LossCell, 'AC_Copper_Loss_(C1)');
        typeStrt.LossCell = removeCellwithMatchingStr(LossCell, 'Iron');
        if isempty(typeStrt.LossCell); typeStrt = rmfield(typeStrt, "LossCell"); end

        otherCell = removeCellwithMatchingStr(subPlotList, 'Loss');
        typeStrt.otherCell = removeCellwithMatchingStr(otherCell, 'V');
        if isempty(typeStrt.otherCell); typeStrt = rmfield(typeStrt, "otherCell"); end
    end

    if nargin < 6 || isempty(lastfigure)
        lastfigure = length(subPlotList);
    end

    %% 보간 or basis 생성
    FitResultStr = struct();
    index = 1;

    for i = 1:lastfigure
        varName = subPlotList{i};
        
         switch lower(mode)
            case 'fit'
                % [tempFitResult, ~, tempSingleDataSet, output] = createInterpDataSetofStrWithFieldName(InputTable, varName);
                [tempFitResult, ~, tempSingleDataSet] = createInterpDataSetofStrWithFieldName(InputTable, varName);

            case 'bilinear'
                % [tempFitResult, ~, tempSingleDataSet] = createInterpDataSetofStrWithFieldName_bilinear(InputTable, varName);
            % [tempFitResult, gof, tempSingleDataSet] = createInterpDataSetofStrWithFieldName_interp2(InputTable, varName);
                [tempFitResult, gof, tempSingleDataSet, coeffsTable] = createInterpDataSetofStrWithFieldName_bilinearCoeffs(InputTable, varName);
            case 'basis'
                model = BasisModel('thinplate');
                model.maskConvexHull = true;
                [~, tempFitResult, tempSingleDataSet, testObj] = model.fitFromTable(InputTable, varName);
                FitResultStr(index).bestModel = testObj;
        end


        if ~isempty(tempFitResult) && ~isempty(tempSingleDataSet)
            FitResultStr(index).fitResult = tempFitResult;
            FitResultStr(index).singleDataSet = tempSingleDataSet;
            FitResultStr(index).varNames = varName;
             index = index + 1;
        end
    end

    %% 타입별로 subplot 시각화
    typestrtNames = fieldnames(typeStrt);
    for cellIndex = 1:length(typestrtNames)
        cellName = typestrtNames{cellIndex};
        if ~isempty(typeStrt.(cellName))
            structbyType.(cellName) = filterWithFieldValueStruct(FitResultStr, 'varNames', typeStrt.(cellName));
            structbyTypeNames = fieldnames(structbyType);
        end
    end

    for strctIndex = 1:length(structbyTypeNames)
        structName = structbyTypeNames{strctIndex};
        cellName = typestrtNames{strctIndex};
        plotSubPlotbyStructAndstrCell(plotFunction, structbyType.(structName), typeStrt.(cellName));
    end

    %% subplot 스타일 통일
    figHandles = findobj('type', 'figure');
    setSubplotFontProperties(figHandles, 'Times New Roman', 8);
end
