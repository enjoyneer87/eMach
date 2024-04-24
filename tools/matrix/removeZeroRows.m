function B = removeZeroRows(A)
    % 모든 요소가 0인 행을 찾아서 삭제하는 함수
    % 입력:
    % A - 처리할 배열
    % 출력:
    % B - 0인 행이 삭제된 배열
    
    % 각 행에 대해 모든 요소가 0인지 검사하여 논리적 배열 생성
    rowsToDelete = all(A == 0, 2);
    
    % 논리적 인덱싱을 사용하여 0이 아닌 행만 남김
    B = A(~rowsToDelete, :);
end
