function newStruct = renameField(s, oldFieldName, newFieldName)
% 필드 이름 변경 함수
    if isfield(s, oldFieldName)
        [s.(newFieldName)] = s.(oldFieldName);
        s = rmfield(s, oldFieldName);
    else
        error('Field "%s" does not exist.', oldFieldName);
    end
    newStruct = s;
end