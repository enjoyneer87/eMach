function varargout = mergeStructs(struct1, struct2)
    % 합쳐진 구조체 초기화
    mergedStruct = struct();
    
    duplicatedFieldsStruct = findDuplicatedFields(struct1, struct2); % 중복 필드 찾기

    % 첫 번째 구조체의 필드들 추가
    fields1 = fieldnames(struct1);
    for i = 1:numel(fields1)
        mergedStruct.(fields1{i}) = struct1.(fields1{i});
    end
    
    % 두 번째 구조체의 필드들 추가
    fields2 = fieldnames(struct2);    
    if isempty(duplicatedFieldsStruct)
    % 중복된 필드가 없는 경우, 두 번째 구조체의 필드를 추가
        nargout = 1;
        for i = 1:numel(fields2)
            mergedStruct.(fields2{i}) = struct2.(fields2{i});
        end
    else
    % 중복된 field가 있으면 두번째 구조체의 값으로 덮어씌워짐
        nargout = 2;
        for i = 1:numel(fields2)
            mergedStruct.(fields2{i}) = struct2.(fields2{i});
        end        
    end
    
    % 출력 변수 설정
    if nargout > 1
        varargout{1} = mergedStruct;
        varargout{2} = duplicatedFieldsStruct;
    else
        varargout{1} = mergedStruct;
    end
end
