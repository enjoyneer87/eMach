function modifiedTable = replaceTableNamebyCell(changedOriginalTable, currentNameCell, NewNameCell)
    % 변수 이름을 가져옴
    varNames = changedOriginalTable.Properties.VariableNames;
    
    % LossCoefficientCell과 LabLinkCell의 길이 확인
    if length(currentNameCell) ~= length(NewNameCell)
        error('LossCoefficientCell과 LabLinkCell의 길이가 일치하지 않습니다.');
    end
    
    % 변수 이름 중에 LossCoefficientCell의 값을 가진 변수를 찾아서 LabLinkCell의 값을 할당
    for i = 1:length(currentNameCell)
            matchingIndex=find(strcmp(currentNameCell{i},varNames));
            changedOriginalTable.Properties.VariableNames{matchingIndex} = NewNameCell{i};
    end
    
    % 수정된 테이블 반환
    modifiedTable = changedOriginalTable;
end
