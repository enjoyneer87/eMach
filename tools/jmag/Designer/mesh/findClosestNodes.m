function quadIndices = findClosestNodes(quadVertices, nodes)
    % 주어진 사각형 꼭짓점에 가장 가까운 노드 인덱스를 찾는 함수
    quadIndices = zeros(1, 3);
    for i = 1:3
        % 각 사각형 꼭짓점에서 가장 가까운 노드 찾기
        [~, idx] = min(vecnorm(nodes - quadVertices(i, :), 2, 2));
        quadIndices(i) = idx;
    end
end