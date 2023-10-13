function indices = findClosestDataIndices(dataArray, value2Find, tolerance)
    % B_array에서 B_value와의 차이가 tolerance 이내인 모든 요소의 인덱스를 찾음
    % tolerance는 선택적 인자로, 제공되지 않으면 기본값으로 1e-5를 사용

    if nargin < 3
        tolerance = 1e-5;
    end
    
    % B_value와 가까운 값들의 논리 배열 생성
    isClose = abs(dataArray - value2Find) <= tolerance;

    % 논리 배열에 따른 인덱스 반환
    indices = find(isClose);
end
