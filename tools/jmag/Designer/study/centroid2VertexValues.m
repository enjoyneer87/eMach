function vertexValues = centroid2VertexValues(tr, elementValues)
    % tr: triangulation 객체 (삼각형 구성 정보 포함)
    % elementValues: 각 삼각형 요소에서의 값 (예: 요소 중심에서의 물리량)
    
    % 삼각형의 구성 정보와 노드 정보 가져오기
    triangles = tr.ConnectivityList;
    numVertices = size(tr.Points, 1);  % 전체 노드 개수
    
    % 각 노드에 할당될 값을 저장할 배열 (초기값은 0)
    vertexValues = zeros(numVertices, 1);
    
    % 각 노드가 연결된 삼각형 개수를 카운트할 배열
    vertexCount = zeros(numVertices, 1);
    
    % 각 삼각형의 중심값(elementValues)을 인접한 꼭짓점에 더해줌
    for i = 1:size(triangles, 1)
        vertexIndices = triangles(i, :);  % 현재 삼각형의 꼭짓점 인덱스
        vertexValues(vertexIndices) = vertexValues(vertexIndices) + elementValues(i);
        vertexCount(vertexIndices) = vertexCount(vertexIndices) + 1;
    end
    
    % 각 꼭짓점에 대해 연결된 삼각형의 값으로 평균 계산
    vertexValues = vertexValues ./ vertexCount;
end