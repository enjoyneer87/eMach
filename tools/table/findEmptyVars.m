function isEmpty = findEmptyVars(tableData,nonEmpty)
    % findEmptyVars - 테이블에서 모든 값이 비어있는 변수를 찾습니다.
    %
    % tableData=resultTable(2,:)
    % 사용법:
    %   emptyVars = findEmptyVars(tableData)
    %
    % 입력 매개변수:
    %   tableData - 검사할 MATLAB 테이블
    %
    % 출력 매개변수:
    %   emptyVars - 모든 값이 비어있는 변수(열)의 이름 목록

    % 각 변수가 모두 비어있는지 확인하는 논리 배열 생성
    isEmpty = varfun(@(x) all(isEmptyCheck(x)), tableData, 'OutputFormat', 'uniform');
    if nargin>1&&nonEmpty==1
        isEmpty=~isEmpty;
    % % 비어있는 변수의 이름을 찾기
    end

    % emptyVars = tableData.Properties.VariableNames(~isEmpty);
    % end
    % emptyVars = tableData.Properties.VariableNames(isEmpty);
end