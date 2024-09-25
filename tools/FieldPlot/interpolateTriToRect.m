function [Xq, Yq, Vq,gridWidth,gridHeight]=interpolateTriToRect(DT_with_values)
    % interpolateTriToRectPolar - 삼각형 메쉬에서 극좌표계를 사용하여 원주방향으로 평행한 직사각형 그리드로 보간
    %
    % 입력:
    %   DT_with_values: 물리량 값이 할당된 Delaunay 삼각화 구조체
    %
    % 출력:
    %   Vq: 직사각형 그리드에서 보간된 물리량 값
    
    % Delaunay 삼각화 객체와 요소 중심의 물리량 값 추출
    DT = DT_with_values.DT;
    elementCenters = DT_with_values.ElementCenters;
    elementValues = DT_with_values.ElementValues;
    
    % 요소 중심 좌표를 극좌표계로 변환 (r, θ)
    [theta, r] = cart2pol(elementCenters(:, 1), elementCenters(:, 2));
    
    % 극좌표계에서 범위 계산
    rMin = min(r);
    rMax = max(r);
    thetaMin = min(theta);
    thetaMax = max(theta);
    
    % 직사각형 그리드 자동 생성 (극좌표계 θ, r 범위에 맞게)
    numTheta = 50;  % θ 방향 그리드 해상도
    numR = 50;      % r 방향 그리드 해상도
    [Thetaq, Rq] = meshgrid(linspace(thetaMin, thetaMax, numTheta), linspace(rMin, rMax, numR));
    
    % 그리드를 직교 좌표계로 변환
    [Xq, Yq] = pol2cart(Thetaq, Rq);
    
    % 삼각형 요소 중심에 할당된 물리량 값을 보간 (극좌표계에서 보간)
    F = scatteredInterpolant(theta, r, elementValues, 'linear', 'none');
    
    
    % 각 그리드의 가로(θ 방향)와 세로(r 방향) 길이 계산
    dTheta = diff(Thetaq, 1, 2);  % θ 방향의 변화 (각도 차이)
    dR = diff(Rq, 1, 1);          % r 방향의 변화 (반지름 차이)
    
    % 가로 길이 (θ 방향, 원호의 길이 계산)
    gridWidth = Rq(:, 1:end-1) .* dTheta;  % θ 방향의 차이를 반지름에 맞춰 원호 길이로 계산
    
    % 세로 길이 (r 방향)
    gridHeight = dR;  % 반지름 차이
    
    % 그리드 면적 계산 (가로 길이 * 세로 길이)
    gridArea = uniquetol(gridWidth,1e-1) .* uniquetol(gridHeight,1e-1);
  
    % 직사각형 그리드로 보간
    Vq = F(Thetaq, Rq);
    
    % 결과 시각화 (옵션)
    % figure;
    surf(Xq, Yq, Vq);
    xlabel('X');
    ylabel('Y');
    zlabel('Interpolated Values');
    title('극좌표계에서 원주방향으로 평행한 직사각형 그리드로 보간');
end