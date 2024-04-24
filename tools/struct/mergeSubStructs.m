function mergedStruct = mergeSubStructs(parentStruct)
    % 모든 하위 구조체의 필드를 하나의 구조체로 합치는 함수
    % parentStruct: 하위 구조체들을 필드로 가지는 상위 구조체

    % 결과를 저장할 빈 구조체 초기화
    mergedStruct = struct();

    % parentStruct의 각 필드(하위 구조체)에 대해 반복
    subStructFields = fieldnames(parentStruct);
    for i = 1:length(subStructFields)
        currentStruct = parentStruct.(subStructFields{i});
        
        % 현재 하위 구조체의 각 필드를 mergedStruct에 병합
        currentFields = fieldnames(currentStruct);
        for j = 1:length(currentFields)
            fieldName = currentFields{j};
            fieldValue = currentStruct.(fieldName);
            
            % 중복 필드가 있을 경우 나중에 오는 값으로 덮어씀
            mergedStruct.(fieldName) = fieldValue;
        end
    end
end
