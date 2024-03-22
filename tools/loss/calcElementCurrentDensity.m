function J_e = calcElementCurrentDensity(A_dot, elements, nodes, sigma)
    % A_dot: 노드별 벡터 포텐셜의 시간 미분 값 (노드 수 x 1 벡터)
    % elements: 요소와 연결된 노드의 인덱스 (요소 수 x 노드 수/요소)
    % nodes: 노드의 위치 좌표 (노드 수 x 2, 각 행은 [x, y] 좌표)
    % sigma: 도체의 전도도
    
    % 요소별 전류밀도를 저장할 배열 초기화
    numElements = size(elements, 1);
    J_e = zeros(numElements, 1);
    
    % 각 요소에 대해 반복
    for i = 1:numElements
        % 현재 요소의 노드 인덱스
        elementNodes = elements(i, :);
        
        % 현재 요소의 노드 위치 좌표
        elementNodePositions = nodes(elementNodes, :);
        
        % 형상 함수 계산 (여기서는 단순화를 위해 평균값 사용)
        % 실제 FEM 계산에서는 요소의 형태와 요소 내 위치에 따라 형상 함수가 달라집니다.
        N = ones(size(elementNodes)) / length(elementNodes);
        
        % 현재 요소의 벡터 포텐셜 시간 미분의 평균 계산
        A_dot_avg = sum(N .* A_dot(elementNodes));
        
        % 요소별 전류밀도 계산
        J_e(i) = sigma * A_dot_avg;
    end
end
