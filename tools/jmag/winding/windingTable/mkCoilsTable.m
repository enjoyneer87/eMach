function CoilsTable=mkCoilsTable(slotArray,LayerArray)
    %% JMAG Winding - Coils Table Fortmat
    %% 변수와 행 개수 설정
    NumSlots        =length(slotArray);      %numVariables    =NumSlots;
    NumRadPosition  =length(LayerArray);     %numRows         =NumRadPosition
    %% 빈 테이블 생성
    emptyCharCell = repmat({' '}, NumRadPosition, NumSlots);
    CoilsTable = cell2table(emptyCharCell);
    %% 변수 이름 설정 (앞에 'Slot'을 붙임)
    variableNames = cellfun(@(x) sprintf('Slot%d', x), num2cell(1:NumSlots), 'UniformOutput', false);
    CoilsTable.Properties.VariableNames = variableNames;
    % %% 행 이름 설정 (예: Layer1, Layer2, ...)
    % rowNames = cellfun(@(x) sprintf('Layer%d', x), num2cell(1:NumRadPosition), 'UniformOutput', false);
    % CoilsTable.Properties.RowNames = rowNames;
end

%% csvPath='Z:\Thesis\00_Theory_Prof\JFTZIP\JFT145WindingEditorParallel\JFT145WindingEditorParallel'
