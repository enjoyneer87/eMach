function updatedTri = filterDelaunayByIncenter(nodeCoords, elementCenters)
    % nodeCoords: 노드 좌표 리스트 (nx2 배열, 각 행이 노드의 좌표 [x, y])
    % elementCenters: 주어진 요소 중앙 위치 배열 (mx2 배열)
    % nodeCoords=slotNodeCoord
    % elementCenters=slotElementCoord
    % % 1. Delaunay 삼각분할 생성
    tri = delaunayTriangulation(nodeCoords);
    
    % 2. Delaunay 삼각형의 Incenter 계산
    [incenterCoords, r] = incenter(tri);  % 각 삼각형의 incenter 계산

    % 3. 주어진 요소 중심 위치와 incenter 비교
    tolerance = 1e-1;  % 비교에 사용할 허용 오차
    matchedTriangles = false(size(incenterCoords, 1), 1);  % 일치하는 삼각형 여부

    for i = 1:size(elementCenters, 1)
        % 주어진 요소 중심과 각 incenter 사이의 거리를 계산
        distances = sqrt(sum((incenterCoords - elementCenters(i, :)).^2, 2));

        % 허용 오차 내에서 일치하는 삼각형 찾기
        matchedTriangles = matchedTriangles | (distances < tolerance);
    end

    % 4. 일치하는 삼각형만 남겨서 업데이트된 Delaunay 삼각형 생성
    updatedTri = triangulation(tri.ConnectivityList(matchedTriangles, :), nodeCoords);
end