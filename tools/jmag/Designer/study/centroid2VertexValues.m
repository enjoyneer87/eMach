function vertexValues = centroid2VertexValues(TR, eleType, eleCenter, elementValues)
    % TR: triangulation 객체 (삼각형 및 사각형 요소가 나누어진 상태)
    % eleType: 요소 유형 (사각형: 3, 삼각형: 2 등)
    % eleCenter: 요소 중심 좌표 (Nx2 또는 Nx3 행렬)
    % elementValues: 각 요소에서의 물리량 값 (사각형 및 삼각형 모두 포함)
    
    triangles = TR.ConnectivityList;
    numVertices = size(TR.Points, 1);  % 전체 노드 개수
    vertexValues = zeros(numVertices, 1);  % 꼭짓점에 할당할 값을 저장할 배열
    vertexCount = zeros(numVertices, 1);  % 각 꼭짓점이 연결된 삼각형 개수를 카운트할 배열
    
    expandedElementValues = [];  % 초기화: 사각형에서 변환된 값 저장용
    
    % 사각형 요소가 있는 경우 처리 (사각형을 먼저 처리)
    if any(eleType == 3)  % 사각형 요소가 존재하는 경우
        quadElementValues = elementValues(eleType == 3);  % 사각형 요소 값
        quadElementCenters = eleCenter(eleType == 3, :);  % 사각형 요소 중심
        
        % 사각형 요소를 삼각형으로 나눠서 처리
        expandedElementValues = QuadEleValues2TriValues(TR, quadElementCenters, quadElementValues);  % 삼각형으로 변환된 값

        % 삼각형으로 변환된 사각형 요소 값을 꼭짓점에 더함
        for i = 1:size(expandedElementValues, 1)  % 사각형 요소만 처리
            vertexIndices = triangles(i, :);  % 삼각형 꼭짓점
            vertexValues(vertexIndices) = vertexValues(vertexIndices) + expandedElementValues(i);
            vertexCount(vertexIndices) = vertexCount(vertexIndices) + 1;
        end
    end
    
    % 삼각형 요소만 있는 경우 처리
    if any(eleType == 2)  % 삼각형 요소가 존재하는 경우
        triElementIndices = find(eleType == 2);  % 삼각형 요소의 인덱스만 추출
        triElementValues = elementValues(eleType == 2);  % 삼각형 요소 값
        triElementCenters = eleCenter(eleType == 2, :);  % 삼각형 요소 중심

        % 삼각형 요소 값을 꼭짓점에 더함
        for i = 1:length(triElementIndices)  % 추출된 삼각형 요소 인덱스만 처리
            elementIndex = triElementIndices(i);  % 실제 삼각형 요소의 인덱스
            vertexIndices = triangles(elementIndex, :);  % 삼각형 꼭짓점
            vertexValues(vertexIndices) = vertexValues(vertexIndices) + triElementValues(i);
            vertexCount(vertexIndices) = vertexCount(vertexIndices) + 1;
        end
    end

    % 각 꼭짓점에 대해 연결된 삼각형 또는 사각형 값으로 평균 계산
    vertexValues = vertexValues ./ vertexCount;
end