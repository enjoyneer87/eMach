function modifiedDataStruct=getMcadVariableTableFromMotFile(MotFilePath)
    load("mcadActiveXparameterList.mat");
    modifiedData=getDataFromMotFiles(MotFilePath);
    % modifiedDataStruct 구조체 초기화
    modifiedDataStruct = struct();
% 확인 및 저장을 위한 코드
for i = 1:numel(modifiedData)
    parts = strsplit(modifiedData{i}, '.');

    if numel(parts) > 1
        tableName = parts{1};

        if isfield(ActiveXParametersStruct, tableName)
            expressionParts = strsplit(parts{2}, '=');
            variableName = strtrim(expressionParts{1});
            value = strtrim(expressionParts{2});
            % 해당 fieldName의 테이블 참조
            targetTable = ActiveXParametersStruct.(tableName);
            if ~isfield(modifiedDataStruct, tableName)
                modifiedDataStruct.(tableName) = targetTable;
                cululatedIndex=[];
            end
            Index = findMatchingIndex(targetTable.AutomationName, variableName);
            if ~isempty(Index) % Index가 비어 있지 않으면 실행
                modifiedDataStruct.(tableName).CurrentValue{Index} = value;
                modifiedDataStruct.(tableName).DefaultValue{Index} = 'This is From Mot File';
                cululatedIndex=[cululatedIndex;Index];
            end
        else
            % disp([modifiedData{i}, '은(는) ActiveXParametersStruct의 필드가 아닙니다.']);
        end
    else
        % disp([modifiedData{i}, '은(는) 올바른 형식이 아닙니다.']);
    end
    
end


end
