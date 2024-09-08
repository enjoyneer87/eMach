function elementCentersTable = calcElementConnectivity(elementCentersTable, NodeTable, numNodesPerElement)
    % calculateElementConnectivity - 요소 중심과 노드 좌표 및 노드 ID로부터 요소의 connectivity 계산
    %
    % 입력:
    %   elementCentersTable - 요소 중심 좌표 (Mx2 또는 Mx3 행렬, M은 요소 수)
    %   nodeCoords - 노드의 좌표 (Nx2 또는 Nx3 행렬, N은 노드 수)
    %   nodeIDs - 노드의 ID (Nx1 벡터, N은 노드 수)
    %   numNodesPerElement - 각 요소가 연결할 노드 수 (삼각형 요소는 3, 사각형 요소는 4 등)
    %
    % 출력:
    %   elementConnectivity - 요소별로 연결된 노드 번호 (MxnumNodesPerElement 행렬)
    %
    % 예:
    %   elementConnectivity = calculateElementConnectivity(elementCenters, nodeCoords, nodeIDs, 3);

    if nargin < 3
        numNodesPerElement = 3;  % 기본값: 삼각형 요소
    end

    numElements = size(elementCentersTable, 1);  % 요소 수
    elementConnectivity = zeros(numElements, numNodesPerElement);  % 요소별로 연결된 노드를 저장할 배열
    
    nodeCoords=NodeTable.nodeCoords;
    NodeID    =NodeTable.NodeID;
    for i = 1:numElements
        % i번째 요소의 중심 좌표 가져오기
        elementCenter = elementCentersTable(i, :);
        elementCenter = m2mm([elementCenter.x, elementCenter.y]);  % 예시에서는 2D 좌표
        
        % 각 노드와 요소 중심 간의 거리 계산
        distances = sqrt(sum((nodeCoords - elementCenter).^2, 2));
        
        % 가장 가까운 numNodesPerElement개의 노드 인덱스를 찾음
        [~, sortedNodeIndices] = sort(distances);
        
        % 요소와 연결된 노드들의 ID를 elementConnectivity에 저장
        elementConnectivity(i, :) = NodeID(sortedNodeIndices(1:numNodesPerElement));
    end
    elementCentersTable.elementConnectivity=elementConnectivity;
end