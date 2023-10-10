function newStruct = extractDoubleFields(inputStruct)
    % 입력 구조체의 필드 이름과 값을 저장할 새로운 구조체를 생성합니다.
    newStruct = struct();

    % 입력 구조체의 모든 필드에 대해 반복합니다.
    fields = fieldnames(inputStruct);
    for i = 1:numel(fields)
        % 현재 필드의 값을 가져옵니다.
        value = inputStruct.(fields{i});
        
        % 현재 필드의 값이 숫자형 데이터인지 확인하고 int32 형태가 아닌 경우만 처리합니다.
        if isnumeric(value) && ~isa(value, 'int32')
            % 숫자형 데이터인 필드의 이름과 값을 새로운 구조체에 저장합니다.
            newStruct.(fields{i}) = value;
        end
    end
end
