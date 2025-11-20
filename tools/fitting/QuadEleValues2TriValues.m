function expandedElementValues = QuadEleValues2TriValues(TR, quadElementCenters, quadElementValues)
    % TR: triangulation 객체 (삼각형 요소 중심 포함)
    % quadElementCenters: 사각형 메쉬의 요소 중심 좌표
    % quadElementValues: 각 사각형 요소에서의 물리량 값
    
    % 삼각형의 중점 좌표 계산
    triangleCenters = incenter(TR);  % 삼각형의 중점 계산
    
    % 삼각형 요소 중심값을 사각형 요소 중심값에서 보간하여 확장된 값 계산
    expandedElementValues = zeros(size(TR.ConnectivityList, 1), 1);  % 삼각형 메쉬로 확장된 값 초기화
    
    % 각 삼각형 중심에 대해 가장 가까운 사각형 중심값을 찾아서 보간
    for i = 1:size(TR.ConnectivityList, 1)
        triCenter = triangleCenters(i, :);  % 현재 삼각형의 중심
        distances = sqrt(sum((quadElementCenters - triCenter).^2, 2));  % 유클리드 거리 계산
        [~, closestQuadIndex] = min(distances);  % 가장 가까운 사각형 요소 중심 찾기
        expandedElementValues(i) = quadElementValues(closestQuadIndex);  % 사각형 요소 값으로 확장
    end
end