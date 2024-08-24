function TableWithGroups = groupCoilsByConsecutiveNumbers(TotalCoilTable)
    
    % CoilNumber 추출
    if iscell(TotalCoilTable.CoilNumber)
    CoilNumbers = cell2mat(TotalCoilTable.CoilNumber);
    else
    CoilNumbers=TotalCoilTable.CoilNumber;
    end
    % CoilNumbers가 연속적인지 확인
    diffCoils = [true; diff(CoilNumbers) ~= 1]; % 연속되지 않는 첫 번째 요소는 true로 표시
    groupIdx = cumsum(diffCoils); % 각 연속 그룹에 고유 인덱스 할당

    % 그룹 번호를 테이블에 추가
    TotalCoilTable.GroupNumber = groupIdx;

    % 그룹별로 테이블 분류
    TableWithGroups = sortrows(TotalCoilTable, 'GroupNumber');

end