function combinedStruct=mergestruct(struct1,struct2)

mergeStruct

% 구조체 합치기
fieldNames1 = fieldnames(struct1);
fieldNames2 = fieldnames(struct2);

for i = 1:numel(fieldNames2)
    fieldName = fieldNames2{i};
    struct1.(fieldName) = struct2.(fieldName);
end

combinedStruct = struct1;

end
