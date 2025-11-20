function quadMesh = findNearestNodes4quadMesh(nodes, elementCenters)
    % nodes: 전체 노드 좌표 리스트 (nx2 배열)
    % elementCenters: 요소 중심 좌표 리스트 (mx2 배열)
    %
    % quadMesh: 4개의 노드로 이루어진 사각형 요소 리스트 (mx4)

    numCenters = size(elementCenters, 1);
    quadMesh = zeros(numCenters, 4);  % 사각형 요소를 저장할 배열
    
    % 1. 각 요소 중심에 대해 가장 가까운 4개의 노드를 찾음
    for i = 1:numCenters
        center = elementCenters(i, :);
        
        % 각 중심점에서 모든 노드에 대한 거리를 계산
        distances = vecnorm(nodes - center, 2, 2);
        
        % 가장 가까운 4개의 노드 인덱스를 찾음
        [~, closestNodeIndices] = mink(distances, 4);
        
        % 2. 가장 가까운 4개의 노드를 시계 방향으로 정렬
        selectedNodeCoords = nodes(closestNodeIndices, :);
        angles = atan2(selectedNodeCoords(:, 2) - center(2), selectedNodeCoords(:, 1) - center(1));
        [~, angleOrder] = sort(angles);  % 시계 방향으로 정렬
        
        % 3. 정렬된 노드 인덱스를 quadMesh에 추가
        quadMesh(i, :) = closestNodeIndices(angleOrder)';
    end
end