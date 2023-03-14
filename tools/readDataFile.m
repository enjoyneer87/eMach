function [dataTable, nameCell, unitCell] = readDataFile(filepath, NumVariables)

    % 파일 확장자 추출
    [~,~,ext] = fileparts(filepath);

    if strcmp(ext,'.csv')
        % CSV 파일인 경우
        % 파일 옵션 지정
        fileOpts = delimitedTextImportOptions("NumVariables", NumVariables, "Encoding", "UTF-8");
        fileOpts.DataLines = [1, inf];
        fileOpts.Delimiter = ",";
        fileOpts.VariableTypes = repmat({'char'}, 1, NumVariables);
        fileOpts.ExtraColumnsRule = "ignore";
        fileOpts.EmptyLineRule = "read";
    
        % 데이터 가져오기
        dataInfoTable = readtable(filepath, fileOpts);
    
        % 데이터 전처리
        nameCell = table2cell(dataInfoTable(1,:));
        if height(dataInfoTable) > 1
            unitCell = table2cell(dataInfoTable(2,:));
        else
            unitCell = [];
        end
    
        dataOpts = delimitedTextImportOptions("NumVariables", NumVariables, "Encoding", "UTF-8");
        dataOpts.DataLines = [3, inf];
        dataOpts.Delimiter = ",";
        dataOpts.VariableTypes = repmat({'double'}, 1, NumVariables);
        dataOpts.ExtraColumnsRule = "ignore";
        dataOpts.EmptyLineRule = "read";
    
        dataTable = readtable(filepath, dataOpts);
    
        % NaN 값을 가지는 열 제거
        dataArr = table2array(dataTable);
        nanCols = any(isnan(dataArr), 1);
        clear dataArr
        dataTable = dataTable(:, ~nanCols);
        nameCell = nameCell(:, ~nanCols);
        if ~isempty(unitCell)
            unitCell = unitCell(:, ~nanCols);
        end
    
        % 열 이름 설정
        dataTable.Properties.VariableNames = nameCell;


    elseif strcmp(ext,'.mat')
        % MAT 파일인 경우
        loadedData = load(filepath);
        varNames = fieldnames(loadedData);
        dataCells = cell(1, numel(varNames));

        % 필드의 값을 cell 형태로 변환
        for i = 1:numel(varNames)
            varData = loadedData.(varNames{i});
            if istable(varData)
                if isequal(size(varData), size(dataCells{1})) && isequal(varData.Properties.VariableNames, dataCells{1}.Properties.VariableNames)
                    dataCells{i} = varData;
                else
                    error('Tables in MAT file must have same size and variable names.');
                end
            elseif isnumeric(varData)
                % 매트릭스인 경우 평활화(flatten)
                if ~isvector(varData)
                    varData = varData(:);
                end
                % 길이가 같은 데이터끼리 묶어주기
                len = length(varData);
                dataCells{i} = [varData(:); NaN(max(len)-len,1)];
            else
                dataCells{i} = varData;
            end
        end

        % cell들의 길이 구하기
        len = cellfun(@length, dataCells);

        % 길이가 같은 cell끼리 묶어서 테이블 만들기
        uniqueLen = unique(len);
        tables = cell(1, numel(uniqueLen));
        for i = 1:numel(uniqueLen)
            sameLenCells = dataCells(len == uniqueLen(i));
            tables{i} = cell2table(sameLenCells);
                       testTable = cell2table(sameLenCells);

            tableData = cell(numel(sameLenCells), numel(varNames{i}));
            for j = 1:numel(sameLenCells)
                for k = 1:numel(varNames)
                    tableData{j,k} = sameLenCells{j}.(varNames{k});
                end
            end
            
            tables{i}.Properties.VariableNames = varNames;
        end
    
    
    else
        error('Unsupported file extension. Only .csv and .mat files are supported.')
    end

end