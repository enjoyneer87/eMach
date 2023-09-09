function [uniqueFields, commonFields] = findUniqueFields(struct1, struct2)
    % struct1과 struct2의 필드 이름을 가져옵니다.
    fields1 = fieldnames(struct1);
    fields2 = fieldnames(struct2);

    % struct1과 struct2의 유니크한 필드를 찾습니다.
    uniqueFields1 = setdiff(fields1, fields2);
    uniqueFields2 = setdiff(fields2, fields1);

    % struct1과 struct2의 공통 필드를 찾습니다.
    commonFields = intersect(fields1, fields2);

    % 결과를 반환합니다.
    uniqueFields = struct();
    for i = 1:numel(uniqueFields1)
        uniqueFields.(uniqueFields1{i}) = struct1.(uniqueFields1{i});
    end
    for i = 1:numel(uniqueFields2)
        uniqueFields.(uniqueFields2{i}) = struct2.(uniqueFields2{i});
    end
end
