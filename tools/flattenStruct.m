function flattenedStruct = flattenStruct(inputStruct)
    fieldNames = fieldnames(inputStruct); % 구조체 필드 이름들을 얻습니다.
    
    % 각 필드를 반복하고 행렬인 경우 평탄화합니다.
    for i = 1:numel(fieldNames)
        fieldName = fieldNames{i};
        fieldValue = inputStruct.(fieldName);
        
        % 필드가 행렬인지 확인합니다.
        if ismatrix(fieldValue)
            % 행렬을 평탄화합니다.
            flattenedMatrix = flattenMatrix(fieldValue);
            % 결과를 새로운 구조체에 저장합니다.
            flattenedStruct.(fieldName) = flattenedMatrix;
        else
            % 행렬이 아닌 경우 그대로 복사합니다.
            flattenedStruct.(fieldName) = fieldValue;
        end
    end
end
