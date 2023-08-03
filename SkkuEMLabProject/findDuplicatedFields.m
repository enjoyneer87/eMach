function duplicatedFieldsStruct = findDuplicatedFields(struct1, struct2)
    % 중복된 필드를 저장할 구조체 초기화
    duplicatedFieldsStruct = struct();

    % 두 번째 구조체의 필드들 검사하여 중복된 필드 저장
    fields2 = fieldnames(struct2);
    for i = 1:numel(fields2)
        if isfield(struct1, fields2{i})
            duplicatedFieldsStruct.(fields2{i}) = {struct1.(fields2{i}), struct2.(fields2{i})};
        end
    end
end
