function matchingStructIndices = findStructsWithValue(structArray, fieldName, targetValue)
% 구조체 배열에서 특정 필드 값이 주어진 값과 일치하는 구조체의 인덱스를 찾는 함수

% 일치하는 구조체의 인덱스 초기화
matchingStructIndices = [];

% 구조체 배열 전체를 순회
for i = 1:length(structArray)
    % 현재 구조체에서 지정된 필드의 값이 타겟 값과 일치하는지 확인
    if any(structArray(i).(fieldName) == targetValue)
        % 일치한다면 인덱스를 저장
        matchingStructIndices = [matchingStructIndices, i];
    end
end
end
