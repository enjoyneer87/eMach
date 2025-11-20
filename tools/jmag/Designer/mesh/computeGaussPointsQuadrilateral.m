function gaussPoints = computeGaussPointsQuadrilateral(elementNodes)
    % elementNodes: 4x2 행렬로, 사각형 요소의 각 꼭짓점 좌표 (x, y) 포함
    % gaussPoints: 4x2 행렬로, 각 가우스 포인트의 좌표
    
    % 참조 좌표계에서의 가우스 포인트 (2x2 Gauss quadrature)
    gaussRef = [-1, -1; 1, -1; 1, 1; -1, 1] * (1 / sqrt(3));
    
    % 변환 행렬 초기화
    gaussPoints = zeros(size(gaussRef));
    
    % 사각형 요소의 형상 함수 (Bilinear interpolation)를 사용하여 실제 좌표로 변환
    for i = 1:size(gaussRef, 1)
        xi = gaussRef(i, 1);
        eta = gaussRef(i, 2);
        
        % Bilinear shape functions
        N1 = (1 - xi) * (1 - eta) / 4;
        N2 = (1 + xi) * (1 - eta) / 4;
        N3 = (1 + xi) * (1 + eta) / 4;
        N4 = (1 - xi) * (1 + eta) / 4;
        
        % 실제 좌표로 변환
        gaussPoints(i, :) = N1 * elementNodes(1, :) + N2 * elementNodes(2, :) + ...
                            N3 * elementNodes(3, :) + N4 * elementNodes(4, :);
    end
end