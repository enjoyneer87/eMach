function totalSum = sumFieldsWithEqualSize(structArray, fieldNames)
    % structArray: 필드를 더할 구조체 배열
    % fieldNames: 크기가 동일한 필드 이름을 포함한 셀 배열

    % 모든 구조체의 크기를 저장할 변수 초기화
    totalSize = [];

    % 각 구조체의 크기를 가져와 저장
    for i = 1:numel(structArray)
        % 각 구조체에서 필드의 크기 가져오기
        fieldSizes = cellfun(@(fieldName) size(structArray(i).(fieldName)), fieldNames, 'UniformOutput', false);

        % 필드 크기가 동일한지 확인
        if all(cellfun(@(x) isequal(x, fieldSizes{1}), fieldSizes))
            totalSize = fieldSizes{1};
            break;
        end
    end

    % 동일한 크기의 필드 값을 더하기
    totalSum = zeros(totalSize);
    for i = 1:numel(structArray)
        for j = 1:numel(fieldNames)
            fieldData = structArray(i).(fieldNames{j});
            % NaN 값을 0으로 처리
            fieldData(isnan(fieldData)) = 0;
            totalSum = totalSum + fieldData;
        end
    end
end
