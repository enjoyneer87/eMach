function reNumberLayerTable = renumberRadialPositionNumber(McadWindingPatternTable)
    reNumberLayerTable = McadWindingPatternTable;    
    %% RadialPosition 데이터를 가져옴
    tempRadialPosition = McadWindingPatternTable(contains(McadWindingPatternTable.TypeofData,'RadialPosition'),'ValueTable');    
    %% 숫자로 변환 후 1 증가
    tempRadialPosition = str2double(tempRadialPosition.Variables) + 1;    
    %% 숫자를 소문자 알파벳으로 변환
    strCellArray = arrayfun(@(x) char('a' + x - 1), tempRadialPosition, 'UniformOutput', false);
    %% RadialPosition 데이터를 알파벳으로 변경
    logicalIndex = contains(McadWindingPatternTable.TypeofData, 'RadialPosition');
    reNumberLayerTable.ValueTable(logicalIndex) = strCellArray;
end