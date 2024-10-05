function nearestNodes = findNearestNodes(nodeId, nodes, centerPoints, numNodes)
    % nodeId: 각 노드의 고유 ID (nx1 배열)
    % nodes: 노드 좌표 리스트 (nx2 배열, 각 행이 [x, y] 좌표)
    % centerPoints: 요소의 중심점 좌표 리스트 (mx2 배열, 각 행이 요소 중심의 좌표 [x, y])
    % numNodes: 찾을 노드의 개수 (예: 4)
    %
    % nearestNodes: nodeId에 맞춰 반환되는 가장 가까운 노드 인덱스 (mxnumNodes)

    % 중심점의 개수
    numCenters = size(centerPoints, 1);

    % 노드 좌표에 대해 각 중심점에서 거리를 계산 (m x n 행렬)
    distances = sqrt(sum((permute(centerPoints, [1, 3, 2]) - permute(nodes, [3, 1, 2])).^2, 3));

    % 가장 가까운 노드를 찾기 위해 거리를 기준으로 정렬
    [~, sortedIndices] = sort(distances, 2);

    % 가장 가까운 numNodes개의 노드를 선택
    nearestNodes = sortedIndices(:, 1:numNodes);

    % 각 요소에 대해 선택된 노드를 시계 방향으로 정렬
    for i = 1:numCenters
        selectedNodeCoords = nodes(nearestNodes(i, :), :);  % 선택된 numNodes개의 노드 좌표
        center = centerPoints(i, :);  % 중심점

        % 각도를 기준으로 노드들을 시계 방향으로 정렬
        angles = atan2(selectedNodeCoords(:, 2) - center(2), selectedNodeCoords(:, 1) - center(1));
        [~, angleOrder] = sort(angles);  % 각도에 따라 정렬

        % 정렬된 순서로 nearestNodes 업데이트
        nearestNodes(i, :) = nearestNodes(i, angleOrder);
    end

    % 연속되는 노드가 유지되도록 순서 조정
    for i = 2:numCenters  % 첫 번째 행은 그대로 두고, 두 번째 행부터 조정
        % 이전 행의 마지막 노드 ID
        previousLastNode = nearestNodes(i - 1, end);

        % 현재 행에서 이전 행의 마지막 노드와 일치하는 노드의 인덱스 찾기
        currentRow = nearestNodes(i, :);
        idx = find(currentRow == previousLastNode, 1);

        % 이전 행의 마지막 노드가 현재 행의 첫 번째 노드가 되도록 순서 변경
        if ~isempty(idx)
            % idx에 해당하는 노드를 첫 번째로 가져오고, 그 뒤의 노드를 시계 방향으로 순서 유지
            nearestNodes(i, :) = [currentRow(idx:end), currentRow(1:idx-1)];
        end
    end

    % nodeId를 기준으로 nearestNodes의 인덱스를 반환
    nearestNodes = arrayfun(@(i, j) nodeId(nearestNodes(i, j)), repmat((1:size(nearestNodes, 1))', 1, numNodes), repmat(1:numNodes, size(nearestNodes, 1), 1));
end