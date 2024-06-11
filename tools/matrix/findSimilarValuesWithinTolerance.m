function valueIndicesStruct = findSimilarValuesWithinTolerance(valueArray, tolerance)
    % tolerance: 오차 허용 범위
    if nargin<2
        tolerance=1e-5;
    end
    % 검색할 열 추출
    % valueArray=RegionDataTable.Area
    columnData = valueArray;

    % uniquetol 함수를 사용하여 중복된 값을 처리하고 중복을 제거한 결과와 인덱스를 반환
    [uniqueSimilarValues, ~, indices] = uniquetol(columnData, tolerance, 'DataScale', 1);

    % 각 고유한 값에 해당하는 인덱스들을 저장할 셀 배열 초기화
    valueIndicesCell = cell(size(uniqueSimilarValues));

    % 각 값에 대한 인덱스 찾기
    for i = 1:numel(uniqueSimilarValues)
        valueIndicesCell{i} = find(indices == i);
    end

    % 두 개 이상의 값을 가지는 행들과 해당 uniqueSimilarValues를 구조체로 만들기
    valueIndicesStruct = struct();
    for i = 1:numel(uniqueSimilarValues)
        if numel(valueIndicesCell{i}) >= 2
            valueIndicesStruct(i).Values = uniqueSimilarValues(i);
            valueIndicesStruct(i).Indices = valueIndicesCell{i};
        end
    end

    if ~isempty(fields(valueIndicesStruct))
    % 빈 구조체 제거
    emptyStructs = arrayfun(@(x) isempty(x.Values), valueIndicesStruct);
    valueIndicesStruct(emptyStructs) = [];
    else
    valueIndicesStruct=[];    
    end
end


