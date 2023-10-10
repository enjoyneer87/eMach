function hasSpecifiedTypeField = checkForSpecifiedTypeFields(inputStruct, targetType)
    % 구조체 내의 모든 필드를 반복 순회
    fieldNames = fieldnames(inputStruct);
    hasSpecifiedTypeField = false;

    for i = 1:numel(fieldNames)
        fieldName = fieldNames{i};
        fieldValue = inputStruct.(fieldName);

        % 필드 값이 지정된 데이터 타입인 경우
        if isa(fieldValue, targetType)
            disp(['구조체 필드 ' fieldName ' 가 ' targetType ' 타입입니다.']);

            % 구조체 내의 다른 필드를 확인하지 않고 바로 반환
            hasSpecifiedTypeField = true;
            return;
        elseif isstruct(fieldValue)
            % 필드 값이 구조체인 경우 구조체 내의 필드를 확인 (재귀 호출)
            hasSpecifiedTypeField = checkForSpecifiedTypeFields(fieldValue, targetType) || hasSpecifiedTypeField;
        end
    end
end
