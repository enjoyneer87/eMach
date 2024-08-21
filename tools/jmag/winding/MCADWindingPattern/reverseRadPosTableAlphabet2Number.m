function reNumberLayerTable = reverseRadPosTableAlphabet2Number(curCoilGroupTable)
    reNumberLayerTable = curCoilGroupTable;   
    %% RadialPosition 데이터를 가져옴
    tempRadialPositionTable = curCoilGroupTable(:, contains(curCoilGroupTable.Properties.VariableNames, 'RadialPosition'));
    %% 카테고리형을 문자형으로 변환
    tempRadialPosition = cellstr(tempRadialPositionTable{:,:});
    %%소문자 알파벳을 숫자로 변환
    numericArray = cellfun(@(x) double(x) - double('a') + 1, tempRadialPosition);
    %% 숫자로 변환된 데이터를 다시 카테고리형으로 변환
    categoryArray = categorical(numericArray);
    %% 테이블에 반영
    logicalIndex = contains(curCoilGroupTable.Properties.VariableNames, 'RadialPosition');
    reNumberLayerTable{:, logicalIndex} = categoryArray;
end