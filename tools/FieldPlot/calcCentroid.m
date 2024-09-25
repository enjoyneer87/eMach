function centroid = calcCentroid(nodeCoords)
    % calculateCentroid - 요소 노드 좌표로부터 중심 좌표 계산
    %
    % nodeCoords: N x 3 배열로, N개의 노드 좌표 (X, Y, Z)가 포함
    % centroid: 요소 중심 좌표 (X, Y, Z)

    % 요소 노드의 평균을 계산하여 중심 좌표를 구함
    centroid = mean(nodeCoords, 1);
end