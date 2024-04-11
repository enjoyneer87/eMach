function modifiedDataStruct = getMcadActiveXTableFromMotFile(MotFilePath)
    load("mcadActiveXparameterList.mat");
    modifiedData = getDataFromMotFiles(MotFilePath);
    % modifiedDataStruct 구조체 초기화
    modifiedDataStruct = struct();

    % 각 tableName에 대한 CurrentValue를 초기화
    tableNames = fieldnames(ActiveXParametersStruct);
    for tableIndex = 1:numel(tableNames)
        tableName = tableNames{tableIndex};
        tableCategory = ActiveXParametersStruct.(tableName);
        nVariables = numel(tableCategory.AutomationName);
        modifiedDataStruct.(tableName) = tableCategory;
        modifiedDataStruct.(tableName).CurrentValue = cell(nVariables,1);
        % modifiedDataStruct.(tableName).DefaultValue = repmat({'This is From Mot File'}, nVariables, 1);
    end

%%  
    for lineIndex = 1:numel(modifiedData)
        line = modifiedData{lineIndex};
        dotIndex = find(line == '.', 1, 'first'); % 첫 번째 '.'의 위치 찾기
        
        if ~isempty(dotIndex)
            % 첫 번째 '.'을 기준으로 문자열 나누기
            tableName = strtrim(line(1:dotIndex-1)); % '.' 이전 부분
            restOfLine = strtrim(line(dotIndex+1:end)); % '.' 이후 부분
            
            if isfield(modifiedDataStruct, tableName)  
                expressionParts = strsplit(restOfLine, '=');
                if numel(expressionParts) == 2
                    AutomationName = strtrim(expressionParts{1});
                    value = strtrim(expressionParts{2});
    
                    % [숫자] 감지 및 처리 로직은 이전과 동일
                      % 대괄호 위치 찾기
                    openBracketPos = find(AutomationName == '[', 1, 'first');
                    closeBracketPos = find(AutomationName == ']', 1, 'first');
                    if ~isempty(openBracketPos) && ~isempty(closeBracketPos)
                        indexStr = AutomationName(openBracketPos+1:closeBracketPos-1);
                        indexNum = str2double(indexStr);
                        if ~isnan(indexNum) % 숫자가 감지된 경우
                            AutomationName = AutomationName(1:openBracketPos-1); % [숫자] 제거
                        end
                    end
    
                    Index = findMatchingIndex(modifiedDataStruct.(tableName).AutomationName, AutomationName, 'exact');
                    
                    if ~isempty(Index)
                        currentValues = modifiedDataStruct.(tableName).CurrentValue{Index};
                        if isempty(currentValues)
                            newValues = value;  
                        else
                            newValues = strjoin([currentValues(:)', {value}], ':');
                        end
                        modifiedDataStruct.(tableName).CurrentValue{Index} = {newValues};
                    end
                end
            end
        end
    end
%%
end



