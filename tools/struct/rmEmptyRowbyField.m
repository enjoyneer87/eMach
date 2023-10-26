function PartStruct = rmEmptyRowbyField(PartStruct,fieldName)
emptyAreaIndices = [];
for i = 1:numel(PartStruct)
    if isempty(PartStruct(i).(fieldName))
        emptyAreaIndices = [emptyAreaIndices, i];
    end
end

% 찾은 인덱스를 사용하여 해당 행을 삭제
PartStruct(emptyAreaIndices) = [];
end