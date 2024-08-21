function CoilPropertiesTable=mkCoilPropertiesTable(slotArray,NumTotalCoilsTable)
    numVariables = length(slotArray);
    numRows = 2;
    % 빈 테이블 생성
    emptyStr = repmat({' '}, numRows, numVariables);
    CoilPropertiesTable = cell2table(emptyStr);
    % 변수 이름 설정 (앞에 'Slot'을 붙임)
    variableNames = cellfun(@(x) sprintf('Slot%d', x), num2cell(1:numVariables), 'UniformOutput', false);
    CoilPropertiesTable.Properties.VariableNames = variableNames;
    %%
    CoilPropertiesTable.Slot1{1}    ='ReadPropertiesTab';
    CoilPropertiesTable.Slot1{2}    ='NumCoils'         ;
    CoilPropertiesTable.Slot2{1}    ='0'                ;
    CoilPropertiesTable.Slot2{2}    =num2str(NumTotalCoilsTable);                   
end

