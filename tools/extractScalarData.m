function scalarStruct = extractScalarData(inputStruct)
    % 스칼라 데이터를 저장할 구조체를 초기화합니다.
    scalarStruct = struct();

    % 입력 구조체의 모든 필드에 대해 반복합니다.
    fields = fieldnames(inputStruct);
    for i = 1:numel(fields)
        % 현재 필드의 값을 가져옵니다.
        value = inputStruct.(fields{i});

        % 현재 필드의 값이 스칼라인지 확인합니다.
        if isscalar(value)
            % 스칼라 데이터를 새로운 구조체에 필드 이름으로 저장합니다.
            scalarStruct.(fields{i}) = value;
        end
    end
end
