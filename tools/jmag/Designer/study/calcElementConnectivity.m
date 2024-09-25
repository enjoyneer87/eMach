function elementCentersTable = calcElementConnectivity(elementCentersTable, NodeTable)
    % 요소 중심 좌표와 노드 좌표 및 노드 ID로부터 요소의 연결 정보를 계산
    %
    % 입력:
    %   elementCentersTable - 요소 중심 좌표와 eleType을 포함한 테이블
    %   NodeTable - 노드의 좌표 및 ID를 포함한 테이블
    %
    % 출력:
    %   elementCentersTable - 연결된 노드 정보가 포함된 테이블

    numElements = size(elementCentersTable, 1);  % 요소 수
    nodeCoords = NodeTable.nodeCoords;
    NodeID = NodeTable.NodeID;
    
    elementCentersTable.elementConnectivity = cell(numElements, 1);  % 연결 정보를 저장할 셀 배열
    
    for i = 1:numElements
        % i번째 요소의 중심 좌표 가져오기
        elementCenter = elementCentersTable(i, :);
        elementCenter = m2mm([elementCenter.x, elementCenter.y]);  % 예시에서는 2D 좌표
        
        % 요소 타입에 따라 연결할 노드 수 결정 (2: 삼각형, 3: 사각형)
        if elementCentersTable.eleType(i) == 2
            numNodesPerElement = 3;  % 삼각형 요소
        elseif elementCentersTable.eleType(i) == 3
            numNodesPerElement = 4;  % 사각형 요소
        else
            error('알 수 없는 요소 타입입니다.');
        end
        
        % 각 노드와 요소 중심 간의 거리 계산
        distances = sqrt(sum((nodeCoords - elementCenter).^2, 2));
        
        % 가장 가까운 numNodesPerElement개의 노드 인덱스를 찾음
        [~, sortedNodeIndices] = sort(distances);
        
        % 요소와 연결된 노드들의 ID를 저장
        elementCentersTable.elementConnectivity{i} = NodeID(sortedNodeIndices(1:numNodesPerElement));
    end
end