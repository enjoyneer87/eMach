function nearestNodes = findAdaptiveNearestNodesOptimized(elementCenters,nodeCoords, EleTypeList)
    % nodeCoords: 노드 좌표 리스트 (nx2 배열, 각 행이 노드의 좌표 [x, y])
    % elementCenters: 요소 중심점 리스트 (mx2 배열, 각 행이 요소 중심의 좌표 [x, y])
    % elementTypes: 요소 타입 (mx1 배열, 각 요소가 삼각형인지 사각형인지 저장 ['triangle', 'quadrilateral'])
    % nearestNodes: 각 요소별로 가장 가까운 노드 인덱스를 반환하는 배열

    % eleType=slotEleTypeList
    % elementCenters=slotElementCoord
    % nodeCoords=   slotNodeCoord
    % 1. 삼각형과 사각형 요소 인덱스를 분리
    triangleIdx = EleTypeList==2;  % 삼각형 요소 인덱스
    quadrilateralIdx = EleTypeList==3;  % 사각형 요소 인덱스

% elementTypes=     AllelementCentersTable.eleType
    % 2. 각각에 대해 knnsearch 수행
    % 삼각형 요소에 대해 k=3, 사각형 요소에 대해 k=4
    % nearestTriangleNodes = knnsearch(nodeCoords, elementCenters(triangleIdx, :),'fast, 'K', 3);
    % nearestQuadrilateralNodes = knnsearch(nodeCoords, elementCenters(quadrilateralIdx, :),, 'K', 4);
    nearestQuadrilateralNodes = findNearestNodes(elementCenters, nodeCoords, 3);

   % elementCenters= elementCoord
    % 3. 원래 인덱스 순서로 결과를 결합
    nearestNodes = cell(size(elementCenters, 1), 1);  % 결과 저장할 셀 배열
    nearestNodes(triangleIdx)      = mat2cell(nearestTriangleNodes, ones(sum(triangleIdx), 1), 3);
    nearestNodes(quadrilateralIdx) = mat2cell(nearestQuadrilateralNodes, ones(sum(quadrilateralIdx), 1), 4);
end