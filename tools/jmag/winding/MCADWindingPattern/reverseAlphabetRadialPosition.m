function reNumberLayerTable = reverseAlphabetRadialPosition(McadWindingPatternTable)
    %% 원본 테이블 복사
    reNumberLayerTable = McadWindingPatternTable;    
    %% RadialPosition 데이터를 가져옴
    tempRadialPosition = McadWindingPatternTable(contains(McadWindingPatternTable.TypeofData, 'RadialPosition'), 'ValueTable');    
    %% 알파벳을 숫자로 변환
    numericArray = cellfun(@(x) double(x) - 'a' + 1, tempRadialPosition.Variables, 'UniformOutput', false);    
    %% RadialPosition 데이터를 숫자로 변경
    logicalIndex = contains(McadWindingPatternTable.TypeofData, 'RadialPosition');
    reNumberLayerTable.ValueTable(logicalIndex) = numericArray;
end