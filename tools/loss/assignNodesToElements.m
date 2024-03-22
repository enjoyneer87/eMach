function combinedCellArray = assignNodesToElements(nodePositions, elementPositions, nodeIndex, elementIndex)
    % 각 요소별로 노드 인덱스를 저장할 배열 초기화
    numElements = length(elementIndex);
    combinedCellArray = cell(numElements, 2);

    % 각 요소 위치에 대해 가장 가까운 네 개의 노드 찾기
    for i = 1:numElements
        % 현재 요소 위치와 모든 노드 위치 사이의 거리 계산
        distances = sqrt(sum((nodePositions - elementPositions(i, :)).^2, 2));
        
        % 거리가 가장 짧은 네 개의 노드의 인덱스 찾기
        [~, nearestNodeIndices] = sort(distances, 'ascend');
        
        % 세 노드의 x,y 위치 평균 계산
        meanPosition = mean(nodePositions(nearestNodeIndices(1:3), :), 1);
        
        % 평균 위치와 elementPositions의 값이 충분히 일치하는지 검증
        if norm(meanPosition - elementPositions(i, :)) > 1e-2 % 임계값은 상황에 따라 조정
            % 일치하지 않으면 네 번째 노드까지 포함
            selectedNodeIndices = nearestNodeIndices(1:4);
        else
            % 일치하면 세 개의 노드만 포함
            selectedNodeIndices = nearestNodeIndices(1:3);
        end
        
        % elementIndex와 선택된 노드 인덱스 할당
        combinedCellArray{i, 1} = elementIndex(i); % elementIndex 할당
        combinedCellArray{i, 2} = nodeIndex(selectedNodeIndices); % 선택된 노드 인덱스 할당
    end
end
