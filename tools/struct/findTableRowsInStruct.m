function tableRowsStr = findTableRowsInStruct(structArray)
    % struct 배열에서 'class' 필드의 값이 'table'인 행을 찾기
    tableRowsStr = structArray(strcmp({structArray.class}, 'table'));
end
