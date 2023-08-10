function ActiveXParametersStruct = sortRowsTableinStruct(ActiveXParametersStruct)
    % 'Input_Output' 변수에 맞춰 내림차순으로 정렬
    for fieldName = fieldnames(ActiveXParametersStruct)'
        tableName = fieldName{1}; % 구조체 내 테이블 이름
        table = ActiveXParametersStruct.(tableName);
        
        % 'Input_Output' 열을 기준으로 테이블 정렬
        table = sortrows(table, 'Input_Output', 'ascend');
        
        % 구조체에 정렬된 테이블 다시 할당
        ActiveXParametersStruct.(tableName) = table;
    end
end