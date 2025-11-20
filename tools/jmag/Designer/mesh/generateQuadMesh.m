function quadMesh = generateQuadMesh(nodes, elementCenters, boundaryEdges)
    % nodes: 전체 노드 좌표 리스트 (nx2 배열)
    % elementCenters: 요소 중심 좌표 리스트 (mx2 배열)
    % boundaryEdges: 외각선을 이루는 변의 노드 인덱스 리스트 (px2 배열)
    %
    % quadMesh: 4개의 노드로 이루어진 사각형 요소 리스트 (mx4)

    numCenters = size(elementCenters, 1);
    quadMesh = zeros(numCenters, 4);  % 사각형 요소를 저장할 배열

    % 1. 외각선 기준 첫 번째 사각형 찾기 (boundaryEdges를 사용)
    for i = 1:size(boundaryEdges, 1)
        edgeNodes = nodes(boundaryEdges(i, :), :);  % 현재 외각선의 변 노드
        edgeCenter = mean(edgeNodes, 1);            % 해당 변의 중심점

        % 해당 변과 가장 가까운 요소 중심 찾기
        distancesToCenters = vecnorm(elementCenters - edgeCenter, 2, 2);
        [~, closestCenterIdx] = min(distancesToCenters);

        % 2. 가장 가까운 요소 중심에 대해 사각형을 구성
        center = elementCenters(closestCenterIdx, :);
        distancesToNodes = vecnorm(nodes - center, 2, 2);

        % 가장 가까운 4개의 노드 찾기
        [~, closestNodeIndices] = mink(distancesToNodes, 4);

        % 3. 찾은 4개의 노드를 시계 방향으로 정렬
        selectedNodeCoords = nodes(closestNodeIndices, :);
        
        angles = atan2(selectedNodeCoords(:, 2) - center(2), selectedNodeCoords(:, 1) - center(1));
        [~, angleOrder] = sort(angles);  % 시계 방향으로 정렬

        % scatter(selectedNodeCoords(:,1),selectedNodeCoords(:,2))
        hold on
        % 4. 첫 번째 사각형 요소를 quadMesh에 추가
        quadMesh(closestCenterIdx, :) = closestNodeIndices(angleOrder)';
    
    
        % 5. 연결된 다음 사각형 찾기
        % 첫 번째 사각형의 변을 기준으로, 새로운 사각형을 찾아 연결
        nextEdgeNodes = closestNodeIndices(angleOrder(1:2));  % 첫 번째 사각형의 한 변
        quadMesh = findNextQuadMesh(quadMesh, nodes, elementCenters, nextEdgeNodes, closestCenterIdx);
    end
end

function quadMesh = findNextQuadMesh(quadMesh, nodes, elementCenters, edgeNodes, prevCenterIdx)
    % edgeNodes: 현재 사각형의 변 노드 리스트 (2x1 배열)
    % prevCenterIdx: 이전에 사용된 요소 중심 인덱스
    
    % edgeNodes를 기준으로 새로운 요소 중심을 찾음
    edgeCenter = mean(nodes(edgeNodes, :), 1);  % 변의 중심점
    distancesToCenters = vecnorm(elementCenters - edgeCenter, 2, 2);

    % 이전 중심과 동일한 중심 제외
    distancesToCenters(prevCenterIdx) = inf;

    % 가장 가까운 새로운 중심 찾기
    [~, nextCenterIdx] = min(distancesToCenters);
    
    % 새로운 중심을 기준으로 사각형 구성
    center = elementCenters(nextCenterIdx, :);
    distancesToNodes = vecnorm(nodes - center, 2, 2);

    % 가장 가까운 4개의 노드를 찾고 시계 방향으로 정렬
    [~, closestNodeIndices] = mink(distancesToNodes, 4);
    selectedNodeCoords = nodes(closestNodeIndices, :);
    angles = atan2(selectedNodeCoords(:, 2) - center(2), selectedNodeCoords(:, 1) - center(1));
    [~, angleOrder] = sort(angles);  % 시계 방향으로 정렬

    % 새로운 사각형을 quadMesh에 추가
    quadMesh(nextCenterIdx, :) = closestNodeIndices(angleOrder)';
end