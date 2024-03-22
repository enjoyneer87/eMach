function WireStruct = updatePartStructWithFieldTable(WireStruct, FieldTable, tableNameAsString)
    % BfftMagTable의 변수 이름을 가져옵니다.
    varNames = FieldTable.Properties.VariableNames;
    if contains(tableNameAsString,'B')||contains(tableNameAsString,'Element','IgnoreCase',true)
    StructField2Check='ElementId';
    elseif strcmp(tableNameAsString,'A')||contains(tableNameAsString,'Node','IgnoreCase',true)
    StructField2Check='NodeId';
    
    end

    % 각 변수에 대해 반복합니다.
    for iVar = 1:length(varNames)
        varName = varNames{iVar};
        % 변수 이름에서 숫자를 추출합니다.
        match = regexp(varName, '.*x(\d+)$', 'tokens');
        if ~isempty(match)
            % 추출한 숫자를 기반으로 targetValue를 설정합니다.
            targetValue = str2double(match{:});
            
            % 해당 ElementId를 가진 WireStruct의 인덱스를 찾습니다.
            matchingIndicesOfStruct = findMatchingIndexInStruct(WireStruct, StructField2Check, targetValue);
            
            % 일치하는 각 구조체에 대해 새로운 필드 데이터를 추가합니다.
            % 이미 해당 필드가 있는지 확인하고, 새로운 데이터를 추가합니다.
            if isfield(WireStruct(matchingIndicesOfStruct), tableNameAsString)
                % 해당 필드가 이미 있으면, 새로운 변수를 추가합니다.
                currentTable = WireStruct(matchingIndicesOfStruct).(tableNameAsString);
                newTable = [currentTable FieldTable(:, iVar)];
                WireStruct(matchingIndicesOfStruct).(tableNameAsString) = newTable;
            else
                % 해당 필드가 없으면 새로 생성합니다.
                WireStruct(matchingIndicesOfStruct).(tableNameAsString) = FieldTable(:, iVar);
            end
        end
    end
end
