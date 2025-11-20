function gaussPoints = computeGaussPointsTriangular(elementNodes)
    % elementNodes: 3x2 행렬로, 삼각형 요소의 각 꼭짓점 좌표 (x, y) 포함
    % gaussPoints: 1x2 행렬로, 가우스 포인트 좌표 (요소 중심)

    % 가우스 포인트: 삼각형의 중심점 (1차 적분)
    % 삼각형 요소의 중심점 계산
    gaussPoints = mean(elementNodes, 1);
end