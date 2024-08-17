function [uniqueStruct1, uniqueStruct2] = removeDuplicatedFields(struct1, struct2)
    % 중복된 필드 제거한 새로운 구조체 초기화
    uniqueStruct1 = struct();
    uniqueStruct2 = struct();
    
    % 첫 번째 구조체의 필드들 추가 (두 번째 구조체와 중복되지 않은 필드만 추가)
    fields1 = fieldnames(struct1);
    for i = 1:numel(fields1)
        if ~isfield(struct2, fields1{i})
            uniqueStruct1.(fields1{i}) = struct1.(fields1{i});
        end
    end
    
    % 두 번째 구조체의 필드들 추가 (첫 번째 구조체와 중복되지 않은 필드만 추가)
    fields2 = fieldnames(struct2);
    for i = 1:numel(fields2)
        if ~isfield(struct1, fields2{i})
            uniqueStruct2.(fields2{i}) = struct2.(fields2{i});
        end
    end
end
