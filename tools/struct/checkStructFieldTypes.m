function checkStructFieldTypes(structData)
    % 구조체 필드명을 가져옵니다.
    fieldNames = fieldnames(structData);
    
    % 각 필드에 대해 반복하여 데이터 유형을 확인합니다.
    for i = 1:length(fieldNames)
        fieldName = fieldNames{i};  % 현재 필드명
        fieldValue = structData.(fieldName);  % 필드 값
        fieldType = class(fieldValue);  % 필드 값의 데이터 유형
        
        % 필드명과 데이터 유형을 출력합니다.
        fprintf('Field "%s" has type: %s\n', fieldName, fieldType);
    end
end
