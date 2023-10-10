function EffiTable = renameVariableByName(EffiTable, varNames, newName)
    if class(varNames) =='char' 
        EffiTable.Properties.VariableNames{ismember(EffiTable.Properties.VariableNames, varNames)} = newName;
    elseif numel(varNames) > 1
        error('여러 개의 변수를 찾았습니다. 하나의 변수만 대상으로 이름을 변경해주세요.');
    else
        warning('변수를 찾을 수 없습니다.');
    end
end