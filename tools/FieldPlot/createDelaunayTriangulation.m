function DT=createDelaunayTriangulation(elementConnetivity,nodeCoors)

    nodesPos = nodeCoors;  % 노드 좌표 가져오기
    elements = elementConnetivity;  % 요소 연결성 가져오기

    % 1. 노드 번호가 1부터 시작하지 않는 경우 처리
    uniqueNodeIDs = unique(cell2mat(elements));  % 사용된 모든 노드 번호 추출
    numNodes = length(uniqueNodeIDs);  % 고유 노드 수
    newIndexMap = zeros(numNodes, 1);  % 노드 번호 -> 새로운 인덱스로 매핑

    % 2. 노드 번호를 1번부터 시작하도록 매핑
    newIndexMap(uniqueNodeIDs) = 1:numNodes;

    % 3. 요소의 노드 번호를 새로운 인덱스로 업데이트
    updatedElements = cellfun(@(x) newIndexMap(x), elements, 'UniformOutput', false);

    % 4. uniqueNodeIDs를 사용하여 nodesPos에서 해당 노드 좌표를 추출
    updatedNodes = nodesPos;

    % 5. 삼각형 요소를 생성하여 플롯
    DT = triangulation([updatedElements{:}]', updatedNodes);
    triplot(DT);
    hold on;

end